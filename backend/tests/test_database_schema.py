"""Startup must fail before ingestion; migrations publish a verified copy only."""
import sqlite3

import pytest

from backend.app import create_app
from backend.config import Config
from backend.models import db


def config_for(path):
    class ConfigForDatabase(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(path)
        ML_SERVICE_URL = ''
    return ConfigForDatabase


def test_legacy_startup_fails_before_ingestion(tmp_path, monkeypatch):
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE readings_classification (id TEXT PRIMARY KEY, wheeze_crackle_class TEXT)')
    import backend.app as module
    monkeypatch.setattr(module, 'register_websocket_routes', lambda app: pytest.fail('ingestion started'))
    monkeypatch.setattr(module, 'start_mqtt_subscriber', lambda app: pytest.fail('MQTT started'))
    with pytest.raises(RuntimeError, match='schema.*migrate_database'):
        create_app(config_for(path))
    with sqlite3.connect(path) as conn:
        assert len(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()) == 1


def test_empty_database_bootstraps(tmp_path):
    app = create_app(config_for(tmp_path / 'new.db'), start_mqtt=False)
    with app.app_context():
        assert 'hr_confidence' in db.metadata.tables['readings_vital'].columns


def test_quality_upgrade_preserves_unknown_and_source(tmp_path):
    from backend.scripts.migrate_database import migrate
    source, target = tmp_path / 'source.db', tmp_path / 'target.db'
    create_app(config_for(source), start_mqtt=False)
    with sqlite3.connect(source) as conn:
        for field in ('hr_confidence', 'spo2_confidence', 'rr_confidence'):
            conn.execute(f'ALTER TABLE readings_vital DROP COLUMN {field}')
        conn.execute("INSERT INTO devices (device_id,status) VALUES ('dev','offline')")
        conn.execute("INSERT INTO readings_vital (id,device_id,timestamp,hr) VALUES ('v1','dev','2026-01-01 00:00:00',25)")
    with pytest.raises(RuntimeError, match='schema'):
        create_app(config_for(source), start_mqtt=False)
    migrate(source, target)
    create_app(config_for(target), start_mqtt=False)
    with sqlite3.connect(target) as conn:
        assert conn.execute('SELECT hr,hr_confidence FROM readings_vital').fetchone() == (25, None)
        assert conn.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert conn.execute('SELECT version FROM pneumacare_schema_version').fetchone() == (1,)
    with sqlite3.connect(source) as conn:
        assert 'hr_confidence' not in {r[1] for r in conn.execute('PRAGMA table_info(readings_vital)')}
    with pytest.raises(ValueError, match='exist'):
        migrate(source, target)


def test_four_class_archived_without_relabeling(tmp_path):
    from backend.scripts.migrate_database import migrate
    source, target = tmp_path / 'source.db', tmp_path / 'target.db'
    with sqlite3.connect(source) as conn:
        conn.execute('CREATE TABLE readings_classification (id TEXT PRIMARY KEY,wheeze_crackle_class TEXT)')
        conn.execute("INSERT INTO readings_classification VALUES ('c1','wheeze')")
    migrate(source, target)
    with sqlite3.connect(target) as conn:
        assert conn.execute('SELECT * FROM readings_classification_legacy_four_class').fetchone() == ('c1','wheeze')
        assert conn.execute('SELECT count(*) FROM readings_classification').fetchone() == (0,)
    # A current schema can also be snapshotted repeatedly to distinct new targets.
    migrate(target, tmp_path / 'second.db')


def test_failed_migration_leaves_no_target(tmp_path, monkeypatch):
    from backend.scripts import migrate_database
    source, target = tmp_path / 'source.db', tmp_path / 'target.db'
    with sqlite3.connect(source) as conn:
        conn.execute('CREATE TABLE readings_vital (unexpected TEXT)')
    with pytest.raises(RuntimeError, match='schema'):
        migrate_database.migrate(source, target)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == [source]


def test_factory_import_has_no_startup_side_effects():
    import os
    import subprocess
    import sys
    environment = dict(os.environ, DATABASE_URL='sqlite:////does-not-exist/pneumacare.db')
    result = subprocess.run([sys.executable, '-c',
        'from backend.app import create_app; import backend.app as module; '
        'assert module._wsgi_app is None'], env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_unknown_schema_version_is_not_downgraded(tmp_path):
    from backend.scripts.migrate_database import migrate
    source, target = tmp_path / 'future.db', tmp_path / 'target.db'
    with sqlite3.connect(source) as connection:
        connection.execute('CREATE TABLE pneumacare_schema_version (version INTEGER NOT NULL)')
        connection.execute('INSERT INTO pneumacare_schema_version VALUES (99)')
    with pytest.raises(RuntimeError, match='schema'):
        migrate(source, target)
    assert not target.exists()


def test_snapshot_includes_committed_wal_rows(tmp_path):
    from backend.scripts.migrate_database import migrate
    source, target = tmp_path / 'wal.db', tmp_path / 'snapshot.db'
    connection = sqlite3.connect(source)
    try:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('CREATE TABLE retained_evidence (value TEXT)')
        connection.execute("INSERT INTO retained_evidence VALUES ('committed')")
        connection.commit()
        migrate(source, target)
        with sqlite3.connect(target) as copied:
            assert copied.execute('SELECT value FROM retained_evidence').fetchone() == ('committed',)
    finally:
        connection.close()

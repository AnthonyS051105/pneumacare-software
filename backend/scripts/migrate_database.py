"""Upgrade a consistent SQLite snapshot; never overwrite or modify the source.

Four-class classifications/trends/alerts stay in archive tables. They cannot be
converted into AST two-class predictions. Old vital quality remains NULL/unknown.
A failed migration publishes nothing; rerun with the same new target to retry.
"""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
import tempfile

from flask import Flask

from backend.database_schema import QUALITY_COLUMNS, SCHEMA_VERSION, assert_compatible_schema
from backend.models import db


@contextmanager
def _connect(*args, **kwargs):
    connection = sqlite3.connect(*args, **kwargs)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _check_integrity(connection):
    if connection.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
        raise RuntimeError('SQLite integrity check failed; migration not published')


def migrate(source: Path, target: Path):
    source, target = source.resolve(), target.resolve()
    if source == target or target.exists():
        raise ValueError('target must not exist; source is never overwritten')
    if not source.is_file():
        raise ValueError('source database does not exist')
    # Same directory ensures atomic publication. mkstemp also excludes races.
    descriptor, temporary = tempfile.mkstemp(prefix='.pneumacare-migrate-', suffix='.db', dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        # SQLite backup captures a consistent snapshot even with a WAL source.
        with _connect(source.as_uri() + '?mode=ro', uri=True) as old:
            with _connect(temporary) as copied:
                old.backup(copied)
                _check_integrity(copied)
        with _connect(temporary) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            columns = {row[1] for row in connection.execute('PRAGMA table_info(readings_classification)')}
            if 'wheeze_crackle_class' in columns:
                for table in ('readings_classification', 'trend_events', 'alerts'):
                    if table in tables:
                        if table + '_legacy_four_class' in tables:
                            raise RuntimeError('schema archive already exists; resolve ambiguity before migration')
                        connection.execute(f'ALTER TABLE {table} RENAME TO {table}_legacy_four_class')
            vital_columns = {row[1] for row in connection.execute('PRAGMA table_info(readings_vital)')}
            if vital_columns:
                for column in QUALITY_COLUMNS:
                    if column not in vital_columns:
                        connection.execute(f'ALTER TABLE readings_vital ADD COLUMN {column} VARCHAR(16)')
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(temporary)
        db.init_app(app)
        with app.app_context():
            try:
                assert_compatible_schema()
                db.create_all()
                assert_compatible_schema()
            finally:
                db.session.remove()
                db.engine.dispose()
        with _connect(temporary) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS pneumacare_schema_version (version INTEGER NOT NULL)')
            connection.execute('DELETE FROM pneumacare_schema_version')
            connection.execute('INSERT INTO pneumacare_schema_version VALUES (?)', (SCHEMA_VERSION,))
            _check_integrity(connection)
            violations = connection.execute('PRAGMA foreign_key_check').fetchall()
            if violations:
                raise RuntimeError('foreign key check failed; migration not published')
        with temporary.open('rb') as snapshot:
            os.fsync(snapshot.fileno())
        # Unlike replace(), link fails if another process creates target first.
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    args = parser.parse_args()
    migrate(args.source, args.target)
    print('Migration verified and published; original database unchanged. Select the new database explicitly.')


if __name__ == '__main__':
    main()

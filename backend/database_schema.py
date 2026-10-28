"""Non-mutating compatibility check before ingestion/background workers start."""
from sqlalchemy import inspect

from backend.models import db

SCHEMA_VERSION = 1
QUALITY_COLUMNS = ('hr_confidence', 'spo2_confidence', 'rr_confidence')


def assert_compatible_schema():
    inspector = inspect(db.engine)
    existing = set(inspector.get_table_names())
    problems = []
    for table in db.metadata.sorted_tables:
        if table.name not in existing:
            continue  # create_all may safely create genuinely missing tables.
        actual = {column['name'] for column in inspector.get_columns(table.name)}
        missing = set(table.columns.keys()) - actual
        if missing:
            problems.append(f"{table.name}: missing {','.join(sorted(missing))}")
    if 'pneumacare_schema_version' in existing:
        from sqlalchemy import text
        with db.engine.connect() as connection:
            versions = connection.execute(text('SELECT version FROM pneumacare_schema_version')).scalars().all()
        if versions != [SCHEMA_VERSION]:
            problems.append('unsupported schema version')
    if problems:
        raise RuntimeError(
            'Incompatible database schema (' + '; '.join(problems) + '). '
            'Stop ingestion and run python -m backend.scripts.migrate_database '
            '--source OLD.db --target NEW.db; review the copy, then select NEW.db. '
            'The source database has not been changed.'
        )

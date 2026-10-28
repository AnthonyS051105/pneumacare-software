"""Copy DB read-only; archive four-class results only on the isolated copy.

Accounts, pairing, vitals and thresholds remain. Old classifications/trends/alerts
are retained in *_legacy_four_class tables, never relabeled as AST predictions.
"""
import argparse
from pathlib import Path
import sqlite3


def prepare(source: Path, target: Path):
    source, target = source.resolve(), target.resolve()
    if target.exists() or source == target:
        raise ValueError('target must be new; source is never overwritten')
    with sqlite3.connect(f'file:{source}?mode=ro', uri=True) as old:
        with sqlite3.connect(target) as new:
            old.backup(new)
    with sqlite3.connect(target) as conn:
        columns = {r[1] for r in conn.execute('pragma table_info(readings_classification)')}
        if 'wheeze_crackle_class' in columns:
            for table in ('readings_classification', 'trend_events', 'alerts'):
                conn.execute(f'ALTER TABLE {table} RENAME TO {table}_legacy_four_class')
    from flask import Flask
    from backend.models import db
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(target)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    print('Prepared isolated two-class database; original database unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.source, args.target)

"""Backward compatible alias for the verified copy-only database migrator."""
from backend.scripts.migrate_database import main, migrate

prepare = migrate

if __name__ == '__main__':
    main()

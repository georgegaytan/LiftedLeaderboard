from src.database.db_manager import DBManager
import argparse


def up(db_manager: DBManager):
    # Optimizes inserts - safe for small, non-critical apps
    db_manager.execute('SET synchronous_commit = off')

    # Drop unused indexes
    db_manager.execute('DROP INDEX IF EXISTS idx_activity_records_updated_at')
    db_manager.execute('DROP INDEX IF EXISTS idx_activity_records_created_at')
    db_manager.execute('DROP INDEX IF EXISTS idx_activity_records_activity_id')

    # Update Award XP TRIGGER to not call redundant updated_at = NOW()
    db_manager.execute(
        '''
        CREATE OR REPLACE FUNCTION award_activity_xp_fn()
        RETURNS TRIGGER AS $$
        DECLARE
            v_xp INTEGER;
        BEGIN
            SELECT xp_value INTO v_xp FROM activities WHERE id = NEW.activity_id;
            IF v_xp IS NULL THEN
                v_xp := 0;
            END IF;

            -- Removed redundant updated_at = NOW() assignment
            UPDATE users
            SET total_xp = total_xp + v_xp
            WHERE id = NEW.user_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        '''
    )


def down(db_manager: DBManager):
    # Re-enable synchronous commits
    db_manager.execute('SET synchronous_commit = on')

    # Recreate previously dropped indexes
    db_manager.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_activity_records_updated_at
        ON activity_records(updated_at)
        '''
    )
    db_manager.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_activity_records_created_at
        ON activity_records(created_at)
        '''
    )
    db_manager.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_activity_records_activity_id
        ON activity_records(activity_id)
        '''
    )

    # Restore the original Award XP trigger function (with updated_at assignment)
    db_manager.execute(
        '''
        CREATE OR REPLACE FUNCTION award_activity_xp_fn()
        RETURNS TRIGGER AS $$
        DECLARE
            v_xp INTEGER;
        BEGIN
            SELECT xp_value INTO v_xp FROM activities WHERE id = NEW.activity_id;
            IF v_xp IS NULL THEN
                v_xp := 0;
            END IF;

            UPDATE users
            SET total_xp = total_xp + v_xp,
                updated_at = NOW()
            WHERE id = NEW.user_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        '''
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['up', 'down'])
    args = parser.parse_args()

    if args.command == 'up':
        with DBManager() as _db:
            up(_db)
    elif args.command == 'down':
        with DBManager() as _db:
            down(_db)


if __name__ == '__main__':
    main()

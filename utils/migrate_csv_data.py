import sys
from pathlib import Path

# Add project root to sys.path to allow importing from 'campaign_crafter_api'
# This assumes the script is in 'utils/' and project root is its parent.
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from campaign_crafter_api.app.core.seeding import seed_all_csv_data
from campaign_crafter_api.app.db import SessionLocal, engine, Base
# Removed sqlalchemy.orm.Session, csv, crud, models as they are no longer directly used here.

if __name__ == "__main__":
    print("Starting data migration script (wrapper for app.core.seeding)...")
    
    # Ensure tables are created before attempting to seed data
    print("Initializing database and creating tables if they don't exist...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables checked/created successfully.")
    except Exception as e:
        print(f"FATAL: Error during database table initialization: {e}")
        sys.exit(1) # Exit if tables can't be created

    db_session = None # Ensure db_session is defined for finally block
    try:
        db_session = SessionLocal()
        print("Database session started for seeding.")
        # Call the main seeding function from its new location
        seed_all_csv_data(db_session) 
        print("\nData migration script process completed successfully.")
    except Exception as e:
        # This will catch errors from seed_all_csv_data or SessionLocal() call
        print(f"An critical error occurred during the data migration process: {e}")
    finally:
        if db_session:
            db_session.close()
            print("Database session closed.")
    
    print("Migration script finished.")

import sys
import csv
from pathlib import Path
# import re # No longer needed

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from campaign_crafter_api.app.db import engine, SessionLocal, Base
from campaign_crafter_api.app import crud, models

# Define paths to CSV files - these remain global for the seeding functions
FEATURES_CSV_PATH = project_root / "csv" / "features.csv"
ROLLTABLES_CSV_PATH = project_root / "csv" / "tables1e.csv"

def seed_features(db: Session):
    print("\n--- Seeding Features ---")
    try:
        if not FEATURES_CSV_PATH.is_file():
            print(f"ERROR: Features CSV file not found at {FEATURES_CSV_PATH}")
            return

        with open(FEATURES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None) # Skip header row
            if not header or len(header) < 2:
                print("ERROR: Invalid CSV header for features. Expected at least 'Feature Name' and 'Template'.")
                return

            # print(f"Feature CSV Header: {header}") # Optional: for debugging
            
            processed_count = 0
            created_count = 0
            skipped_malformed = 0
            for row_num, row in enumerate(reader, 1): # Start row_num from 1 for data rows
                processed_count += 1
                if len(row) < 2:
                    print(f"Skipping malformed row {row_num} in features.csv: Insufficient columns. Content: {row}")
                    skipped_malformed +=1
                    continue
                
                feature_name, feature_template = row[0].strip(), row[1].strip()

                if not feature_name or not feature_template:
                    print(f"Skipping row {row_num} in features.csv: Empty name or template. Content: {row}")
                    skipped_malformed +=1
                    continue

                existing_feature = crud.get_feature_by_name(db, name=feature_name)
                if existing_feature:
                    print(f"Feature '{feature_name}' already exists. Skipping.")
                else:
                    feature_data = models.FeatureCreate(name=feature_name, template=feature_template)
                    crud.create_feature(db, feature=feature_data)
                    created_count += 1
                    print(f"Created feature: '{feature_name}'")
        print(f"--- Feature Seeding Finished ---")
        print(f"Processed {processed_count} data rows. Created {created_count} new features. Skipped {skipped_malformed} malformed rows.")

    except Exception as e:
        print(f"An error occurred during feature seeding: {e}")
        # Re-raise the exception if this function is called by another that handles overall try/except
        # For standalone, this print is okay. If part of a larger transaction, might need to re-raise.

def parse_roll_range(roll_str: str) -> tuple[int, int]:
    """Parses a roll string like '01-05' or '90' into (min_roll, max_roll)."""
    roll_str = roll_str.strip()
    if '-' in roll_str:
        min_val, max_val = map(int, roll_str.split('-'))
        return min_val, max_val
    else:
        val = int(roll_str)
        return val, val

def seed_roll_tables(db: Session):
    print("\n--- Seeding Rolltables ---")
    try:
        if not ROLLTABLES_CSV_PATH.is_file():
            print(f"ERROR: Rolltables CSV file not found at {ROLLTABLES_CSV_PATH}")
            return

        current_table_name: str | None = None
        current_table_description: str | None = None
        current_items: list[models.RollTableItemCreate] = []
        
        tables_processed_from_file = 0 # Number of table definitions encountered
        tables_actually_created = 0    # Number of new tables added to DB
        items_in_current_table_count = 0

        with open(ROLLTABLES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t') 
            
            for row_num, row in enumerate(reader, 1):
                if not row or not row[0].strip(): 
                    continue

                first_col = row[0].strip()

                if first_col.startswith('d') and len(row) > 1 and row[1].strip():
                    # New table header. Process the previous table if it exists.
                    if current_table_name and current_items:
                        tables_processed_from_file += 1
                        print(f"Checking database for existing rolltable: '{current_table_name}'...")
                        existing_table = crud.get_roll_table_by_name(db, name=current_table_name)
                        if existing_table:
                            print(f"Rolltable '{current_table_name}' already exists with {len(existing_table.items)} items. Skipping.")
                        else:
                            print(f"Creating rolltable: '{current_table_name}' with {len(current_items)} items.")
                            roll_table_data = models.RollTableCreate(
                                name=current_table_name,
                                description=current_table_description,
                                items=current_items
                            )
                            crud.create_roll_table(db, roll_table=roll_table_data)
                            tables_actually_created += 1
                    
                    # Reset for the new table
                    current_items = []
                    items_in_current_table_count = 0
                    current_table_description = first_col 
                    current_table_name = row[1].strip()
                    print(f"\nEncountered new table definition in CSV: '{current_table_name}' ({current_table_description})")

                elif current_table_name and len(row) > 1: 
                    roll_range_str = row[0].strip()
                    item_description = row[1].strip()

                    if not roll_range_str or not item_description:
                        print(f"Skipping malformed item row {row_num} for table '{current_table_name}': {row}")
                        continue
                    
                    try:
                        min_roll, max_roll = parse_roll_range(roll_range_str)
                        item_data = models.RollTableItemCreate(
                            min_roll=min_roll,
                            max_roll=max_roll,
                            description=item_description
                        )
                        current_items.append(item_data)
                        items_in_current_table_count += 1
                    except ValueError:
                        print(f"Invalid roll range '{roll_range_str}' in item row {row_num} for table '{current_table_name}'. Skipping item.")
                    except Exception as e:
                        print(f"Error processing item row {row_num} for table '{current_table_name}': {e}. Skipping item.")
                # else: # Optional: log lines that are neither headers nor items for a current table
                #     if first_col: 
                #         print(f"Skipping unclassified row {row_num} in rolltables.csv: {row}")

            # Process the last table in the file
            if current_table_name and current_items:
                tables_processed_from_file += 1
                print(f"Checking database for existing rolltable (last table in file): '{current_table_name}'...")
                existing_table = crud.get_roll_table_by_name(db, name=current_table_name)
                if existing_table:
                    print(f"Rolltable '{current_table_name}' already exists with {len(existing_table.items)} items. Skipping.")
                else:
                    print(f"Creating rolltable (last table in file): '{current_table_name}' with {len(current_items)} items.")
                    roll_table_data = models.RollTableCreate(
                        name=current_table_name,
                        description=current_table_description,
                        items=current_items
                    )
                    crud.create_roll_table(db, roll_table=roll_table_data)
                    tables_actually_created += 1
        
        print(f"--- Rolltable Seeding Finished ---")
        print(f"Encountered {tables_processed_from_file} table definitions in CSV. Created {tables_actually_created} new rolltables in the database.")

    except Exception as e:
        print(f"An error occurred during rolltable seeding: {e}")
        # Consider re-raising if part of a larger transaction

def seed_all_csv_data(db: Session):
    """Seeds all data from CSV files into the database."""
    print("\n--- Starting All CSV Data Seeding ---")
    seed_features(db)
    seed_roll_tables(db)
    print("\n--- All CSV Data Seeding Finished ---")


if __name__ == "__main__":
    print("Starting data migration script...")
    
    # Ensure tables are created before attempting to seed data
    print("Initializing database and creating tables if they don't exist...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables checked/created successfully.")
    except Exception as e:
        print(f"FATAL: Error during database table initialization: {e}")
        sys.exit(1) # Exit if tables can't be created

    db: Session | None = None # Ensure db is defined in the outer scope for finally block
    try:
        db = SessionLocal()
        seed_all_csv_data(db)
        print("\nData migration script process completed successfully.")
    except Exception as e:
        # This will catch errors from seed_all_csv_data or SessionLocal() call
        print(f"An critical error occurred during the data migration process: {e}")
    finally:
        if db:
            db.close()
            print("Database session closed.")
    
    print("Migration script finished.")

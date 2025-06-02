import sys
import csv
from pathlib import Path
import re # For parsing roll ranges

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from campaign_crafter_api.app.db import engine, SessionLocal, Base
from campaign_crafter_api.app import crud, models

# Define paths to CSV files
FEATURES_CSV_PATH = project_root / "csv" / "features.csv"
ROLLTABLES_CSV_PATH = project_root / "csv" / "tables1e.csv"

def migrate_features():
    print("\n--- Starting Feature Migration ---")
    Base.metadata.create_all(bind=engine) # Ensure tables are created
    
    db: Session = SessionLocal()
    try:
        if not FEATURES_CSV_PATH.is_file():
            print(f"ERROR: Features CSV file not found at {FEATURES_CSV_PATH}")
            return

        with open(FEATURES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None) # Skip header row
            if not header or len(header) < 2:
                print("ERROR: Invalid CSV header for features.")
                return

            print(f"Found header: {header}")
            
            count = 0
            created_count = 0
            for row in reader:
                count += 1
                if len(row) < 2:
                    print(f"Skipping malformed row {count}: {row}")
                    continue
                
                feature_name, feature_template = row[0].strip(), row[1].strip()

                if not feature_name or not feature_template:
                    print(f"Skipping row {count} with empty name or template: {row}")
                    continue

                existing_feature = crud.get_feature_by_name(db, name=feature_name)
                if existing_feature:
                    print(f"Feature '{feature_name}' already exists. Skipping.")
                else:
                    feature_data = models.FeatureCreate(name=feature_name, template=feature_template)
                    crud.create_feature(db, feature=feature_data)
                    created_count += 1
                    print(f"Created feature: '{feature_name}'")
        print(f"--- Feature Migration Finished ---")
        print(f"Processed {count} rows. Created {created_count} new features.")

    except Exception as e:
        print(f"An error occurred during feature migration: {e}")
    finally:
        db.close()

def parse_roll_range(roll_str: str):
    """Parses a roll string like '01-05' or '90' into (min_roll, max_roll)."""
    roll_str = roll_str.strip()
    if '-' in roll_str:
        min_val, max_val = map(int, roll_str.split('-'))
        return min_val, max_val
    else:
        val = int(roll_str)
        return val, val

def migrate_roll_tables():
    print("\n--- Starting Rolltable Migration ---")
    Base.metadata.create_all(bind=engine) # Ensure tables are created

    db: Session = SessionLocal()
    try:
        if not ROLLTABLES_CSV_PATH.is_file():
            print(f"ERROR: Rolltables CSV file not found at {ROLLTABLES_CSV_PATH}")
            return

        current_table_name = None
        current_table_description = None
        current_items = []
        processed_tables_count = 0
        created_tables_count = 0

        with open(ROLLTABLES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t') # Tab-delimited
            
            for row_num, row in enumerate(reader, 1):
                if not row or not row[0].strip(): # Skip empty lines or lines with no first cell
                    continue

                first_col = row[0].strip()

                # Check for table header (e.g., "d100", "Table Name")
                if first_col.startswith('d') and len(row) > 1 and row[1].strip():
                    # This is a new table header. Process the previous table if it exists.
                    if current_table_name and current_items:
                        processed_tables_count +=1
                        existing_table = crud.get_roll_table_by_name(db, name=current_table_name)
                        if existing_table:
                            print(f"Rolltable '{current_table_name}' already exists. Skipping.")
                        else:
                            roll_table_data = models.RollTableCreate(
                                name=current_table_name,
                                description=current_table_description,
                                items=current_items
                            )
                            crud.create_roll_table(db, roll_table=roll_table_data)
                            created_tables_count += 1
                            print(f"Created rolltable: '{current_table_name}' with {len(current_items)} items.")
                        current_items = [] # Reset for the new table
                    
                    current_table_description = first_col # e.g., "d100"
                    current_table_name = row[1].strip()
                    print(f"\nProcessing new table: '{current_table_name}' ({current_table_description})")

                elif current_table_name and len(row) > 1: # This is an item for the current table
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
                    except ValueError:
                        print(f"Invalid roll range '{roll_range_str}' in row {row_num} for table '{current_table_name}'. Skipping item.")
                    except Exception as e:
                        print(f"Error processing item row {row_num} for table '{current_table_name}': {e}. Skipping item.")
                else:
                    # Line is not a header and not an item for a current table (e.g. could be before first table)
                    if first_col: # Avoid printing for completely empty lines already skipped
                        print(f"Skipping unclassified row {row_num}: {row}")


            # Process the last table in the file
            if current_table_name and current_items:
                processed_tables_count +=1
                existing_table = crud.get_roll_table_by_name(db, name=current_table_name)
                if existing_table:
                    print(f"Rolltable '{current_table_name}' already exists. Skipping.")
                else:
                    roll_table_data = models.RollTableCreate(
                        name=current_table_name,
                        description=current_table_description,
                        items=current_items
                    )
                    crud.create_roll_table(db, roll_table=roll_table_data)
                    created_tables_count += 1
                    print(f"Created rolltable: '{current_table_name}' with {len(current_items)} items.")
        
        print(f"--- Rolltable Migration Finished ---")
        print(f"Processed {processed_tables_count} tables from file. Created {created_tables_count} new rolltables.")

    except Exception as e:
        print(f"An error occurred during rolltable migration: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting data migration script...")
    # Initialize DB and create tables
    print("Initializing database and creating tables if they don't exist...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        sys.exit(1)

    migrate_features()
    migrate_roll_tables()
    print("\nData migration script finished.")

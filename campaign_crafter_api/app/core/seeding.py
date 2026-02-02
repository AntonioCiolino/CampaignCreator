import csv
import logging
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session

from app import crud, models # Standardized import

logger = logging.getLogger(__name__)
# Base path for CSV files relative to this file (app/core/seeding.py)
# project_root is app/core/seeding.py -> app/core -> app -> campaign_crafter_api
CSV_BASE_PATH = Path(__file__).resolve().parent.parent.parent / "csv"
FEATURES_CSV_PATH = CSV_BASE_PATH / "features.csv"
ROLLTABLES_CSV_PATH = CSV_BASE_PATH / "tables1e.csv"

def seed_features(db: Session):
    logger.info("--- Seeding Features ---")
    try:
        if not FEATURES_CSV_PATH.is_file():
            logger.error(f": Features CSV file not found at {FEATURES_CSV_PATH}")
            return

        with open(FEATURES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            expected_cols = ["Name", "Template", "RequiredContext", "CompatibleTypes", "FeatureCategory"]
            if not header or not all(col in header for col in expected_cols):
                logger.error(f": Invalid CSV header for features. Expected all of: {', '.join(expected_cols)}. Got: {header}")
                return
            
            name_idx = header.index("Name")
            template_idx = header.index("Template")
            context_idx = header.index("RequiredContext")
            types_idx = header.index("CompatibleTypes")
            category_idx = header.index("FeatureCategory")

            processed_count = 0
            created_count = 0
            updated_count = 0
            skipped_malformed = 0
            for row_num, row in enumerate(reader, 1):
                processed_count += 1
                if len(row) <= max(name_idx, template_idx, context_idx, types_idx, category_idx): # Check if all expected indices are within row bounds
                    logger.debug(f"Skipping malformed row {row_num} in features.csv: Insufficient columns. Expected at least {max(name_idx, template_idx, context_idx, types_idx, category_idx) + 1}, got {len(row)}. Content: {row}")
                    skipped_malformed +=1
                    continue
                
                feature_name = row[name_idx].strip()
                feature_template = row[template_idx].strip()
                required_context_str = row[context_idx].strip()
                compatible_types_str = row[types_idx].strip()
                feature_category_str = row[category_idx].strip()

                if not feature_name or not feature_template:
                    logger.debug(f"Skipping row {row_num} in features.csv: Empty name or template. Content: {row}")
                    skipped_malformed +=1
                    continue

                required_context_list = [ctx.strip() for ctx in required_context_str.split(';') if ctx.strip()] if required_context_str else []
                compatible_types_list = [ctype.strip() for ctype in compatible_types_str.split(';') if ctype.strip()] if compatible_types_str else []
                # Ensure feature_category is None if the string is empty, otherwise use the string
                feature_category = feature_category_str if feature_category_str else None


                existing_feature = crud.get_feature_by_name(db, name=feature_name)
                feature_data_dict = {
                    "name": feature_name,
                    "template": feature_template,
                    "required_context": required_context_list,
                    "compatible_types": compatible_types_list,
                    "feature_category": feature_category
                }

                if existing_feature:
                    needs_update = False
                    if existing_feature.template != feature_template:
                        existing_feature.template = feature_template
                        needs_update = True
                    if existing_feature.required_context != required_context_list:
                        existing_feature.required_context = required_context_list
                        needs_update = True
                    if existing_feature.compatible_types != compatible_types_list:
                        existing_feature.compatible_types = compatible_types_list
                        needs_update = True
                    if existing_feature.feature_category != feature_category:
                        existing_feature.feature_category = feature_category
                        needs_update = True

                    if needs_update:
                        logger.info(f"Feature '{feature_name}' already exists. Updating fields.")
                        db.add(existing_feature)
                        updated_count += 1
                    else:
                        logger.info(f"Feature '{feature_name}' already exists and fields are identical. Skipping update.")
                else:
                    feature_create_obj = models.FeatureCreate(**feature_data_dict)
                    crud.create_feature(db, feature=feature_create_obj)
                    created_count += 1
                    logger.info(f"Created feature: '{feature_name}' Category: '{feature_category}' Context: {required_context_list} Types: {compatible_types_list}")

        logger.info(f"--- Feature Seeding Finished ---")
        logger.info(f"Processed {processed_count} data rows. Created {created_count} new features. Updated {updated_count} existing features. Skipped {skipped_malformed} malformed rows.")

    except FileNotFoundError:
        logger.error(f": Features CSV file not found at {FEATURES_CSV_PATH}. Please ensure the file exists.")
    except Exception as e:
        logger.error(f"An error occurred during feature seeding: {e}")


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
    logger.info("--- Seeding Rolltables ---")
    try:
        if not ROLLTABLES_CSV_PATH.is_file():
            logger.error(f": Rolltables CSV file not found at {ROLLTABLES_CSV_PATH}")
            return

        current_table_name: str | None = None
        current_table_description: str | None = None
        current_items: list[models.RollTableItemCreate] = []
        
        tables_processed_from_file = 0
        tables_actually_created = 0

        with open(ROLLTABLES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t') 
            
            for row_num, row in enumerate(reader, 1):
                if not row or not row[0].strip(): 
                    continue

                first_col = row[0].strip()

                if first_col.startswith('d') and len(row) > 1 and row[1].strip():
                    if current_table_name and current_items:
                        tables_processed_from_file += 1
                        logger.debug(f"Checking database for existing rolltable: '{current_table_name}'...")
                        existing_table = crud.get_roll_table_by_name(db, name=current_table_name)
                        if existing_table:
                            logger.info(f"Rolltable '{current_table_name}' already exists. Skipping.")
                        else:
                            logger.info(f"Creating rolltable: '{current_table_name}' with {len(current_items)} items.")
                            roll_table_data = models.RollTableCreate(
                                name=current_table_name,
                                description=current_table_description,
                                items=current_items
                            )
                            crud.create_roll_table(db, roll_table=roll_table_data)
                            tables_actually_created += 1
                    
                    current_items = []
                    current_table_description = first_col 
                    current_table_name = row[1].strip()
                    logger.debug(f"Encountered new table definition in CSV: '{current_table_name}' ({current_table_description})")

                elif current_table_name and len(row) > 1: 
                    roll_range_str = row[0].strip()
                    item_description = row[1].strip()

                    if not roll_range_str or not item_description:
                        logger.debug(f"Skipping malformed item row {row_num} for table '{current_table_name}': {row}")
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
                        logger.warning(f"Invalid roll range '{roll_range_str}' in item row {row_num} for table '{current_table_name}'. Skipping item.")
                    except Exception as e:
                        logger.error(f"Error processing item row {row_num} for table '{current_table_name}': {e}. Skipping item.")

            if current_table_name and current_items: # Process the last table
                tables_processed_from_file += 1
                logger.debug(f"Checking database for existing rolltable (last table in file): '{current_table_name}'...")
                existing_table = crud.get_roll_table_by_name(db, name=current_table_name)
                if existing_table:
                    logger.info(f"Rolltable '{current_table_name}' already exists. Skipping.")
                else:
                    logger.info(f"Creating rolltable (last table in file): '{current_table_name}' with {len(current_items)} items.")
                    roll_table_data = models.RollTableCreate(
                        name=current_table_name,
                        description=current_table_description,
                        items=current_items
                    )
                    crud.create_roll_table(db, roll_table=roll_table_data)
                    tables_actually_created += 1
        
        logger.info(f"--- Rolltable Seeding Finished ---")
        logger.debug(f"Encountered {tables_processed_from_file} table definitions in CSV. Created {tables_actually_created} new rolltables in the database.")

    except FileNotFoundError: # More specific error handling
        logger.error(f": Rolltables CSV file not found at {ROLLTABLES_CSV_PATH}. Please ensure the file exists.")
    except Exception as e:
        logger.error(f"An error occurred during rolltable seeding: {e}")

def seed_all_csv_data(db: Session):
    """Seeds all data from CSV files into the database."""
    logger.info("--- Starting All CSV Data Seeding (from app.core.seeding) ---")
    seed_features(db)
    seed_roll_tables(db)
    seed_initial_superuser(db) # Add call to seed superuser
    logger.info("--- All CSV Data Seeding Finished (from app.core.seeding) ---")

def seed_initial_superuser(db: Session):
    logger.info("--- Seeding Initial Superuser ---")
    try:
        users = crud.get_users(db, limit=1)
        if not users:
            default_username = "admin"
            default_password = "changeme" # TODO: Make this configurable via environment variables for production
            default_email = "admin@example.com"

            logger.info(f"No users found in the database. Creating default superuser '{default_username}' with email '{default_email}'.")
            logger.warning(f"IMPORTANT: Default password is 'changeme'. Please change it immediately after first login.")

            superuser_in = models.UserCreate(
                username=default_username,
                password=default_password, # crud.create_user will hash this
                email=default_email,
                is_superuser=True
                # Pydantic model UserCreate does not have 'disabled', ORM model handles default
            )
            crud.create_user(db=db, user=superuser_in)
            logger.info(f"Default superuser '{default_username}' created successfully.")
        else:
            logger.info(f"Users already exist in the database. Skipping default superuser creation.")
        logger.info("--- Initial Superuser Seeding Finished ---")
    except Exception as e:
        logger.error(f"An error occurred during initial superuser seeding: {e}")
        # Optionally, re-raise if this is critical and should halt startup,
        # or handle more gracefully depending on application requirements.

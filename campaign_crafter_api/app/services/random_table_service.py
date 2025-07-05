import csv
import random
from typing import List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from app import crud, models, orm_models # Assuming models might be needed for Pydantic types if returned

class TableNotFoundError(Exception):
    """Custom exception for when a table is not found."""
    pass

class RandomTableService:

    def get_available_table_names(self, db: Session, user_id: Optional[int] = None) -> List[str]:
        """
        Retrieves a list of all available roll table names from the database.
        If a user_id is provided, it includes tables owned by that user and system tables.
        Otherwise, it includes only system tables.
        User-specific tables take precedence in case of name collision with system tables.
        """
        tables = crud.get_roll_tables(db, limit=1000, user_id=user_id) # Assuming a reasonable limit

        # Prioritize user-specific tables in case of name collision
        table_names_map: Dict[str, bool] = {} # Using a more descriptive name
        for table in tables:
            # If table name not in map, add it.
            # If table name IS in map, but current table is user-owned (user_id is not None),
            # it means the existing one must be a system table, so overwrite.
            if table.name not in table_names_map or table.user_id is not None:
                table_names_map[table.name] = True
        return list(table_names_map.keys())

    def get_random_item_from_table(self, table_name: str, db: Session, user_id: Optional[int] = None) -> Optional[str]:
        """
        Retrieves a random item from the specified roll table using dice roll logic.
        If user_id is provided, it prioritizes the user's table, then system tables.
        """
        db_roll_table = crud.get_roll_table_by_name(db, name=table_name, user_id=user_id)

        if not db_roll_table:
            raise TableNotFoundError(f"Table '{table_name}' not found for the user or as a system table.")
        
        if not db_roll_table.items:
            # Table exists but has no items
            return None 

        min_possible_roll = 1
        max_possible_roll = 0

        # Attempt to parse max roll from table description (e.g., "d100", "d20")
        if db_roll_table.description and db_roll_table.description.startswith('d'):
            try:
                max_possible_roll = int(db_roll_table.description[1:])
            except ValueError:
                # Description is not in "dX" format, try to infer from items
                pass # Fall through to infer from items
        
        if max_possible_roll == 0: # If not determined from description or parsing failed
            # Infer from actual min/max values in items if not standard dX table
            # This provides a fallback if description isn't dX or is missing
            if not db_roll_table.items: return None # Should be caught above, but defensive
            
            # min_roll_in_items = min(item.min_roll for item in db_roll_table.items)
            # This is not necessarily the dice min, dice usually start at 1.
            # We should use the max_roll from items as the max dice roll value.
            max_roll_in_items = max(item.max_roll for item in db_roll_table.items)
            
            # If description was not like "d100", use the max roll found in items.
            # Min roll is still assumed to be 1 for typical dice.
            max_possible_roll = max_roll_in_items
            # min_possible_roll could be set to min_roll_in_items if non-standard dice.
            # For now, assume standard dice start at 1.

        if max_possible_roll == 0 : # Still zero, means no items or bad data.
             # This case should ideally be prevented by data validation or if table has no items.
            return None


        # Perform the roll
        roll = random.randint(min_possible_roll, max_possible_roll)

        for item in db_roll_table.items:
            if item.min_roll <= roll <= item.max_roll:
                return item.description
        
        # This should ideally not be reached if the table items cover the full roll range.
        # Could indicate a gap in the table data.
        # For example, d100 table where items only go up to 90. A roll of 95 would find nothing.
        print(f"Warning: Rolled {roll} for table '{table_name}', but no matching item found. Check table data for gaps.")
        return None


# Example usage (for testing - requires database setup and data):
# if __name__ == '__main__':
#     from app.db import SessionLocal, engine, Base
#     # Base.metadata.create_all(bind=engine) # Ensure tables are created via migration script
# 
#     db = SessionLocal()
#     service = RandomTableService()
# 
#     print("Available tables:")
#     try:
#         table_names = service.get_available_table_names(db)
#         for name in table_names:
#             print(f"- {name}")
# 
#         # Example: Test with a known table (ensure 'Magic Items' table exists from migration)
#         # test_table_name = "Magic Items" # Or any table loaded by your migration
#         # if test_table_name in table_names:
#         #     print(f"\nRandom item from '{test_table_name}':")
#         #     for _ in range(5): # Roll 5 times
#         #         item = service.get_random_item_from_table(test_table_name, db)
#         #         print(item if item else "No item found for roll.")
#         # else:
#         #     print(f"\nTest table '{test_table_name}' not found in DB, skipping item roll test.")
# 
#     except Exception as e:
#         print(f"Error during testing: {e}")
# 
#     # Test with a non-existent table
#     try:
#         print("\nTrying to get item from 'NonExistent Table':")
#         service.get_random_item_from_table("NonExistent Table", db)
#     except TableNotFoundError as e:
#         print(e)
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#     finally:
#         db.close()

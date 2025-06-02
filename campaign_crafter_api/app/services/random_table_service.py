import random
from typing import List, Optional
from sqlalchemy.orm import Session
from app import crud, models, orm_models # Assuming models might be needed for Pydantic types if returned

class TableNotFoundError(Exception):
    """Custom exception for when a table is not found."""
    pass

class RandomTableService:

    def __init__(self, csv_file_path: Optional[Path] = None):
        self.random_tables: Dict[str, List[Tuple[int, str]]] = {}
        
        if csv_file_path is None:
            # Assuming the script is run from the project root or 'app' directory
            # Adjust if necessary based on execution context
            base_path = Path(__file__).resolve().parent.parent.parent.parent
            self.csv_path = base_path / "csv" / "tables1e.csv"
        else:
            self.csv_path = csv_file_path
            
        self._load_tables()

    def _load_tables(self):
        current_table_name = None
        current_table_items: List[Tuple[int, str]] = []

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t') # Assuming tab-separated
                for row_num, row in enumerate(reader):
                    if not row: # Skip empty rows
                        continue
                    
                    # Check if this row defines a new table (e.g., "d100	Fantasy Names")
                    if row[0].startswith('d') and len(row) > 1 and row[1].strip():
                        if current_table_name and current_table_items:
                            self.random_tables[current_table_name] = current_table_items
                        
                        current_table_name = row[1].strip()
                        current_table_items = []
                    elif current_table_name:
                        # This row is an item for the current table
                        try:
                            # Try to parse the first column as a number (range or single value)
                            # For simplicity, we'll treat single numbers as a range of 1.
                            # e.g., "1" becomes 1, "1-5" becomes 5 (max of range)
                            # The original script might have more complex range parsing.
                            # This simplified version assumes the first value is the roll result.
                            
                            roll_value_str = row[0].strip()
                            item_description = row[1].strip() if len(row) > 1 else f"Unnamed Item {row_num}"

                            if not item_description: # Skip if item description is empty
                                continue

                            # Basic range handling (e.g., "1", "1-5")
                            if '-' in roll_value_str:
                                # For ranges, we store the item multiple times up to max of range
                                # or handle it differently in get_random_item.
                                # Simplified: use the lower bound as the key for now or expand.
                                # The original script's logic for range mapping was complex.
                                # This version will just use the number before the dash.
                                first_val_str = roll_value_str.split('-')[0].strip()
                                roll_value = int(first_val_str)

                            else:
                                roll_value = int(roll_value_str)
                            
                            current_table_items.append((roll_value, item_description))
                        except ValueError:
                            print(f"Warning: Skipping malformed row in table '{current_table_name}': {row}")
                        except IndexError:
                            print(f"Warning: Skipping row with missing data in table '{current_table_name}': {row}")


                # Add the last table being processed
                if current_table_name and current_table_items:
                    self.random_tables[current_table_name] = current_table_items
        
        except FileNotFoundError:
            print(f"Error: The CSV file was not found at {self.csv_path}")
            # Depending on requirements, could raise an error or operate with empty tables
        except Exception as e:
            print(f"An error occurred while loading tables: {e}")


    def get_available_table_names(self) -> List[str]:
        return list(self.random_tables.keys())

    def get_available_table_names(self, db: Session) -> List[str]:
        """
        Retrieves a list of all available roll table names from the database.
        """
        tables = crud.get_roll_tables(db, limit=1000) # Assuming a reasonable limit for table names
        return [table.name for table in tables]

    def get_random_item_from_table(self, table_name: str, db: Session) -> Optional[str]:
        """
        Retrieves a random item from the specified roll table using dice roll logic.
        """
        db_roll_table = crud.get_roll_table_by_name(db, name=table_name)

        if not db_roll_table:
            raise TableNotFoundError(f"Table '{table_name}' not found.")
        
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

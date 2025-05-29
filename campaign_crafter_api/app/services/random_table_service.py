import csv
import random
from pathlib import Path
from typing import List, Optional, Dict, Tuple

class TableNotFoundError(Exception):
    """Custom exception for when a table is not found."""
    pass

class RandomTableService:
    def __init__(self, csv_file_path: Optional[Path] = None):
        self.random_tables: Dict[str, List[Tuple[int, str]]] = {}
        
        if csv_file_path is None:
            # Assuming the script is run from the project root or 'app' directory
            # Adjust if necessary based on execution context
            base_path = Path(__file__).resolve().parent.parent.parent 
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

    def get_random_item_from_table(self, table_name: str) -> Optional[str]:
        if table_name not in self.random_tables:
            raise TableNotFoundError(f"Table '{table_name}' not found.")
        
        table_items = self.random_tables[table_name]
        if not table_items:
            return None # Or raise an error if table is empty

        # The items are stored as (roll_value, description).
        # For a simple random choice, we can just pick one of the descriptions.
        # A more accurate d100 roll would require respecting the roll_values.
        # For now, a uniform random choice from the list of descriptions.
        
        # To simulate a roll, we'd do something like:
        # roll = random.randint(1, max_roll_value_for_table) 
        # Then find the item corresponding to that roll.
        # This simplified version just picks a random entry from the list of items.
        _, item_description = random.choice(table_items)
        return item_description

# Example usage (for testing):
if __name__ == '__main__':
    # This assumes the CSV is in ../../csv/tables1e.csv relative to this file
    # or that the script is run from project root.
    
    # For direct execution testing, provide the correct path if needed:
    # test_csv_path = Path(__file__).resolve().parent.parent.parent / "csv" / "tables1e.csv"
    # print(f"Looking for CSV at: {test_csv_path}")
    # service = RandomTableService(csv_file_path=test_csv_path)
    
    service = RandomTableService() # Assumes correct path resolution

    print("Available tables:")
    table_names = service.get_available_table_names()
    for name in table_names:
        print(f"- {name}")

    if table_names:
        selected_table = table_names[0] # Pick the first table for testing
        print(f"\nRandom item from '{selected_table}':")
        item = service.get_random_item_from_table(selected_table)
        print(item)

        # Test with a non-existent table
        try:
            print("\nTrying to get item from 'NonExistent Table':")
            service.get_random_item_from_table("NonExistent Table")
        except TableNotFoundError as e:
            print(e)

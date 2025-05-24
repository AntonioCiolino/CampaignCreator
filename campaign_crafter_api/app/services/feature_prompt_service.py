import csv
from pathlib import Path
from typing import Dict, Optional

class FeaturePromptService:
    def __init__(self, csv_file_path: Optional[Path] = None):
        self.prompts: Dict[str, str] = {}
        
        if csv_file_path is None:
            base_path = Path(__file__).resolve().parent.parent.parent 
            self.csv_path = base_path / "csv" / "features.csv"
        else:
            self.csv_path = csv_file_path
            
        self._load_prompts()

    def _load_prompts(self):
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=',') # Comma-separated
                for row_num, row in enumerate(reader):
                    if not row or len(row) < 2: # Skip empty or malformed rows
                        print(f"Warning: Skipping malformed row {row_num+1} in {self.csv_path}: {row}")
                        continue
                    
                    feature_name = row[0].strip()
                    prompt_template = row[1].strip()
                    
                    if not feature_name or not prompt_template:
                        print(f"Warning: Skipping row {row_num+1} with empty feature name or prompt in {self.csv_path}: {row}")
                        continue
                        
                    self.prompts[feature_name] = prompt_template
            
            if not self.prompts:
                print(f"Warning: No prompts were loaded from {self.csv_path}. The file might be empty or all rows were malformed.")

        except FileNotFoundError:
            print(f"Error: The prompt CSV file was not found at {self.csv_path}. Feature prompts will not be available.")
            # In a real application, this might raise an error or use hardcoded defaults.
        except Exception as e:
            print(f"An error occurred while loading prompts from {self.csv_path}: {e}")
            # Similar handling for other errors.

    def get_prompt(self, feature_name: str) -> Optional[str]:
        return self.prompts.get(feature_name)

# Example usage (for testing):
if __name__ == '__main__':
    # This assumes the CSV is in ../../csv/features.csv relative to this file
    # or that the script is run from project root.
    
    # For direct execution testing, provide the correct path if needed:
    # test_csv_path = Path(__file__).resolve().parent.parent.parent / "csv" / "features.csv"
    # print(f"Looking for prompt CSV at: {test_csv_path}")
    # service = FeaturePromptService(csv_file_path=test_csv_path)
    
    service = FeaturePromptService() # Assumes correct path resolution

    print("Loaded prompts:")
    if service.prompts:
        for name, template in service.prompts.items():
            print(f"- Feature: '{name}'\n  Template: '{template}'\n")
    else:
        print("No prompts loaded.")

    print(f"Test get_prompt('Campaign'): {service.get_prompt('Campaign')}")
    print(f"Test get_prompt('NonExistentFeature'): {service.get_prompt('NonExistentFeature')}")

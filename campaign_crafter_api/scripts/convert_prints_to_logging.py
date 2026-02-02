#!/usr/bin/env python3
"""
Script to convert print() statements to proper logging calls.
Run from campaign_crafter_api directory.
"""
import re
import os

# Files to process
FILES_TO_PROCESS = [
    "app/core/seeding.py",
    "app/api/endpoints/user_settings.py",
    "app/api/endpoints/image_generation.py",
    "app/api/endpoints/import_data.py",
    "app/api/endpoints/llm_management.py",
    "app/api/endpoints/characters.py",
    "app/api/endpoints/file_uploads.py",
    "app/api/endpoints/utility_endpoints.py",
    "app/main.py",
    "app/services/random_table_service.py",
    "app/services/llm_service.py",
    "app/services/local_llm_service.py",
    "app/services/export_service.py",
    "app/services/gemini_service.py",
    "app/services/deepseek_service.py",
    "app/services/llama_service.py",
    "app/crud.py",
]

# Patterns to convert (pattern, replacement_level)
PATTERNS = [
    (r'print\(f?"ERROR', 'logger.error(f"'),
    (r'print\(f?"Warning', 'logger.warning(f"'),
    (r'print\(f?"WARNING', 'logger.warning(f"'),
    (r'print\(f?"Info', 'logger.info(f"'),
    (r'print\(f?"INFO', 'logger.info(f"'),
    (r'print\(f?"DEBUG', 'logger.debug(f"'),
    (r'print\(f?"Attempting', 'logger.debug(f"Attempting'),
    (r'print\(f?"Successfully', 'logger.info(f"Successfully'),
    (r'print\(f?"Failed', 'logger.error(f"Failed'),
    (r'print\(f?"Error', 'logger.error(f"Error'),
    (r'print\(f?"Skipping', 'logger.debug(f"Skipping'),
    (r'print\(f?"Created', 'logger.info(f"Created'),
    (r'print\(f?"Updated', 'logger.info(f"Updated'),
    (r'print\(f?"Checking', 'logger.debug(f"Checking'),
    (r'print\(f?"Fetching', 'logger.debug(f"Fetching'),
    (r'print\(f?"Could not', 'logger.warning(f"Could not'),
    (r'print\(f?"No ', 'logger.info(f"No '),
    (r'print\(f?"An error', 'logger.error(f"An error'),
    (r'print\(f?"Unexpected', 'logger.error(f"Unexpected'),
    (r'print\(f?"Network', 'logger.error(f"Network'),
    (r'print\(f?"Service', 'logger.info(f"Service'),
    (r'print\(f?"CRUD', 'logger.debug(f"CRUD'),
    (r'print\(f?"LLM', 'logger.warning(f"LLM'),
    (r'print\(f?"Gemini', 'logger.warning(f"Gemini'),
    (r'print\(f?"OpenAI', 'logger.warning(f"OpenAI'),
    (r'print\(f?"Stable', 'logger.warning(f"Stable'),
    (r'print\(f?"Image', 'logger.info(f"Image'),
    (r'print\(f?"Blob', 'logger.debug(f"Blob'),
    (r'print\(f?"Rolltable', 'logger.info(f"Rolltable'),
    (r'print\(f?"Feature', 'logger.info(f"Feature'),
    (r'print\(f?"Processed', 'logger.info(f"Processed'),
    (r'print\(f?"Encountered', 'logger.debug(f"Encountered'),
    (r'print\(f?"Users', 'logger.info(f"Users'),
    (r'print\(f?"IMPORTANT', 'logger.warning(f"IMPORTANT'),
    (r'print\(f?"Default', 'logger.info(f"Default'),
    (r'print\(f?"Database', 'logger.info(f"Database'),
    (r'print\(f?"Data', 'logger.info(f"Data'),
    (r'print\(f?"Application', 'logger.info(f"Application'),
    (r'print\(f?"Starting', 'logger.info(f"Starting'),
    (r'print\(f?"Rolled', 'logger.warning(f"Rolled'),
    (r'print\(f?"Dummy', 'logger.debug(f"Dummy'),
    (r'print\(f?"Constructed', 'logger.debug(f"Constructed'),
    (r'print\(f?"Deleting', 'logger.debug(f"Deleting'),
    (r'print\(f?"Summarized', 'logger.info(f"Summarized'),
    (r'print\(f?"Memory', 'logger.info(f"Memory'),
    (r'print\(f?"Character', 'logger.debug(f"Character'),
    (r'print\(f?"User', 'logger.debug(f"User'),
    (r'print\(f?"Conversation', 'logger.debug(f"Conversation'),
    # Generic patterns (catch remaining)
    (r'print\("---', 'logger.info("---'),
    (r'print\(f"---', 'logger.info(f"---'),
    (r'print\(error_detail\)', 'logger.error(error_detail)'),
]

def add_logging_import(content: str) -> str:
    """Add logging import if not present."""
    if 'import logging' in content:
        return content
    
    # Find the first import line
    lines = content.split('\n')
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_idx = i
            break
    
    # Insert logging import after first import
    lines.insert(import_idx + 1, 'import logging')
    
    # Find where to add logger = logging.getLogger(__name__)
    # Look for the last import or after class definition
    logger_line = '\nlogger = logging.getLogger(__name__)\n'
    
    # Find the end of imports
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
    
    # Check if logger already defined
    if 'logger = logging.getLogger' not in content:
        lines.insert(last_import_idx + 2, 'logger = logging.getLogger(__name__)')
    
    return '\n'.join(lines)

def convert_prints(content: str) -> str:
    """Convert print statements to logger calls."""
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content)
    return content

def process_file(filepath: str) -> bool:
    """Process a single file."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        original = f.read()
    
    # Add logging import
    content = add_logging_import(original)
    
    # Convert prints
    content = convert_prints(content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated: {filepath}")
        return True
    else:
        print(f"No changes: {filepath}")
        return False

def main():
    updated = 0
    for filepath in FILES_TO_PROCESS:
        if process_file(filepath):
            updated += 1
    print(f"\nTotal files updated: {updated}/{len(FILES_TO_PROCESS)}")

if __name__ == "__main__":
    main()

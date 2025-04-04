# Directory Listing

This directory contains a simple utility for recursively listing all files in a given directory.

## Purpose
The `directory_lister.py` script provides a function that can recursively traverse a directory and list all file paths within it. This can be useful for:
- Getting a complete inventory of files in a directory structure
- Finding specific files across multiple subdirectories
- Analyzing directory contents programmatically

## Usage
The script can be run directly or imported as a module:

1. Direct usage:
```python
python directory_lister.py
```
Then enter the base directory path when prompted.

2. Import as module:
```python
from directory_lister import list_all_files

files = list_all_files("path/to/directory")
```

## Function Details
The main function `list_all_files(base_dir)`:
- Takes a base directory path as input
- Returns a list of all file paths found in the directory and its subdirectories
- Uses `os.walk()` for efficient directory traversal
- Handles errors gracefully with try-except blocks 
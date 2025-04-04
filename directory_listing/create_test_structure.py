import os
import random
from pathlib import Path

def create_test_structure(base_dir: str, min_depth: int = 3, max_depth: int = 6, 
                         min_files_per_dir: int = 10, max_files_per_dir: int = 30,
                         min_subdirs_per_dir: int = 5, max_subdirs_per_dir: int = 10):
    """
    Creates a complex test directory structure with random depths and files.
    
    Args:
        base_dir (str): Base directory to create structure in
        min_depth (int): Minimum depth of directory tree
        max_depth (int): Maximum depth of directory tree
        min_files_per_dir (int): Minimum files per directory
        max_files_per_dir (int): Maximum files per directory
        min_subdirs_per_dir (int): Minimum subdirectories per directory
        max_subdirs_per_dir (int): Maximum subdirectories per directory
    """
    def create_dir_structure(current_path: Path, current_depth: int):
        if current_depth > max_depth:
            return
        
        # Create random number of files in current directory
        num_files = random.randint(min_files_per_dir, max_files_per_dir)
        for i in range(num_files):
            file_path = current_path / f"file_{current_depth}_{i}.txt"
            file_path.write_text(f"This is file {i} at depth {current_depth}")
        
        # Create subdirectories if not at max depth
        if current_depth < max_depth:
            num_subdirs = random.randint(min_subdirs_per_dir, max_subdirs_per_dir)
            for i in range(num_subdirs):
                subdir_path = current_path / f"dir_{current_depth}_{i}"
                subdir_path.mkdir(exist_ok=True)
                create_dir_structure(subdir_path, current_depth + 1)
    
    # Create base directory if it doesn't exist
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    # Start creating the structure
    create_dir_structure(base_path, 1)
    print(f"Created test directory structure in: {base_dir}")

if __name__ == "__main__":
    test_dir = os.path.join(".", "complex_test_dir")
    
    # Remove existing directory if it exists
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)
    
    # Create a much larger structure
    print("Creating test directory structure...")
    create_test_structure(
        test_dir,
        min_depth=3,      # Start with deeper minimum depth
        max_depth=6,      # Allow deeper maximum depth
        min_files_per_dir=10,    # More files per directory
        max_files_per_dir=30,    # More maximum files
        min_subdirs_per_dir=5,   # More minimum subdirectories
        max_subdirs_per_dir=10   # More maximum subdirectories
    )
    
    # Count total files created
    print("Counting total files...")
    total_files = 0
    total_dirs = 0
    for root, dirs, files in os.walk(test_dir):
        total_files += len(files)
        total_dirs += len(dirs)
    
    print(f"Total directories created: {total_dirs:,}")
    print(f"Total files created: {total_files:,}") 
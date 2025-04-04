import os
import time
import multiprocessing
from typing import List, Dict
from concurrent.futures import ProcessPoolExecutor

def get_directory_depth(path: str) -> int:
    """Calculate the depth of a directory path."""
    return len(os.path.normpath(path).split(os.sep))

def process_directory(args: tuple) -> List[str]:
    """
    Process a single directory and return its files.
    
    Args:
        args: Tuple containing (dir_path, target_depth)
    """
    dir_path, _ = args  # target_depth is not needed anymore
    files_in_dir = []
    
    # Only process the given directory and its subdirectories
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            files_in_dir.append(file_path)
    
    return files_in_dir

def get_directories_at_depth(base_dir: str, target_depth: int) -> List[str]:
    """
    Get all directories at a specific depth.
    
    Args:
        base_dir (str): Base directory to start from
        target_depth (int): Target depth to find directories at
        
    Returns:
        List[str]: List of directory paths at the target depth
    """
    directories = []
    for root, dirs, _ in os.walk(base_dir):
        current_depth = get_directory_depth(root)
        if current_depth == target_depth - 1:
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                directories.append(dir_path)
    return directories

def list_all_files_single(base_dir: str) -> List[str]:
    """
    Recursively lists all file paths in the given directory using a single process.
    
    Args:
        base_dir (str): The base directory path to start listing from
        
    Returns:
        List[str]: A list of all file paths found in the directory and its subdirectories
    """
    all_files = []
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)
    
    return all_files

def list_all_files_parallel(base_dir: str, target_depth: int) -> List[str]:
    """
    Recursively lists all file paths in the given directory using parallel processing.
    Directories above target depth are processed in the current process,
    while directories at or below target depth are processed in parallel.
    
    Args:
        base_dir (str): The base directory path to start listing from
        target_depth (int): The depth at which to start parallel processing
        
    Returns:
        List[str]: A list of all file paths found in the directory and its subdirectories
    """
    all_files = []
    
    # First, process directories above target depth in the current process
    for root, _, files in os.walk(base_dir):
        current_depth = get_directory_depth(root)
        if current_depth < target_depth:
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
    
    # Then, get all directories at target depth
    directories = get_directories_at_depth(base_dir, target_depth)
    
    if not directories:
        print(f"No directories found at or below depth {target_depth}")
        return all_files
    
    # Process directories at or below target depth in parallel
    tasks = [(dir_path, target_depth) for dir_path in directories]
    
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_directory, tasks)
        for files_in_dir in results:
            all_files.extend(files_in_dir)
    
    return all_files

def measure_execution_time(func, *args, **kwargs):
    """
    Measure the execution time of a function.
    
    Args:
        func: The function to measure
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        tuple: (result, execution_time)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def main():
    # Test with the current directory
    test_dir = os.path.join(".", "complex_test_dir")
    print(f"Listing all files in: {test_dir}")
    
    try:
        # Fixed target depth
        target_depth = 4
        
        # Run single process version
        print("\nRunning single process version...")
        single_files, single_time = measure_execution_time(list_all_files_single, test_dir)
        print(f"Single process found {len(single_files)} files in {single_time:.2f} seconds")
        
        # Run parallel version
        print(f"\nRunning parallel process version starting from depth {target_depth}...")
        parallel_files, parallel_time = measure_execution_time(list_all_files_parallel, test_dir, target_depth)
        print(f"Parallel process found {len(parallel_files)} files in {parallel_time:.2f} seconds")
        
        # Compare results
        print("\nComparison:")
        print(f"Single process time: {single_time:.2f} seconds")
        print(f"Parallel process time: {parallel_time:.2f} seconds")
        print(f"Speedup: {single_time/parallel_time:.2f}x")
        
        # Verify both methods found the same files
        single_set = set(single_files)
        parallel_set = set(parallel_files)
        if single_set == parallel_set:
            print("\nVerification: Both methods found the same files")
        else:
            print("\nWarning: The two methods found different sets of files!")
            print(f"Files only in single process: {len(single_set - parallel_set)}")
            print(f"Files only in parallel process: {len(parallel_set - single_set)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Set the start method to 'spawn' for better compatibility
    multiprocessing.set_start_method('spawn')
    main()

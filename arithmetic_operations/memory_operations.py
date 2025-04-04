"""
Module for calculating and validating memory sizes.
"""

from typing import List, Tuple

def calculate_total_size(words: int, bits: int) -> int:
    """
    Calculate the total size of memory
    
    Args:
        words (int): Number of words
        bits (int): Number of bits
        
    Returns:
        int: Total memory size (words * bits)
    """
    return words * bits

def validate_memory_size(target_words: int, target_bits: int, 
                        sub_sizes: List[Tuple[int, int]]) -> bool:
    """
    Validate if the sum of sub-memory sizes matches the target size
    
    Args:
        target_words (int): Target number of words
        target_bits (int): Target number of bits
        sub_sizes (List[Tuple[int, int]]): List of sub-memory sizes [(words, bits), ...]
        
    Returns:
        bool: True if the sum of sub-sizes equals the target size, False otherwise
    """
    target_total = calculate_total_size(target_words, target_bits)
    sub_total = sum(calculate_total_size(words, bits) for words, bits in sub_sizes)
    
    return target_total == sub_total

def test_memory_size():
    """
    Test function for memory size validation
    """
    # Test Case 1: Dividing 2048 x 128 memory into two 1024 x 128 blocks
    target_words = 2048
    target_bits = 128
    sub_sizes = [(1024, 128), (1024, 128)]
    
    result = validate_memory_size(target_words, target_bits, sub_sizes)
    print(f"Test Case 1: {'Pass' if result else 'Fail'}")
    
    # Test Case 2: Dividing 2048 x 128 memory into four 512 x 128 blocks
    sub_sizes = [(512, 128), (512, 128), (512, 128), (512, 128)]
    result = validate_memory_size(target_words, target_bits, sub_sizes)
    print(f"Test Case 2: {'Pass' if result else 'Fail'}")
    
    # Test Case 3: Invalid size combination
    sub_sizes = [(1024, 128), (1024, 64)]  # Different bit sizes
    result = validate_memory_size(target_words, target_bits, sub_sizes)
    print(f"Test Case 3: {'Pass' if not result else 'Fail'}")  # Should fail


test_memory_size() 
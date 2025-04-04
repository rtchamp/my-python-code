# Arithmetic Operations

This directory is created for implementing and testing various arithmetic operations.

## Implemented Features
- Basic arithmetic operations (addition, subtraction, multiplication, division)
- Complex mathematical operations (power, square root, logarithm, etc.)
- Memory size operations (memory size calculation and validation in words and bits)
- Custom operations

## File Structure
- `basic_operations.py`: Implementation of basic arithmetic operations
- `advanced_operations.py`: Implementation of advanced mathematical operations
- `memory_operations.py`: Memory size calculation and validation
- `tests/`: Test code directory

## Usage
Each Python file can be imported to use the required operations.

### Memory Size Operations Example
```python
from arithmetic_operations.memory_operations import validate_memory_size

# Dividing 2048 x 128 memory into two 1024 x 128 blocks
target_words = 2048
target_bits = 128
sub_sizes = [(1024, 128), (1024, 128)]
result = validate_memory_size(target_words, target_bits, sub_sizes)  # Returns True
``` 
"""
고급 수학 연산을 구현한 모듈입니다.
"""
import math

def square_root(x: float) -> float:
    """
    제곱근을 계산하는 함수
    
    Args:
        x (float): 제곱근을 구할 숫자
        
    Returns:
        float: x의 제곱근
        
    Raises:
        ValueError: x가 음수일 때 발생
    """
    if x < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(x)

def logarithm(x: float, base: float = math.e) -> float:
    """
    로그를 계산하는 함수
    
    Args:
        x (float): 로그를 구할 숫자
        base (float): 로그의 밑 (기본값: 자연로그)
        
    Returns:
        float: x의 로그값
        
    Raises:
        ValueError: x가 0 이하이거나 base가 1 이하일 때 발생
    """
    if x <= 0:
        raise ValueError("Cannot calculate logarithm of non-positive number")
    if base <= 1:
        raise ValueError("Logarithm base must be greater than 1")
    return math.log(x, base)

def factorial(n: int) -> int:
    """
    팩토리얼을 계산하는 함수
    
    Args:
        n (int): 팩토리얼을 구할 숫자
        
    Returns:
        int: n의 팩토리얼
        
    Raises:
        ValueError: n이 음수일 때 발생
    """
    if n < 0:
        raise ValueError("Cannot calculate factorial of negative number")
    return math.factorial(n)

def average(numbers: list[float]) -> float:
    """
    숫자들의 평균을 계산하는 함수
    
    Args:
        numbers (list[float]): 평균을 구할 숫자들의 리스트
        
    Returns:
        float: 숫자들의 평균
        
    Raises:
        ValueError: numbers가 비어있을 때 발생
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers) 
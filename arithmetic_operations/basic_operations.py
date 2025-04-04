"""
기본적인 산술 연산을 구현한 모듈입니다.
"""

def add(a: float, b: float) -> float:
    """
    두 숫자를 더하는 함수
    
    Args:
        a (float): 첫 번째 숫자
        b (float): 두 번째 숫자
        
    Returns:
        float: a와 b의 합
    """
    return a + b

def subtract(a: float, b: float) -> float:
    """
    두 숫자를 빼는 함수
    
    Args:
        a (float): 첫 번째 숫자
        b (float): 두 번째 숫자
        
    Returns:
        float: a에서 b를 뺀 값
    """
    return a - b

def multiply(a: float, b: float) -> float:
    """
    두 숫자를 곱하는 함수
    
    Args:
        a (float): 첫 번째 숫자
        b (float): 두 번째 숫자
        
    Returns:
        float: a와 b의 곱
    """
    return a * b

def divide(a: float, b: float) -> float:
    """
    두 숫자를 나누는 함수
    
    Args:
        a (float): 첫 번째 숫자
        b (float): 두 번째 숫자
        
    Returns:
        float: a를 b로 나눈 값
        
    Raises:
        ZeroDivisionError: b가 0일 때 발생
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b

def power(base: float, exponent: float) -> float:
    """
    거듭제곱을 계산하는 함수
    
    Args:
        base (float): 밑
        exponent (float): 지수
        
    Returns:
        float: base의 exponent 제곱
    """
    return base ** exponent 
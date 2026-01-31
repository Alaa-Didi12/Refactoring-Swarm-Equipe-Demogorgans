import pytest
from sample import add, subtract, multiply, divide

def test_add_positive_integers():
    """Test add with two positive integers."""
    assert add(2, 3) == 5

def test_add_negative_integers():
    """Test add with two negative integers."""
    assert add(-2, -3) == -5

def test_add_mixed_integers():
    """Test add with a positive and a negative integer."""
    assert add(5, -3) == 2
    assert add(-5, 3) == -2

def test_add_with_zero():
    """Test add with one or both numbers being zero."""
    assert add(0, 5) == 5
    assert add(5, 0) == 5
    assert add(0, 0) == 0

def test_add_floats():
    """Test add with float numbers."""
    assert add(2.5, 3.5) == 6.0
    assert add(-1.5, 2.0) == 0.5

def test_subtract_positive_integers():
    """Test subtract with two positive integers."""
    assert subtract(5, 2) == 3
    assert subtract(2, 5) == -3

def test_subtract_negative_integers():
    """Test subtract with two negative integers."""
    assert subtract(-5, -2) == -3
    assert subtract(-2, -5) == 3

def test_subtract_mixed_integers():
    """Test subtract with a positive and a negative integer."""
    assert subtract(5, -2) == 7
    assert subtract(-5, 2) == -7

def test_subtract_with_zero():
    """Test subtract with one or both numbers being zero."""
    assert subtract(5, 0) == 5
    assert subtract(0, 5) == -5
    assert subtract(0, 0) == 0

def test_subtract_floats():
    """Test subtract with float numbers."""
    assert subtract(5.5, 2.0) == 3.5
    assert subtract(2.0, 5.5) == -3.5

def test_multiply_positive_integers():
    """Test multiply with two positive integers."""
    assert multiply(2, 3) == 6

def test_multiply_negative_integers():
    """Test multiply with two negative integers."""
    assert multiply(-2, -3) == 6

def test_multiply_mixed_integers():
    """Test multiply with a positive and a negative integer."""
    assert multiply(2, -3) == -6
    assert multiply(-2, 3) == -6

def test_multiply_by_zero():
    """Test multiply when one or both numbers are zero."""
    assert multiply(5, 0) == 0
    assert multiply(0, 5) == 0
    assert multiply(0, 0) == 0

def test_multiply_floats():
    """Test multiply with float numbers."""
    assert multiply(2.5, 2.0) == 5.0
    assert multiply(-1.5, 3.0) == -4.5

def test_divide_positive_integers():
    """Test divide with two positive integers."""
    assert divide(6, 3) == 2.0
    assert divide(7, 2) == 3.5

def test_divide_negative_integers():
    """Test divide with two negative integers."""
    assert divide(-6, -3) == 2.0
    assert divide(-7, -2) == 3.5

def test_divide_mixed_integers():
    """Test divide with a positive and a negative integer."""
    assert divide(6, -3) == -2.0
    assert divide(-6, 3) == -2.0

def test_divide_floats():
    """Test divide with float numbers."""
    assert divide(7.5, 2.5) == 3.0
    assert divide(10.0, 4.0) == 2.5

def test_divide_by_one():
    """Test divide by 1."""
    assert divide(5, 1) == 5.0
    assert divide(-5, 1) == -5.0

def test_divide_zero_by_number():
    """Test divide 0 by a non-zero number."""
    assert divide(0, 5) == 0.0
    assert divide(0, -5) == 0.0

def test_divide_by_zero_raises_error():
    """Test divide by zero raises a ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(-5, 0)
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(0, 0)
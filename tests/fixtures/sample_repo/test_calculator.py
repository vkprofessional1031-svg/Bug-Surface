from calculator import add, divide, multiply, subtract, modulo


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 3) == 2


def test_multiply():
    assert multiply(4, 3) == 12


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    import pytest
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_modulo_by_zero():
    import pytest
    with pytest.raises(ValueError, match="Cannot compute modulo by zero"):
        modulo(10, 0)

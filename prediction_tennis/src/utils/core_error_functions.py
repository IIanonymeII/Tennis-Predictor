"""
Error Handling Utilities Module.

This module provides standardized error handling functions for logging
and raising exceptions. These utilities ensure consistent error reporting
across the application by combining logging with exception raising.

Functions in this module follow a pattern of:
1. Logging the error message at the appropriate level
2. Raising the corresponding exception with the same message

This approach ensures that all exceptions are properly logged before
being raised, facilitating debugging and error tracking.

Typical usage:
    >>> import logging
    >>> from error_utils import raise_value_error, raise_type_error
    >>>
    >>> logger = logging.getLogger(__name__)
    >>>
    >>> def validate_input(value):
    ...     if value < 0:
    ...         raise_value_error(
    ...             "Value must be non-negative",
    ...             logger
    ...         )
"""

import logging
from typing import Any, Tuple, Union


def raise_value_error(message: str, logger: logging.Logger, *args: Any, **kwargs: Any) -> None:
    """
    Log an error message and raise a ValueError.

    This function provides a standardized way to log and raise ValueError
    exceptions. It ensures that all value-related errors are properly
    logged before the exception is raised.

    Parameters
    ----------
    message : str
        The error message to log and include in the exception.
    logger : logging.Logger
        Logger instance to use for logging the error.
    *args : Any
        Additional positional arguments to pass to the ValueError.
    **kwargs : Any
        Additional keyword arguments (currently unused, reserved for
        future extensions).

    Raises
    ------
    ValueError
        Always raised with the provided message after logging.

    Examples
    --------
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> raise_value_error("Invalid parameter value: -5", logger)
    Traceback (most recent call last):
        ...
    ValueError: Invalid parameter value: -5

    >>> def validate_age(age):
    ...     if age < 0:
    ...         raise_value_error(f"Age cannot be negative: {age}", logger)
    ...     if age > 150:
    ...         raise_value_error(f"Age is unrealistic: {age}", logger)
    """
    logger.error(message)
    raise ValueError(message, *args)


def raise_type_error(message: str, logger: logging.Logger, *args: Any, **kwargs: Any) -> None:
    """
    Log an error message and raise a TypeError.

    This function provides a standardized way to log and raise TypeError
    exceptions. It ensures that all type-related errors are properly
    logged before the exception is raised.

    Parameters
    ----------
    message : str
        The error message to log and include in the exception.
    logger : logging.Logger
        Logger instance to use for logging the error.
    *args : Any
        Additional positional arguments to pass to the TypeError.
    **kwargs : Any
        Additional keyword arguments (currently unused, reserved for
        future extensions).

    Raises
    ------
    TypeError
        Always raised with the provided message after logging.

    Examples
    --------
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> raise_type_error("Expected int, got str", logger)
    Traceback (most recent call last):
        ...
    TypeError: Expected int, got str

    >>> def process_number(value):
    ...     if not isinstance(value, (int, float)):
    ...         raise_type_error(
    ...             f"Expected numeric type, got {type(value).__name__}",
    ...             logger
    ...         )
    """
    logger.error(message)
    raise TypeError(message, *args)


def raise_runtime_error(message: str, logger: logging.Logger, *args: Any, **kwargs: Any) -> None:
    """
    Log an error message and raise a RuntimeError.

    This function provides a standardized way to log and raise RuntimeError
    exceptions. It ensures that all runtime errors are properly logged
    before the exception is raised.

    Parameters
    ----------
    message : str
        The error message to log and include in the exception.
    logger : logging.Logger
        Logger instance to use for logging the error.
    *args : Any
        Additional positional arguments to pass to the RuntimeError.
    **kwargs : Any
        Additional keyword arguments (currently unused, reserved for
        future extensions).

    Raises
    ------
    RuntimeError
        Always raised with the provided message after logging.

    Examples
    --------
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> raise_runtime_error("Operation failed unexpectedly", logger)
    Traceback (most recent call last):
        ...
    RuntimeError: Operation failed unexpectedly

    >>> def perform_calculation(data):
    ...     try:
    ...         result = complex_operation(data)
    ...     except Exception as e:
    ...         raise_runtime_error(
    ...             f"Calculation failed: {e}",
    ...             logger
    ...         )
    """
    logger.error(message)
    raise RuntimeError(message, *args)


def validate_type(
    value: Any, expected_type: Union[type, Tuple[type, ...]], logger: logging.Logger
) -> None:
    """
    Validate that a value matches the expected type(s).

    Parameters
    ----------
    value : Any
        The value to be validated.
    expected_type : type or tuple of types
        The expected type or a tuple of acceptable types.
    logger : logging.Logger
        Logger instance used to record errors.

    Raises
    ------
    TypeError
        If the value does not match the expected type(s).
    """
    if not isinstance(value, expected_type):
        if isinstance(expected_type, tuple):
            expected_types_str = ", ".join(t.__name__ for t in expected_type)
            message = f"Expected one of ({expected_types_str}), got {type(value).__name__}"
        else:
            message = f"Expected {expected_type.__name__}, got {type(value).__name__}"

        raise_type_error(message, logger)

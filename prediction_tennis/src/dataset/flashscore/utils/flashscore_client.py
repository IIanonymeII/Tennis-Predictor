"""
FlashScore data retrieval and URL validation utilities module.

This module provides utility functions for retrieving data from FlashScore
using custom headers and validating URLs with HTTP status checks.
Both functions include retry logic for temporary network or server issues.
"""

import logging
import time
from typing import Union

import requests

logger = logging.getLogger("[UTIL] [FLASHSCORE_CLIENT]")


def retrieve_flashscore_data(
    url: str,
    return_as_text: bool = True,
    max_retries: int = 5,
    backoff_factor: float = 1.5,
) -> Union[str, requests.Response]:
    """
    Retrieve data from FlashScore using a custom header with retry logic.

    This function sends an HTTP GET request to the provided URL with the FlashScore
    specific header. If the request fails (network error or non-200 response),
    it retries up to `max_retries` times with exponential backoff.

    Parameters
    ----------
    url : str
        The URL from which to fetch data
    return_as_text : bool, optional
        If True, returns the response text; else, the response object (default True)
    max_retries : int, optional
        Maximum number of retries before raising an error (default 5)
    backoff_factor : float, optional
        Factor for exponential backoff delay between retries (default 1.5)

    Returns
    -------
    Union[str, requests.Response]
        The response text or the full response object

    Raises
    ------
    ConnectionError
        If all retries fail or the final HTTP response status code is not 200
    """
    headers = {"x-fsign": "SW9D1eZo"}  # FlashScore specific header

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Attempt %d/%d - Fetching data from URL: %s", attempt, max_retries, url)
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.debug("Data fetched successfully from %s", url)
                return response.text if return_as_text else response

            logger.warning(
                "HTTP %d on attempt %d for URL: %s",
                response.status_code,
                attempt,
                url,
            )

        except requests.exceptions.RequestException as e:
            logger.warning(
                "Request error on attempt %d/%d for %s: %s",
                attempt,
                max_retries,
                url,
                str(e),
            )

        # Wait before retrying (exponential backoff)
        if attempt < max_retries:
            sleep_time = backoff_factor**attempt
            logger.debug("Retrying in %.1f seconds...", sleep_time)
            time.sleep(sleep_time)

    # All retries failed
    error_message = f"Failed to fetch data from {url} after {max_retries} attempts."
    logger.error(error_message)
    raise ConnectionError(error_message)


def validate_and_check_url(
    url: str,
    max_retries: int = 5,
    backoff_factor: float = 1.5,
) -> str:
    """
    Validate a given URL and check if it exists via an HTTP GET request, with retry logic.

    This function verifies:
    - The URL begins with 'https://'
    - The URL is not empty or only spaces
    - The URL responds without returning a 404 error
    - If the request is Forbidden (403) or Unauthorized (401), it is still considered valid
    - Retries automatically if temporary connection errors occur

    Parameters
    ----------
    url : str
        The full URL to validate and check
    max_retries : int, optional
        Maximum number of retry attempts for failed requests (default 5)
    backoff_factor : float, optional
        Factor for exponential backoff delay between retries (default 1.5)

    Returns
    -------
    str
        The validated URL if it exists

    Raises
    ------
    ValueError
        If the URL structure is invalid
    Exception
        If the URL returns a 404 (Not Found) or request errors occur after all retries
    """
    logger.debug("Validating URL: %s", url)

    # Validate that URL begins with 'https://'
    if not url.startswith("https://"):
        error_msg = f"Invalid URL '{url}': must start with 'https://'"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Ensure the URL is not empty or improperly formatted
    if not url.strip():
        error_msg = "Invalid URL: URL cannot be empty or contain only spaces."
        logger.error(error_msg)
        raise ValueError(error_msg)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Attempt %d/%d - Checking URL: %s", attempt, max_retries, url)
            response = requests.get(url, timeout=10)

            if response.status_code == 404:
                error_msg = f"URL not found: {url} (HTTP 404)"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Accept 200, 401, 403 as valid
            if response.status_code in (200, 401, 403):
                logger.info("URL validated successfully: %s (%d)", url, response.status_code)
                return url

            logger.warning(
                "Unexpected status %d on attempt %d for URL: %s",
                response.status_code,
                attempt,
                url,
            )

        except requests.exceptions.RequestException as e:
            logger.warning(
                "Request error on attempt %d/%d for %s: %s",
                attempt,
                max_retries,
                url,
                str(e),
            )

        # Wait before retrying (exponential backoff)
        if attempt < max_retries:
            sleep_time = backoff_factor**attempt
            logger.debug("Retrying in %.1f seconds...", sleep_time)
            time.sleep(sleep_time)

    # All retries failed
    error_message = f"Failed to validate URL {url} after {max_retries} attempts."
    logger.error(error_message)
    raise Exception(error_message)

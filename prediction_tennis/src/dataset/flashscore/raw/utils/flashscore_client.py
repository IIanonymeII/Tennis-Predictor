import logging
from typing import Union

import requests


logger = logging.getLogger("[UTIL] [FLASHSCORE_CLIENT]")

def retrieve_flashscore_data(url: str, return_as_text: bool = True) -> Union[str, requests.Response]:
    """
    Retrieve data from FlashScore using a custom header.

    This function sends an HTTP GET request to the provided URL with the FlashScore
    specific header. It returns the response text if `return_as_text` is True,
    otherwise it returns the complete response object.

    Args:
        url (str): The URL from which to fetch data.
        return_as_text (bool): If True, returns the response text; else, the response object.

    Returns:
        Union[str, requests.Response]: The response text or the full response object.

    Raises:
        ConnectionError: If the HTTP response status code is not 200.
    """
    headers = {"x-fsign": "SW9D1eZo"}  # FlashScore specific header

    logger.info("Fetching data from URL: %s", url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        if return_as_text:
            logger.debug("Returning response text")
            return response.text

        logger.debug("Returning full response object")
        return response

    error_message = f"Failed to fetch data from {url}: HTTP {response.status_code}"
    logger.error(error_message)
    raise ConnectionError(error_message)
    
def validate_and_check_url(url: str) -> str:
    """
    Validates a given URL and checks if it exists via an HTTP GET request.

    This function verifies:
      - The URL begins with 'https://'.
      - The URL is not empty or only spaces.
      - The URL responds without returning a 404 error.
      - If the request is Forbidden (403), the URL is still considered valid.
      - If the request is Unauthorized (401), the URL is still considered valid.

    Args:
        url (str): The full URL to validate and check.

    Returns:
        str: The validated URL if it exists.

    Raises:
        ValueError: If the URL structure is invalid.
        Exception: If the URL returns a 404 (Not Found) status.
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

    # Perform an HTTP GET request to verify the URL exists
    try:
        response = requests.get(url)
        
        # Allow 403 (Forbidden)    as a valid response
        # Allow 401 (Unauthorized) as a valid response
        if response.status_code == 404:
            error_msg = f"URL not found: {url} (HTTP 404)"
            logger.error(error_msg)
            raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        logger.error("Error occurred while requesting URL: %s", url)
        raise Exception(f"Error occurred while requesting URL: {url}") from e

    logger.info("URL validated successfully: %s (%s)", url, response.status_code)
    return url

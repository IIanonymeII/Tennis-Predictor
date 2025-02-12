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
    
def build_full_links(base_url: str, add_slug: str, after_slug: str = "") -> str:
    """
    Build a full URL by concatenating the base URL, an additional slug, and an optional after-slug.

    This function verifies:
      - The base_url begins with 'https://' and ends with '/'.
      - If after_slug is provided, then either add_slug ends with '/' or after_slug starts with '/'.

    After constructing the URL, it performs an HTTP GET request to ensure the URL exists.

    Args:
        base_url (str): The base URL (must start with 'https://' and end with '/').
        add_slug (str): The slug to add after the base URL.
        after_slug (str, optional): An optional slug to append after add_slug. Defaults to "".

    Returns:
        str: The fully constructed URL if it exists.

    Raises:
        ValueError: If the base URL or slug structure is invalid.
        Exception: If an HTTP 404 status code is returned, indicating the URL does not exist.
    """
    logger.debug("Building full URL using base URL: %s", base_url)

    # Validate that base_url begins with 'https://' and ends with '/'
    if not base_url.startswith("https://"):
        error_msg = f"Invalid base_url '{base_url}': must start with 'https://'"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not base_url.endswith("/"):
        error_msg = f"Invalid base_url '{base_url}': must end with '/'"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # If after_slug is provided, verify the slug structure
    if after_slug and not (add_slug.endswith("/") or after_slug.startswith("/")):
        error_msg = (
            "Invalid URL structure: if after_slug is provided, "
            "add_slug must end with '/' or after_slug must start with '/'"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Construct the new URL
    new_url = base_url + add_slug + after_slug
    logger.debug("Constructed URL: %s", new_url)

    # Perform an HTTP GET request to verify the URL exists
    try:
        response = requests.get(new_url)
    except Exception as e:
        logger.error("Error occurred while requesting URL: %s", new_url)
        raise Exception(f"Error occurred while requesting URL: {new_url}") from e

    if response.status_code == 404:
        error_msg = f"URL not found: {new_url} (HTTP 404)"
        logger.error(error_msg)
        raise Exception(error_msg)

    logger.info("URL built successfully: %s (%s)", new_url, str(response.status_code))
    return new_url

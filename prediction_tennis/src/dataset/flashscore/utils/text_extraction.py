import logging
import re
from typing import Optional

logger = logging.getLogger("[UTIL] [EXTRACT]")


def extract_pattern_from_text(text: str, pattern: str, optional_value: bool = False) -> Optional[str]:
    """
    Extracts a single pattern match from the given text.

    Args:
        text (str): The input text to search within.
        pattern (str): The regex pattern to search for.
        optional_value (bool, optional): If True, returns None when the match is not exactly one.
            Defaults to False.

    Returns:
        Optional[str]: The matched string if exactly one match is found, or None if
        `optional_value` is True and the match is not exactly one.

    Raises:
        ValueError: If the number of matches is not exactly one and `optional_value` is False.
    """
    matches = re.findall(pattern, text)

    if len(matches) == 1:
        logger.debug("Valid result found: %s", matches[0])
        return matches[0]
    elif optional_value:
        return None

    logger.error(
        "Multiple results found: expected exactly 1 result, found %d using pattern '%s' in text: %s",
        len(matches), pattern, text
    )
    raise ValueError(
        f"Expected exactly 1 result, but found {len(matches)} using pattern '{pattern}' in text: {text}"
    )

def extract_odds(odd_str: str) -> tuple:
    """
    Extracts odds from a formatted string.

    Args:
        odd_str (str): The input string containing odds.

    Returns:
        tuple: A tuple containing two odds as strings.

    Raises:
        ValueError: If the input string does not match the expected format.
    """
    # This regex does the following:
    #  - (?P<odd1>\d+(\.\d+)?) captures the first number (integer or decimal) and names it "odd1".
    #  - (?:\[[ud]\](?P<odd2>\d+(\.\d+)?))? is an optional non-capturing group that:
    #       - Matches a '[' followed by either 'u' or 'd' and a ']'
    #       - Then captures the following number (integer or decimal) as "odd2"
    pattern = r'(?P<odd1>\d+(\.\d+)?)(?:\[[ud]\](?P<odd2>\d+(\.\d+)?))?'
    result = re.fullmatch(pattern, odd_str.strip())

    if not result:
        logger.error(f"Invalid format: {odd_str}")
        raise ValueError(f"Invalid format: {odd_str}")

    odd1 = result.group('odd1')
    # If the second odd is not present, default to the first odd.
    odd2 = result.group('odd2') if result.group('odd2') else odd1

    logger.debug(f"Extracted odds: odd1={odd1}, odd2={odd2}")

    return (odd1, odd2)

def extract_year(text: str) -> str:
        """
        Extract a 4-digit year from the given text using a regular expression.
        
        Args:
            text (str): The text containing the year (e.g. "ATP Acapulco 2024").
        
        Returns:
            str: The extracted year.
        
        Raises:
            ValueError: If no 4-digit year is found in the text.
        """
        logger.debug("Extracting year from text: %s", text)
        match = re.search(r"(\d{4})", text)
        if match:
            year = match.group(1)
            logger.info("Year extracted: %s", year)
            return year
        else:
            logger.error("Year not found in tournament text: '%s'", text)
            raise ValueError(f"Year not found in tournament text: '{text}'")

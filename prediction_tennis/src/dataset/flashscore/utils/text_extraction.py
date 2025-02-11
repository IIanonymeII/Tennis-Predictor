import logging
import re

logger = logging.getLogger("[UTIL] [EXTRACT]")


def extract_pattern_in_text(text: str, pattern: str) -> str:
    """
    Extracts a single pattern match from the given text.

    Args:
        text (str): The input text to search within.
        pattern (str): The regex pattern to search for.

    Returns:
        str: The matched string if exactly one match is found.

    Raises:
        ValueError: If the number of matches is not exactly one.
    """
    result = re.findall(pattern, text)

    if len(result) == 1:

        logger.debug("Valid result found: %s", result[0])
        return result[0]
    
    else:
        logger.error(
            "Multiple results found: expected exactly 1 result, found %d using pattern '%s' in text: %s",
            len(result), pattern, text
        )
        raise ValueError(
            f"Expected exactly 1 result, but found {len(result)} using pattern '{pattern}' in text: {text}"
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
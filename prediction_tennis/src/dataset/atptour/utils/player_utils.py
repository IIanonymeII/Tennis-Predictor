import http
from itertools import combinations, permutations
import logging
from typing import Any, Dict, List, Optional, Tuple

from fuzzywuzzy import fuzz, process
from prediction_tennis.src.dataset.atptour.utils.config import NAME_TO_CHANGE, REPLACE_KEYS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
NAME_EXCEPTION = ["bin"]
TIMEOUT = 10


def clean_key(key: str) -> str:
    """
    Clean player key by replacing hyphens with spaces and applying manual overrides.

    Args:
        key (str): The raw player key (e.g. "wolf-jeffrey-john")

    Returns:
        str: A cleaned and human-readable player name (e.g. "jeff wolf")

    Examples:
        >>> clean_key("wolf-jeffrey-john")
        'jeff wolf'
    """
    cleaned = key.replace("-", " ").strip().lower()
    return REPLACE_KEYS.get(cleaned, cleaned)


def extract_names(entries: List[Dict[str, Any]]) -> List[str]:
    """
    Extract full names from data entries.

    Args:
        entries: List of dictionaries containing player data.

    Returns:
        List[str]: List of full names extracted from the entries.

    Examples:
        >>> extract_names([{"FirstName": "John", "LastName": "Doe"}])
        ['john doe']
    """
    return [
        f"{entry.get('FirstName', '')} {entry.get('LastName', '')}".strip()
        .lower()
        .replace("-", " ")
        .replace("'", " ")
        .replace(".", " ")
        for entry in entries
    ]


def find_best_match(target: str, names: List[str]) -> Tuple[str, int]:
    """
    Find the closest name match using fuzzy matching.

    Args:
        target: The target name to compare.
        names: List of candidate names.

    Returns:
        Tuple of (best_match, score). Returns ("", 0) if no match found above threshold.

    Examples:
        >>> find_best_match("John Doe", ["John Doe", "Jane Doe"])
        ('John Doe', 100)
    """
    best_match, score = process.extractOne(target, names, scorer=fuzz.token_sort_ratio)
    return best_match, score


def generate_name_variants(name: str, particular_case: Dict[str, str]) -> List[str]:
    """
    Generate variants of the player name slug for search purposes.

    This function creates different name formats to improve player data lookup,
    including handling special cases defined in particular_case.

    Args:
        name (str): Player name slug like 'machac-tomas'.
        particular_case (Dict[str, str]): Dictionary of special cases for name changes.

    Returns:
        List[str]: List of name variants, e.g. ['machac%20tomas', 'machac', 'tomas'].
    """
    # Apply name changes if defined
    name = particular_case.get(name, name)

    # Split name and filter out exceptions
    parts = name.split("-")
    parts = [part for part in parts if part not in NAME_EXCEPTION]

    # Generate variants - replace hyphens with URL-encoded spaces and add individual parts
    variants = [name.replace("-", "%20")]
    if len(parts) >= 2:
        variants.extend(parts)
    logger.debug(f"Generated variants for '{name}': {variants}")
    return variants


def generate_player_name_variants(player_name: str) -> List[str]:
    """
    Generate name variants for a given player name, including all combinations and permutations.

    Args:
        player_name (str): Original player name.

    Returns:
        List[str]: List of name variants to search for.
    """
    try:
        # Get initial variants from existing function
        base_variants = generate_name_variants(player_name, particular_case=NAME_TO_CHANGE)

        # Use set to avoid duplicates, start with base variants
        all_variants = set(base_variants)

        # Get the original name (after any particular_case transformations)
        processed_name = NAME_TO_CHANGE.get(player_name, player_name)

        # Split by dash and filter out exceptions
        name_parts = processed_name.split("-")
        name_parts = [part for part in name_parts if part not in NAME_EXCEPTION]

        if len(name_parts) > 1:
            # Generate all combinations of 2 or more parts
            for r in range(2, len(name_parts) + 1):
                # Get all combinations of r parts
                for combo in combinations(name_parts, r):
                    # For each combination, generate all permutations
                    for perm in permutations(combo):
                        # Join with URL-encoded space (matching your existing format)
                        variant_encoded = "%20".join(perm)
                        all_variants.add(variant_encoded)

        # Convert to sorted list for consistency
        final_variants = sorted(list(all_variants))

        logger.debug(
            f"Generated {len(final_variants)} variants for '{player_name}': {final_variants}"
        )
        return final_variants

    except Exception as exc:
        logger.error(f"Failed to generate variants for '{player_name}': {exc}")
        return [player_name]


def build_player_url(player_id: str, timeout: int = TIMEOUT) -> Optional[str]:
    """
    Build and validate the ATP player profile URL using http.client.

    Args:
        player_id (str): Unique identifier for the player.
        timeout (int): Timeout in seconds for the connection.

    Returns:
        Optional[str]: Validated player URL, or None if not reachable or status != 200.
    """
    host = "www.atptour.com"
    path = f"/en/-/www/players/hero/{player_id}?v=1"
    url = f"https://{host}{path}"
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout)
        conn.request(
            "HEAD",
            path,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TennisBot/1.0)"},
        )
        response = conn.getresponse()
        status = response.status
        conn.close()
        if status == 200:
            return url
        else:
            logger.warning(f"⚠️ URL exists but returned status code {status}: {url}")
    except Exception as e:
        logger.error(f"❌ Error validating URL for player_id={player_id}: {e}")
    return None

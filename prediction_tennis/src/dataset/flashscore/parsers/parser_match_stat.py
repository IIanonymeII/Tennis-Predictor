"""
FlashScore statistics parser module.

This module provides functionality to parse FlashScore statistics from response text
using a segment-based approach. It handles various prefixes and extracts match
statistics for tennis matches.
"""

import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Global variables for state tracking
stats_dict = {}
current_stat = None
sh_value = None
si_value = None


def handle_match_id(value: str):
    """Handles the match ID."""
    logging.info(f"[MATCH ID] {value}")
    stats_dict["match_id"] = value


def handle_se(value: str):
    """Handles SE (Event) segments like Match/Set markers."""
    logging.info(f"[EVENT] {value}")
    stats_dict[value] = {}


def handle_sf(value: str):
    """Handles SF (Sub-Feature) segments like Service/Return."""
    logging.info(f"[EVENT][PROB] {value}")
    last_key = list(stats_dict.keys())[-1]
    stats_dict[last_key][value] = {}


def handle_sg(value: str):
    """Handles SG (Stat Group) segments and initiates stat tracking."""
    global current_stat, sh_value, si_value
    logging.info(f"[EVENT][PROB] {value}")
    current_stat = value
    sh_value = None
    si_value = None


def extract_percentage(value: str):
    """Extracts just the percentage value before '%' with exception handling."""
    try:
        match = re.search(r"(\d+)%", value)
        return match.group(1) if match else value
    except Exception:
        raise


def handle_sh(value: str):
    """Handles SH (Stat Home) values."""
    global sh_value
    if current_stat is not None:
        sh_value = extract_percentage(value)
        logging.info(f"[EVENT][PROB][1] {sh_value}")


def handle_si(value: str):
    """Handles SI (Stat Away) values and stores completed statistics."""
    global current_stat, sh_value, si_value
    if current_stat is not None and sh_value is not None:
        si_value = extract_percentage(value)
        logging.info(f"[EVENT][PROB][2] {si_value}")

        # Store values in the correct nested dictionary
        last_event = list(stats_dict.keys())[-1]
        last_feature = list(stats_dict[last_event].keys())[-1]
        # {'player_1': '100% (6/6)', 'player_2': '100% (6/6)'}
        # {'0% (0/6)', 'player_2': '0% (0/6)'}
        stats_dict[last_event][last_feature][current_stat] = {
            "player_1": sh_value,
            "player_2": si_value,
        }

        current_stat = None  # Reset after completing statistic


def handle_end():
    """Handles the end marker."""
    return stats_dict


# Prefix Handlers Mapping
prefix_handlers = {
    "SE": handle_se,
    "SF": handle_sf,
    "SG": handle_sg,
    "SH": handle_sh,
    "SI": handle_si,
    "A1": lambda _: handle_end(),
}


def process_segment(segment: str):
    """
    Process a single segment of the response text.

    This function splits the segment by the delimiter and handles it according
    to its prefix.

    Parameters
    ----------
    segment : str
        A single segment from the response text to process

    Raises
    ------
    ValueError
        If an unrecognized prefix is encountered
    Exception
        If there's an error during segment processing
    """
    if "÷" not in segment:
        return  # Skip invalid segments

    prefix, value = segment.split("÷", 1)
    clean_prefix = prefix.replace("~", "")

    if clean_prefix in prefix_handlers:
        handler = prefix_handlers[clean_prefix]
    else:
        raise ValueError(
            f"Unrecognized prefix '{prefix}'. Valid prefixes are: {list(prefix_handlers.keys())}"
        )

    try:
        handler(value)
    except Exception as e:
        raise Exception(f"Error handling segment '{segment}': {e}")


def flashscore_stat_match_parser(response_text: str):
    """
    Parse FlashScore statistics from response text.

    This function processes the entire response text by splitting it into segments
    and processing each segment according to its prefix.

    Parameters
    ----------
    response_text : str
        The complete response text from FlashScore containing match statistics

    Returns
    -------
    dict
        A dictionary containing the parsed match statistics organized by events and features
    """
    global stats_dict
    segments = response_text.split("¬")

    for segment in segments:
        process_segment(segment=segment)

    return stats_dict


if __name__ == "__main__":
    import requests

    id_match = "p6BxXM75"
    url = f"https://2.flashscore.ninja/2/x/feed/df_st_1_{id_match}"
    headers = {"x-fsign": "SW9D1eZo"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        response_text = response.text

        return_dict = flashscore_stat_match_parser(response_text=response_text)
        print(return_dict)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

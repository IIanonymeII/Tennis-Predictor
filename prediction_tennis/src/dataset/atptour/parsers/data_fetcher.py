"""
ATP Tour player data fetcher module.

This module provides functionality to fetch player data from the ATP Tour website
using HTTP connections. It includes functions for fetching player data by URL
and by name, with proper error handling and data parsing.
"""

import http.client
import json
import logging
from typing import Dict, Optional, Union

from prediction_tennis.src.dataset.atptour.parsers.data_parser import extract_player_info


logger = logging.getLogger(__name__)

# Constants
TIMEOUT = 10
HEADERS = {"Accept": "*/*", "User-Agent": "Bot"}


def fetch_player_data(atp_url: str) -> Optional[dict]:
    """
    Fetch JSON data from the ATP Tour site using http.client.

    This function makes an HTTPS request to the ATP Tour website to fetch
    player data from the specified URL and returns the parsed JSON response.

    Parameters
    ----------
    atp_url : str
        The player-specific URL slug to fetch data from

    Returns
    -------
    Optional[dict]
        Parsed JSON data as dictionary, or None on error
    """
    conn = http.client.HTTPSConnection("www.atptour.com")
    headers = {"Accept": "*/*", "User-Agent": "Thunder Client (https://www.thunderclient.com)"}

    try:
        conn.request("GET", atp_url, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            logger.warning(f"Failed to fetch {atp_url}: status {response.status}")
            return None
        data = response.read()
        return json.loads(data)
    except Exception as e:
        logger.error(f"Exception fetching {atp_url}: {e}")
        return None
    finally:
        conn.close()


def fetch_player_by_name(name: str, host: str = "www.atptour.com") -> Optional[Union[Dict, str]]:
    """
    Fetch player data by player name using HTTPS connection.

    This function makes an HTTPS request to fetch player data based on the player name slug.
    It handles JSON parsing and error cases.

    Parameters
    ----------
    name : str
        Player name slug (e.g., 'machac-tomas')
    host : str, optional
        Hostname of the server, by default "www.atptour.com"

    Returns
    -------
    Optional[Union[Dict, str]]
        - Parsed dictionary with player info if successful
        - Raw response text if not JSON
        - None if request fails or returns no data

    Examples
    --------
    >>> fetch_player_by_name("machac-tomas")
    {'LastName': 'Machac', 'FirstName': 'Tomas', 'player_id': '12345'}

    Raises
    ------
    Exception
        If there's an error during the HTTP request
    """
    conn = http.client.HTTPSConnection(host, timeout=TIMEOUT)
    path = f"/en/-/www/players/find/byname/{name}/en"
    try:
        conn.request("GET", path, headers=HEADERS)
        response = conn.getresponse()
        status = response.status
        data_bytes = response.read()
        data_str = data_bytes.decode("utf-8")
        if status != 200:
            logger.error(f"Failed to fetch data for '{name}': HTTP {status}")
            return None
        try:
            json_data = json.loads(data_str)
            # Extract only desired fields
            return extract_player_info(json_data)
        except json.JSONDecodeError:
            logger.warning(f"Response for '{name}' is not JSON. Returning raw text.")
            return data_str
    except Exception as e:
        logger.error(f"Exception during HTTP request for '{name}': {e}")
        return None
    finally:
        conn.close()

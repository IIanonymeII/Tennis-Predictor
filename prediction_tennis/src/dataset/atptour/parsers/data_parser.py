import datetime
import logging
from typing import Dict, List, Optional, Tuple, Union

from prediction_tennis.src.dataset.atptour.models.players import Player


logger = logging.getLogger(__name__)


def extract_player_info(
    data: Union[Dict, List, str],
) -> Union[Dict[str, Optional[str]], List[Dict[str, Optional[str]]]]:
    """
    Extract player information from JSON data.

    This function extracts 'LastName', 'FirstName', and 'PlayerId' from the provided data.
    It handles both single dictionary and list of dictionaries input formats.

    Args:
        data (Union[Dict, List, str]): JSON decoded response which can be a dictionary,
                                     list of dictionaries, or raw string data.

    Returns:
        Union[Dict[str, Optional[str]], List[Dict[str, Optional[str]]]]:
            - Dictionary with extracted fields if input is a dict
            - List of dictionaries with extracted fields if input is a list
            - Empty list if input is neither dict nor list

    Examples:
        >>> extract_player_info({"LastName": "Doe", "FirstName": "John", "PlayerId": "123"})
        {'LastName': 'Doe', 'FirstName': 'John', 'player_id': '123'}
    """
    if isinstance(data, dict):
        # Extract from single dict
        return {
            "LastName": data.get("LastName"),
            "FirstName": data.get("FirstName"),
            "player_id": data.get("PlayerId"),
        }
    elif isinstance(data, list):
        # Extract from each dict in list
        extracted_list = []
        for item in data:
            extracted_list.append(
                {
                    "LastName": item.get("LastName"),
                    "FirstName": item.get("FirstName"),
                    "player_id": item.get("PlayerId"),
                }
            )
        return extracted_list if extracted_list else []
    # If data is not dict or list (probably str), return empty list
    return []


def parse_hand_backhand(data: Dict) -> Tuple[str, str]:
    """
    Parse handedness and backhand style from player data.

    Args:
        data (dict): Nested player data dictionary.

    Returns:
        Tuple[str, str]: (hand, backhand) - e.g. ("Right", "two_handed")
    """
    # Parse playing hand
    hand_raw = data.get("PlayHand", {}).get("Id", "X")
    if hand_raw not in {"R", "L"}:
        hand = "X"
    else:
        hand = "Right" if hand_raw == "R" else "Left"

    # Parse backhand type
    backhand_raw = data.get("BackHand", {}).get("Id", "0")
    if backhand_raw not in {"0", "1", "2"}:
        backhand = "X"
    else:
        backhand = "two_handed" if backhand_raw == "2" else "one_handed"
    return hand, backhand


def parse_player_json(data: dict, player_id: str) -> Optional[Player]:
    """
    Parse ATP player JSON into a Player dataclass.

    Args:
        data (dict): JSON dictionary from ATP Tour site.
        player_id (str): Unique identifier for the player.

    Returns:
        Player or None: Parsed Player instance or None if missing data.
    """
    try:
        first_name = data.get("FirstName", "").strip()
        last_name = data.get("LastName", "").strip()
        name = f"{first_name} {last_name}".strip()
        raw_height = data.get("HeightCm", 0)
        height = int(raw_height) if raw_height is not None else 0
        raw_pro_year = data.get("ProYear", 1900)
        pro_year = int(raw_pro_year) if raw_pro_year is not None else 1900
        birthday_raw = data.get("BirthDate")
        birthday = datetime.datetime.fromisoformat(birthday_raw).date() if birthday_raw else None
        hand, backhand = parse_hand_backhand(data=data)
        return Player(
            id=player_id,
            name=name,
            birthday=birthday,
            height=height,
            turn_pro=pro_year,
            hand=hand,
            backhand=backhand,
        )
    except Exception as e:
        logger.warning(f"Error parsing player data: {e}")
        return None

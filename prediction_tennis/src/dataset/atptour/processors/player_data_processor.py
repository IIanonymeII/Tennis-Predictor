import logging
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.dataset.atptour.models.players import Player
from prediction_tennis.src.dataset.atptour.parsers.data_fetcher import fetch_player_data
from prediction_tennis.src.dataset.atptour.parsers.data_parser import parse_player_json
from prediction_tennis.src.dataset.atptour.utils.config import NAME_DO_NOT_EXISTS
from prediction_tennis.src.dataset.atptour.utils.player_utils import (
    build_player_url,
    clean_key,
    extract_names,
    find_best_match,
)


def extract_unique_players_from_flashscore(flashscore_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Extract unique players from flashscore data.

    Parameters
    ----------
    flashscore_dataframe : pd.DataFrame
        Raw flashscore data.

    Returns
    -------
    pd.DataFrame
        DataFrame with unique players (player_id, player_name).
    """
    logger = logging.getLogger("DataExtractor")

    try:
        # Extract player1 information
        player1_data = flashscore_dataframe[["player1_id", "player1_name"]].rename(
            columns={"player1_id": "player_id", "player1_name": "player_name"}
        )

        # Extract player2 information
        player2_data = flashscore_dataframe[["player2_id", "player2_name"]].rename(
            columns={"player2_id": "player_id", "player2_name": "player_name"}
        )

        # Combine and deduplicate
        unique_players = (
            pd.concat([player1_data, player2_data], axis=0).drop_duplicates().reset_index(drop=True)
        )

        logger.info(f"Extracted {len(unique_players)} unique players from flashscore data")

        return unique_players

    except KeyError as exc:
        logger.error(f"Required columns missing from flashscore data: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Failed to extract player data: {exc}")
        raise


def _process_single_player_match(
    original_player_name: str,
    player_entries: List[Dict[str, Optional[str]]],
    players_dataframe: pd.DataFrame,
    minimum_match_score: float = 92.0,
) -> str:
    """
    Process a single player's data for fuzzy matching.

    Args:
        original_player_name (str): Original player name from source data
        player_entries (List[Dict]): List of ATP player data entries
        players_dataframe (pd.DataFrame): DataFrame to update with URLs
        minimum_match_score (float): Minimum fuzzy match score for acceptance

    Returns:
        str: Processing result - "success", "failed", or "skipped"
    """
    logger = logging.getLogger("PlayerMatcher")

    # Clean the player name for matching
    cleaned_player_name = clean_key(original_player_name)

    # Skip if no entries or player is in exclusion list
    if not player_entries or cleaned_player_name in NAME_DO_NOT_EXISTS:
        logger.debug(f"Skipping player '{cleaned_player_name}' (no data or excluded)")
        return "skipped"

    # Extract names from ATP entries
    atp_player_names = extract_names(player_entries)
    if not atp_player_names:
        logger.debug(f"No valid names extracted for player '{cleaned_player_name}'")
        return "skipped"

    try:
        # Perform fuzzy matching
        best_match_name, match_score = find_best_match(
            target=cleaned_player_name, names=atp_player_names
        )

        if match_score >= minimum_match_score:
            # Extract player information and build URL
            best_match_index = atp_player_names.index(best_match_name)
            matched_player_id = player_entries[best_match_index]["PlayerId"]
            atp_player_url = build_player_url(player_id=matched_player_id)

            # Update DataFrame with ATP URL
            players_dataframe.loc[
                players_dataframe["player_name"] == original_player_name, "url_atptour"
            ] = atp_player_url

            logger.debug(
                f"✅ Matched '{cleaned_player_name}' to '{best_match_name}' (score: {match_score:.1f}, ID: {matched_player_id})"
            )
            return "success"

        else:
            # Log failed match with context
            player_ids = players_dataframe.loc[
                players_dataframe["player_name"] == original_player_name, "player_id"
            ].values

            context_player_id = player_ids[0] if len(player_ids) > 0 else "N/A"

            logger.warning(
                f"❌ Low match score for '{cleaned_player_name}' "
                f"[ID: {context_player_id}] -- best match: '{best_match_name}' "
                f"(score: {match_score:.1f})"
            )
            return "failed"

    except Exception as exc:
        logger.error(f"Fuzzy matching failed for player '{cleaned_player_name}': {exc}")
        return "failed"


def process_players_data_with_matching(
    players_dataframe: pd.DataFrame, fetched_player_data: Dict[str, List[Dict[str, Optional[str]]]]
) -> pd.DataFrame:
    """
    Process player data and update the DataFrame with ATP URLs using fuzzy matching.

    This function performs fuzzy string matching between player names and fetched
    data to determine the best ATP tour URL for each player.

    Args:
        players_dataframe (pd.DataFrame): DataFrame containing player information
            with columns: player_id, player_name
        fetched_player_data (Dict[str, List[Dict]]): Dictionary mapping original
            player names to lists of ATP player data entries

    Returns:
        pd.DataFrame: Updated DataFrame with additional 'url_atptour' column

    Raises:
        KeyError: If required columns are missing from the DataFrame
        ValueError: If input data is malformed
    """
    logger = logging.getLogger("PlayerDataProcessor")

    # Validate input DataFrame
    required_columns = {"player_id", "player_name"}
    if not required_columns.issubset(players_dataframe.columns):
        missing_cols = required_columns - set(players_dataframe.columns)
        raise KeyError(f"Missing required columns: {missing_cols}")

    # Initialize processing metrics
    total_players = len(fetched_player_data)
    successful_matches = 0
    failed_matches = 0
    skipped_players = 0

    # Initialize the new ATP URL column
    players_dataframe["url_atptour"] = None

    logger.info(f"Starting player data processing for {total_players} players")

    for original_player_name in tqdm(
        fetched_player_data.keys(), desc="Processing player matches", unit="players"
    ):
        try:
            match_result = _process_single_player_match(
                original_player_name=original_player_name,
                player_entries=fetched_player_data[original_player_name],
                players_dataframe=players_dataframe,
            )

            if match_result == "success":
                successful_matches += 1
            elif match_result == "failed":
                failed_matches += 1
            else:
                skipped_players += 1

        except Exception as exc:
            logger.error(f"Error processing player '{original_player_name}': {exc}")
            failed_matches += 1

    # Log processing summary
    success_rate = (successful_matches / total_players * 100) if total_players > 0 else 0
    logger.info(
        f"Player processing complete:\n"
        f"  Total players: {total_players}\n"
        f"  Successful matches: {successful_matches} ({success_rate:.1f}%)\n"
        f"  Failed matches: {failed_matches}\n"
        f"  Skipped players: {skipped_players}"
    )

    return players_dataframe


def _fetch_detailed_player_data(atp_url: str, player_name: str) -> Optional[Dict]:
    """
    Fetch detailed player data from ATP URL.

    Args:
        atp_url (str): ATP tour URL for the player
        player_name (str): Player name for logging context

    Returns:
        Optional[Dict]: Player data dictionary or None if fetch failed
    """
    logger = logging.getLogger("DetailedDataFetcher")

    try:
        logger.debug(f"Fetching detailed data for '{player_name}' from: {atp_url}")

        detailed_data = fetch_player_data(atp_url)

        if not detailed_data:
            logger.warning(f"No detailed data returned for player '{player_name}'")
            return None

        logger.debug(f"Successfully fetched detailed data for '{player_name}'")
        return detailed_data

    except Exception as exc:
        logger.error(f"Failed to fetch detailed data for '{player_name}': {exc}")
        return None


def _parse_player_data_to_object(
    raw_player_data: Dict, source_player_id: str, player_name: str
) -> Optional["Player"]:
    """
    Parse raw player data into a Player object.

    Args:
        raw_player_data (Dict): Raw player data from ATP
        source_player_id (str): Original player ID from source data
        player_name (str): Player name for logging context

    Returns:
        Optional[Player]: Parsed Player object or None if parsing failed
    """
    logger = logging.getLogger("PlayerDataParser")

    try:
        logger.debug(f"Parsing player data for '{player_name}'")

        player_object = parse_player_json(data=raw_player_data, player_id=source_player_id)

        if not player_object:
            logger.warning(f"Failed to parse player data for '{player_name}'")
            return None

        logger.debug(f"Successfully parsed player object for '{player_name}'")
        return player_object

    except Exception as exc:
        logger.error(f"Error parsing player data for '{player_name}': {exc}")
        return None


def collect_detailed_player_objects(players_dataframe: pd.DataFrame) -> List[Player]:
    """
    Collect comprehensive player objects by fetching detailed data from ATP URLs.

    This function iterates through players with valid ATP URLs and fetches
    their complete profile data, parsing it into Player objects.

    Args:
        players_dataframe (pd.DataFrame): DataFrame containing player information
            with 'url_atptour', 'player_name', and 'player_id' columns

    Returns:
        List[Player]: List of Player objects with complete ATP tour information

    Raises:
        KeyError: If required columns are missing from the DataFrame
    """
    logger = logging.getLogger("PlayerObjectCollector")

    # Validate required columns
    required_columns = {"url_atptour", "player_name", "player_id"}
    if not required_columns.issubset(players_dataframe.columns):
        missing_cols = required_columns - set(players_dataframe.columns)
        raise KeyError(f"Missing required columns: {missing_cols}")

    # Filter players with valid ATP URLs
    players_with_urls = players_dataframe.dropna(subset=["url_atptour"])
    total_players_to_process = len(players_with_urls)

    if total_players_to_process == 0:
        logger.warning("No players with ATP URLs found for detailed collection")
        return []

    logger.info(f"Starting detailed data collection for {total_players_to_process} players")

    successfully_parsed_players = []
    failed_fetches = 0
    failed_parses = 0

    for player_row in tqdm(
        players_with_urls.itertuples(),
        total=total_players_to_process,
        desc="Collecting detailed player data",
        unit="players",
    ):
        try:
            # Fetch detailed player data from ATP URL
            detailed_player_data = _fetch_detailed_player_data(
                atp_url=player_row.url_atptour, player_name=player_row.player_name
            )

            if not detailed_player_data:
                failed_fetches += 1
                continue

            # Parse the fetched data into a Player object
            player_object = _parse_player_data_to_object(
                raw_player_data=detailed_player_data,
                source_player_id=player_row.player_id,
                player_name=player_row.player_name,
            )

            if player_object:
                successfully_parsed_players.append(player_object)
                logger.debug(f"Successfully parsed player: {player_row.player_name}")
            else:
                failed_parses += 1

        except Exception as exc:
            logger.error(
                f"Failed to process detailed data for player '{player_row.player_name}': {exc}"
            )
            failed_fetches += 1

    # Log collection summary
    success_rate = (
        len(successfully_parsed_players) / total_players_to_process * 100
        if total_players_to_process > 0
        else 0
    )

    logger.info(
        f"Player object collection complete:\n"
        f"  Players processed: {total_players_to_process}\n"
        f"  Successfully parsed: {len(successfully_parsed_players)} ({success_rate:.1f}%)\n"
        f"  Failed fetches: {failed_fetches}\n"
        f"  Failed parses: {failed_parses}"
    )

    return successfully_parsed_players

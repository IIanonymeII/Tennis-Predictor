import logging
from typing import Dict, List, Optional, Set

from tqdm import tqdm

from prediction_tennis.src.dataset.atptour.parsers.data_fetcher import fetch_player_data
from prediction_tennis.src.dataset.atptour.utils.config import NAME_TO_CHANGE
from prediction_tennis.src.dataset.atptour.utils.player_utils import clean_key, generate_player_name_variants


class PlayerDataFetcher:
    """Handles fetching and processing of ATP player data."""
    
    def __init__(self, logger_name: str = "PlayerDataFetcher"):
        """
        Initialize the PlayerDataFetcher.
        
        Args:
            logger_name (str): Name for the logger instance.
        """
        self.logger = logging.getLogger(logger_name)

    def fetch_multiple_players_data(self, player_names: List[str]) -> Dict[str, List[Dict[str, Optional[str]]]]:
        """
        Fetch data for multiple players including their name variants.
        
        This method processes a list of player names, generates variants for each,
        and fetches comprehensive data while avoiding duplicates.
        
        Args:
            player_names (List[str]): List of player name slugs to process.
            
        Returns:
            Dict[str, List[Dict[str, Optional[str]]]]: Mapping from original name 
                to list of player data entries, deduplicated by player_id.
                
        Raises:
            ValueError: If player_names is empty or contains invalid entries.
            ConnectionError: If API requests fail consistently.
        """
        if not player_names:
            raise ValueError("Player names list cannot be empty")
        
        self.logger.info(f"Starting data fetch for {len(player_names)} players")
        
        player_data_results = {}
        failed_fetches = []
        
        for original_player_name in tqdm(player_names, desc="Fetching player data",unit="players"):
            try:
                player_entries = self._process_single_player(original_player_name)
                player_data_results[original_player_name] = player_entries
                
                self.logger.debug(f"Successfully processed '{original_player_name}': found {len(player_entries)} unique entries")
                
            except Exception as exc:
                self.logger.error(f"Failed to process player '{original_player_name}': {exc}")
                failed_fetches.append(original_player_name)
                player_data_results[original_player_name] = []
        
        if failed_fetches:
            self.logger.warning(
                f"Failed to fetch data for {len(failed_fetches)} players: "
                f"{', '.join(failed_fetches[:5])}{'...' if len(failed_fetches) > 5 else ''}")
        
        self.logger.info(f"Completed data fetch: {len(player_data_results)} players processed")
        return player_data_results
    
    def _process_single_player(self,
                               original_player_name: str
                               ) -> List[Dict[str, Optional[str]]]:
        """
        Process a single player by generating variants and fetching data.
        
        Args:
            original_player_name (str): The original player name to process.
            
        Returns:
            List[Dict[str, Optional[str]]]: List of unique player data entries.
        """
        # Clean the player name for matching
        cleaned_player_name = clean_key(original_player_name)
        cleaned_player_name = cleaned_player_name.replace(" ","-")
        name_variants = self._generate_player_name_variants(cleaned_player_name)
        seen_player_ids: Set[Optional[str]] = set()
        unique_player_entries: List[Dict[str, Optional[str]]] = []
        
        self.logger.debug(f"Processing '{original_player_name}' with {len(name_variants)} variants")
        
        for name_variant in name_variants:
            try:
                variant_data = self._fetch_single_variant_data(name_variant)
                
                if variant_data:
                    new_entries = self._deduplicate_player_entries(variant_data, seen_player_ids)
                    unique_player_entries.extend(new_entries)
                    
            except Exception as exc:
                self.logger.warning(f"Failed to fetch data for variant '{name_variant}': {exc}")
                continue
        
        return unique_player_entries
    
    def _generate_player_name_variants(self, player_name: str) -> List[str]:
        """
        Generate name variants for a given player name.
        
        Args:
            player_name (str): Original player name.
            
        Returns:
            List[str]: List of name variants to search for.
        """
        # This would call your existing generate_name_variants function
        # with proper error handling and logging
        try:
            variants = generate_player_name_variants(player_name)
            self.logger.debug(f"Generated {len(variants)} variants for '{player_name}'")
            return variants
            
        except Exception as exc:
            self.logger.error(f"Failed to generate variants for '{player_name}': {exc}")
            return [player_name]  # Fallback to original name
        
    def _fetch_single_variant_data(self, name_variant: str) -> List[Dict[str, Optional[str]]]:
        """
        Fetch data for a single name variant.
        
        Args:
            name_variant (str): Name variant to fetch data for.
            
        Returns:
            List[Dict[str, Optional[str]]]: Raw data from API or empty list.
        """
        self.logger.debug(f"Fetching data for variant: '{name_variant}'")
        
        atp_api_endpoint = f"/en/-/www/players/find/byname/{name_variant}/en"
        
        try:
            raw_data = fetch_player_data(atp_url=atp_api_endpoint)
            
            if not raw_data:
                self.logger.debug(f"No data found for variant: '{name_variant}'")
                return []
            
            self.logger.debug(f"Retrieved {len(raw_data)} entries for variant: '{name_variant}'")
            return raw_data
            
        except Exception as exc:
            self.logger.warning(f"API request failed for variant '{name_variant}': {exc}")
            raise

    def _deduplicate_player_entries(self,
                                    new_data: List[Dict[str, Optional[str]]],
                                    seen_player_ids: Set[Optional[str]]
                                   ) -> List[Dict[str, Optional[str]]]:
        """
        Remove duplicate player entries based on player_id.
        
        Args:
            new_data (List[Dict]): New player data entries to process.
            seen_player_ids (Set[Optional[str]]): Set of already seen player IDs.
            
        Returns:
            List[Dict[str, Optional[str]]]: List of new, unique player entries.
        """
        unique_entries = []
        
        for player_entry in new_data:
            player_id = player_entry.get("PlayerId")
            
            if player_id not in seen_player_ids:
                seen_player_ids.add(player_id)
                unique_entries.append(player_entry)
                self.logger.debug(f"Added new player with ID: {player_id}")
            else:
                self.logger.debug(f"Skipped duplicate player with ID: {player_id}")
        
        return unique_entries

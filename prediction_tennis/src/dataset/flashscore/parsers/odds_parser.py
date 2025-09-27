"""...."""
import json
import logging
from dataclasses import replace
from typing import Any, Dict, List


from prediction_tennis.src.dataset.flashscore.models.matchs import Match
from prediction_tennis.src.dataset.flashscore.models.odds import (
    CorrectScoreOdds,
    HomeAwayOdds,
    OverUnderOdds,
)
from prediction_tennis.src.dataset.flashscore.models.players import Player
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import (
    retrieve_flashscore_data,
)


class FlashscoreOddsParser:
    """
    Parser using a state machine to process Flashscore betting odds data.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("[FLASHSCORE][PARSER][ODDS]")

        self.bookmaker_mapping: Dict[int, str] = {
            160: "Unibet",
            129: "Bwin",
            398: "Netbet",
            141: "Betclic",
            484: "Parions-Sport",
            264: "Winamax",
            905: "Betsson",
        }

        self.url_api: str = ""
        self.current_match: Match
        self.home_away_odds: List[HomeAwayOdds] = []
        self.over_odds: List[OverUnderOdds] = []
        self.under_odds: List[OverUnderOdds] = []
        self.correct_score_odds: List[CorrectScoreOdds] = []

    def initialize_variables(self, match: Match) -> None:
        """
        Initializes internal state and sets the match to be processed.
        """
        self.logger.info("___ INIT ___")

        if not isinstance(match, Match):
            self.logger.error("Provided object is not an instance of the Match class.")
            raise ValueError("Provided object is not an instance of the Match class.")

        self.current_match = replace(match)
        self.url_api = self.current_match.odds_link
        self.logger.info(f"[{self.current_match.match_id}] : {self.url_api}")

    def get_bookmaker_name(self, bookmaker_id: int) -> str:
        """
        Returns the name of the bookmaker given its ID.

        Args:
            bookmaker_id (int): ID of the bookmaker.

        Returns:
            str: Name of the bookmaker.
        """
        if bookmaker_id not in self.bookmaker_mapping:
            self.logger.error(f"Unknown bookmaker ID: {bookmaker_id}")
            raise KeyError(f"Bookmaker ID {bookmaker_id} not found in mapping.")
        return self.bookmaker_mapping[bookmaker_id]

    def process_home_away(self, odd: Dict[str, Any], bet_variant: str) -> None:
        """
        Processes 'HOME_AWAY' odds and appends them to the current match.

        Args:
            odd (Dict[str, Any]): The odd data from Flashscore.
            bet_variant (str): Type of the bet (e.g., 'home_away_full').
        """
        try:
            bookmaker_id = int(odd["bookmakerId"])
        except (ValueError, KeyError) as e:
            self.logger.error(f"Invalid bookmaker ID: {e}")
            return

        bookmaker_name = self.get_bookmaker_name(bookmaker_id)

        try:
            odd_p1_start = odd["odds"][0]["opening"]
            odd_p1_end = odd["odds"][0]["value"]
            odd_p2_start = odd["odds"][1]["opening"]
            odd_p2_end = odd["odds"][1]["value"]
        except (IndexError, KeyError) as e:
            self.logger.error(f"Error parsing odds: {e}")
            return

        self.logger.info(f"[{bet_variant}][{bookmaker_name}] [1]: {odd_p1_start} -> {odd_p1_end}")
        self.logger.info(f"[{bet_variant}][{bookmaker_name}] [2]: {odd_p2_start} -> {odd_p2_end}")

        home_away_odd_player1 = HomeAwayOdds(
            bet_variant=bet_variant,
            bookmaker=bookmaker_name,
            odd_start=odd_p1_start,
            odd_end=odd_p1_end,
        )

        home_away_odd_player2 = HomeAwayOdds(
            bet_variant=bet_variant,
            bookmaker=bookmaker_name,
            odd_start=odd_p2_start,
            odd_end=odd_p2_end,
        )

        self.current_match.append_home_away(
            player_1=home_away_odd_player1,
            player_2=home_away_odd_player2,
        )

    def process_over_under(self, odd: Dict[str, Any], bet_variant: str) -> None:
        """
        Process an OVER/UNDER betting odd and append it to the current match.

        Args:
            odd (Dict[str, Any]): The raw odd data from the API.
            bet_variant (str): The variant of the bet (e.g., "over_under_full_time").

        Raises:
            ValueError: If bookmaker ID is invalid or selection is unknown.
        """
        try:
            bookmaker_id = int(odd["bookmakerId"])
        except (ValueError, KeyError) as e:
            self.logger.error(f"Invalid bookmaker ID: {e}")
            return

        bookmaker_name = self.get_bookmaker_name(bookmaker_id)

        for odd_value in odd.get("odds", []):
            # Extract relevant fields from the nested structure
            threshold_type = odd_value["handicap"]["type"]  # e.g., "Games" or "Sets"
            threshold_value = odd_value["handicap"]["value"]  # e.g., "39.5", "3.5"
            selection = odd_value["selection"]  # "OVER" or "UNDER"
            begin_odd = odd_value["opening"]  # Initial odd
            end_odd = odd_value["value"]  # Final odd

            self.logger.info(
                f"[{bet_variant}][{bookmaker_name}] [{threshold_type} - {threshold_value}] [{selection}]: {begin_odd} -> {end_odd}"
            )

            # Build the odds object
            over_under_odd = OverUnderOdds(
                bet_variant=bet_variant,
                threshold_type=threshold_type,
                threshold_value=threshold_value,
                bookmaker=bookmaker_name,
                odd_start=begin_odd,
                odd_end=end_odd,
            )

            # Append the odd to the correct list based on the selection
            selection_upper = selection.strip().upper()
            if selection_upper == "OVER":
                self.current_match.append_over_under(over=over_under_odd)
            elif selection_upper == "UNDER":
                self.current_match.append_over_under(under=over_under_odd)
            else:
                self.logger.error(f"Unknown selection: {selection}")
                raise ValueError(f"Unknown selection: {selection}")

    def process_correct_score(self, odd: Dict[str, Any], bet_variant: str) -> None:
        """
        Process a CORRECT SCORE betting odd and append it to the current match.

        Args:
            odd (Dict[str, Any]): The raw odd data from the API.
            bet_variant (str): The variant of the bet (e.g., "correct_score_full_time").

        Logs:
            Logs info-level details about the odds and errors for invalid input.
        """
        try:
            bookmaker_id = int(odd["bookmakerId"])
        except (ValueError, KeyError) as e:
            self.logger.error(f"Invalid bookmaker ID: {e}")
            return

        bookmaker_name = self.get_bookmaker_name(bookmaker_id)

        for odd_value in odd.get("odds", []):
            # Extract final and opening odds, and the associated score
            end_odd = odd_value["value"]
            begin_odd = odd_value["opening"]
            score = odd_value["score"]  # Example: "3:1", "2:0"

            # Log extracted score and odds
            self.logger.info(
                f"[{bet_variant}] [{bookmaker_name}] [{score}]: {begin_odd} -> {end_odd}"
            )

            # Create and append a CorrectScoreOdds object to the current match
            correct_score_odd = CorrectScoreOdds(
                score=score, bookmaker=bookmaker_name, odd_start=begin_odd, odd_end=end_odd
            )

            self.current_match.append_correct_score(correct=correct_score_odd)

    def process_data(self, match: Match) -> Match:
        """
        Main function to process match odds from Flashscore.

        Args:
            match (Match): Match object containing odds link.

        Returns:
            Match: The updated Match object with odds data.
        """
        self.initialize_variables(match=match)

        self.logger.info("Retrieving Flashscore data...")
        response_txt = retrieve_flashscore_data(url=self.url_api, return_as_text=True)
        data = json.loads(response_txt)

        odds_list = data.get("data", {}).get("findOddsByEventId", {}).get("odds", [])
        if not odds_list:
            self.logger.warning("No odds found in response.")
            return self.current_match

        for odd in odds_list:
            betting_type = odd.get("bettingType")
            betting_scope = odd.get("bettingScope")

        # if get ["data"]["findOddsByEventId"] error other wize
        # if not "odds" found in data["data"]["findOddsByEventId"]: continue that means no odds found

        for odd in data["data"]["findOddsByEventId"]["odds"]:
            betting_type = odd.get("bettingType")
            betting_scope = odd.get("bettingScope")

            if betting_type == "HOME_AWAY":
                if betting_scope == "FULL_TIME":
                    self.logger.info("[HOME - AWAY][FULL_TIME]")
                    self.process_home_away(odd=odd, bet_variant="full")
                elif betting_scope == "FIRST_SET":
                    self.logger.info("[HOME - AWAY][FIRST_SET]")
                    self.process_home_away(odd=odd, bet_variant="1st_set")
                elif betting_scope == "SECOND_SET":
                    self.logger.info("[HOME - AWAY][SECOND_SET]")
                    self.process_home_away(odd=odd, bet_variant="2st_set")
                else:
                    self.logger.warning("Unknown bet scope: %s", betting_scope)
                    raise NotImplementedError("Unknown bet scope: %s", betting_scope)

            elif betting_type == "OVER_UNDER":
                if betting_scope == "FULL_TIME":
                    self.logger.info("[OVER - UNDER][FULL_TIME]")
                    self.process_over_under(odd=odd, bet_variant="full")
                elif betting_scope == "FIRST_SET":
                    self.logger.info("[OVER - UNDER][FIRST_SET]")
                    self.process_over_under(odd=odd, bet_variant="1st_set")
                elif betting_scope == "SECOND_SET":
                    self.logger.info("[OVER - UNDER][SECOND_SET]")
                    self.process_over_under(odd=odd, bet_variant="2st_set")
                else:
                    self.logger.warning("Unknown bet scope: %s", betting_scope)
                    raise NotImplementedError("Unknown bet scope: %s", betting_scope)

            elif betting_type == "CORRECT_SCORE":
                if betting_scope == "FULL_TIME":
                    self.logger.info("[CORRECT_SCORE][FULL_TIME]")
                    self.process_correct_score(odd=odd, bet_variant="full")
                elif betting_scope == "FIRST_SET":
                    self.logger.info("[CORRECT_SCORE][FIRST_SET]")
                    self.process_correct_score(odd=odd, bet_variant="1st_set")
                elif betting_scope == "SECOND_SET":
                    self.logger.info("[CORRECT_SCORE][SECOND_SET]")
                    self.process_correct_score(odd=odd, bet_variant="2st_set")
                else:
                    self.logger.warning("Unknown bet scope: %s", betting_scope)
                    raise NotImplementedError("Unknown bet scope: %s", betting_scope)

            elif betting_type == "ASIAN_HANDICAP":
                self.logger.info("[ASIAN HANDICAP]")

            elif betting_type == "ODD_OR_EVEN":
                self.logger.info("[ODD_OR_EVEN]")

            else:
                self.logger.warning("Unknown bet type: %s", betting_type)
                raise NotImplementedError(f"Bet type '{betting_type}' not implemented.")

        return self.current_match


if __name__ == "__main__":
    # Set up logging (if not already configured)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s: %(message)s"
    )

    player1 = Player(id="golem", name="golem", nationality="golem", link="golem")
    player2 = replace(player1)
    match_id = "CMAn4D1j"

    data = Match(
        match_id=f"{match_id}",
        odds_link=f"https://global.ds.lsapp.eu/odds/pq_graphql?_hash=oce&eventId={match_id}&projectId=2&geoIpCode=FR&geoIpSubdivisionCode=FRBRE",
        stats_link="golem",
        score_link="golem",
        status_link="golem",
        match_date="golem",
        timestamp="golem",
        round="golem",
        player1=player1,
        player2=player2,
    )

    parser = FlashscoreOddsParser()
    match_processed = parser.process_data(match=data)

    print(" === Match === ")
    print(match_processed.to_dict())


from dataclasses import replace
import logging
from typing import List, Optional, Tuple

from prediction_tennis.src.dataset.flashscore.models.matchs import Match
from prediction_tennis.src.dataset.flashscore.models.players import Player
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import retrieve_flashscore_data
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_pattern_from_text

class FlashscoreMatchScoreProcessor:
    """.... """

    def __init__(self) -> None:
        """Initialize the parser state and set up logging."""
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [MATCH][SCORE]")
        
        # set type value
        self.url_api: str
        self.current_match: Match

    def initialize_variables(self, match: Match) -> None:
        self.logger.info("___ INIT ___")

        # Verify that match is an instance of the Match class
        if not isinstance(match, Match):
            self.logger.error("Provided object is not an instance of the Match class")
            raise ValueError("Provided object is not an instance of the Match class")
        
        # Store the current match and the API URL
        self.current_match: Match = replace(match)
        self.url_api: str = self.current_match.score_link

    def _score_set(self, text: str) -> List[Optional[str]]:
        """
        Extracts set scores for Player 1 and Player 2 from the provided text.
        
        The first three sets for each player are mandatory. The optional sets (fourth and fifth)
        are attempted to be extracted; if not found, they are set to None.
        
        Args:
            text (str): The text containing the score set information.
        
        Returns:
            List[Optional[str]]: A list with scores for Player 1 (first five items) followed by
            scores for Player 2 (next five items). Optional sets may be None.
        """
        self.logger.debug(f"Extracting score sets from text: {text}")

        # Define regex patterns for Player 1 score sets (5 sets; sets 4 and 5 are optional)
        player1_patterns = [
            {"pattern": r"¬BA÷([^¬÷]+)¬(?:BB|DA|~BD)÷" , "optional_value": False}, # Set 1 (optional)
            {"pattern": r"¬~BC÷([^¬÷]+)¬(?:BD|DC|~BF)÷", "optional_value": True},  # Set 2 (optional)
            {"pattern": r"¬~BE÷([^¬÷]+)¬(?:BF|DE|~BH)÷", "optional_value": True},  # Set 3 (optional)
            {"pattern": r"¬~BG÷([^¬÷]+)¬(?:BH|DG|~BJ)÷", "optional_value": True},  # Set 4 (optional)
            {"pattern": r"¬~BI÷([^¬÷]+)¬(?:BJ|DI|~A1)÷", "optional_value": True},  # Set 5 (optional)
        ]

        # Define regex patterns for Player 2 score sets (5 sets; sets 4 and 5 are optional)
        player2_patterns = [
            {"pattern": r"¬BB÷([^¬÷]+)¬(?:RC|DB|~BC|BA|~A1)÷" , "optional_value": False}, # Set 1 (mandatory)
            {"pattern": r"¬BD÷([^¬÷]+)¬(?:RD|DD|~BE|~BC|~A1)÷", "optional_value": True},  # Set 2 (optional)
            {"pattern": r"¬BF÷([^¬÷]+)¬(?:RE|DF|~BG|~BE|~A1)÷", "optional_value": True},  # Set 3 (optional)
            {"pattern": r"¬BH÷([^¬÷]+)¬(?:RF|DH|~BI|~BG|~A1)÷", "optional_value": True},  # Set 4 (optional)
            {"pattern": r"¬BJ÷([^¬÷]+)¬(?:RG|DJ|~BI|~A1)÷"    , "optional_value": True},  # Set 5 (optional)
        ]

        player1_scores: List[Optional[str]] = []
        player2_scores: List[Optional[str]] = []

        # Extract scores for Player 1 using the defined patterns.
        for set_pattern in player1_patterns:
            player1_scores.append(extract_pattern_from_text(text, **set_pattern))

        # Extract scores for Player 2 using the defined patterns.
        for set_pattern in player2_patterns:
            player2_scores.append(extract_pattern_from_text(text, **set_pattern))
        
        self.logger.info(f"'SCORE SET' extract : {player1_scores + player2_scores}")

        # Combine and return both players' scores in a single list.
        return player1_scores + player2_scores

    def _score_break_set(self, text: str) -> List[Optional[str]]:
        player1_patterns = [
            {"pattern": r"¬DA÷([^¬÷]+)¬BB÷", "optional_value": True}, # Set 2 (optional)
            {"pattern": r"¬DC÷([^¬÷]+)¬BD÷", "optional_value": True}, # Set 2 (optional)
            {"pattern": r"¬DE÷([^¬÷]+)¬BF÷", "optional_value": True}, # Set 3 (optional)
            {"pattern": r"¬DG÷([^¬÷]+)¬BH÷", "optional_value": True}, # Set 4 (optional)
            {"pattern": r"¬DI÷([^¬÷]+)¬BJ÷", "optional_value": True}, # Set 5 (optional)
        ]

        player2_patterns = [
            {"pattern": r"¬DB÷([^¬÷]+)¬RC÷", "optional_value": True}, # Set 1 (optional)
            {"pattern": r"¬DD÷([^¬÷]+)¬RD÷", "optional_value": True}, # Set 2 (optional)
            {"pattern": r"¬DF÷([^¬÷]+)¬RE÷", "optional_value": True}, # Set 3 (optional)
            {"pattern": r"¬DH÷([^¬÷]+)¬RF÷", "optional_value": True}, # Set 4 (optional)
            {"pattern": r"¬DJ÷([^¬÷]+)¬RG÷", "optional_value": True}, # Set 5 (optional)
        ]

        player1_scores: List[Optional[str]] = []
        player2_scores: List[Optional[str]] = []

        # Extract scores for Player 1 using the defined patterns.
        for set_pattern in player1_patterns:
            player1_scores.append(extract_pattern_from_text(text, **set_pattern))

        # Extract scores for Player 2 using the defined patterns.
        for set_pattern in player2_patterns:
            player2_scores.append(extract_pattern_from_text(text, **set_pattern))

        self.logger.info(f"'SCORE BREAK SET' extract : {player1_scores + player2_scores}")

        # Combine and return both players' scores in a single list.
        return player1_scores + player2_scores

    def _time_set(self, text: str) -> List[Optional[str]]:
        """
        Extracts set time details from the provided text. This includes the total clock and
        the time pass for each set. The total clock and the time for sets 1 to 3 are mandatory,
        while sets 4 and 5 are optional.

        Args:
            text (str): The text containing the set time information.

        Returns:
            List[Optional[str]]: A list containing the extracted set time details. Mandatory fields
            are guaranteed; optional ones will be None if not found.
        """
        self.logger.debug("Extracting set times from text: %s", text)

        # Define regex patterns for set times as dictionaries with an optional flag.
        time_set_patterns = [
            {"pattern": r"¬~RB÷([^¬÷]+)¬~(?:MIT|PSPH|PSPA|A1)÷", "optional_value": True}, # Total clock         (optional)
            {"pattern": r"¬RC÷([^¬÷]+)¬~(?:BC|RB)÷"            , "optional_value": True}, # Time pass for Set 1 (optional)
            {"pattern": r"¬RD÷([^¬÷]+)¬~(?:BE|RB)÷"            , "optional_value": True}, # Time pass for Set 2 (optional)
            {"pattern": r"¬RE÷([^¬÷]+)¬~(?:BG|RB)÷"            , "optional_value": True}, # Time pass for Set 3 (optional)
            {"pattern": r"¬RF÷([^¬÷]+)¬~(?:BI|RB)÷"            , "optional_value": True}, # Time pass for Set 4 (optional)
            {"pattern": r"¬RG÷([^¬÷]+)¬~RB÷"                   , "optional_value": True}, # Time pass for Set 5 (optional)
        ]

        times_set: List[Optional[str]] = []

        # Iterate over each pattern and extract the corresponding time value.
        for pattern_dict in time_set_patterns:
            times_set.append(extract_pattern_from_text(text, **pattern_dict))

        return times_set

    def process_data(self, match: Match) -> Match:
        """
        Process match data by retrieving scores and durations from the Flashscore API,
        extracting set and tiebreak scores, and updating the match object.

        Depending on the match status:
        - SCHEDULED and WALKOVER: No data retrieval.
        - FINISH and RETIRED: Full data processing is performed.
        
        Args:
            match (Match): The match object to process.

        Returns:
            Match: The updated match object.
        """
        # Initialize variables related to the match.    
        self.initialize_variables(match = match)

        if self.current_match.status != "FINISH":
            # "SCHEDULED", "WALKOVER", "AWARDED", "RETIRED"
            return self.current_match

        self.logger.info("Retrieving Flashscore data...")
        response_text = retrieve_flashscore_data(url=self.url_api, return_as_text=True)

        # Extract set scores and divide them between the two players.
        set_scores: List[Optional[str]] = self._score_set(text=response_text)
        player1_set_scores: List[Optional[str]] = set_scores[0:5]
        player2_set_scores: List[Optional[str]] = set_scores[5:]

        # Extract tiebreak scores for sets.
        set_tiebreak_scores: List[Optional[str]] = self._score_break_set(text=response_text)
        player1_tiebreak_scores: List[Optional[str]] = set_tiebreak_scores[0:5]
        player2_tiebreak_scores: List[Optional[str]] = set_tiebreak_scores[5:]
        
        # Extract global match duration and individual set durations.
        all_times: List[Optional[str]] = self._time_set(text=response_text)
        global_duration: str = all_times[0]  # Global match duration.
        set_durations: List[Optional[str]] = all_times[1:]  # Durations for individual sets.
        
        # Update the match object with the global duration.
        self.current_match.global_duration = global_duration

        # Process and append data for each set (1 to 5).
        for i in range(5):
            set_number: int = i + 1

            # Prepare the score tuple for the current set.
            current_set_scores: Tuple[Optional[str], Optional[str]] = (
                player1_set_scores[i],
                player2_set_scores[i]
            )

            # Prepare the tiebreak score tuple for the current set.
            current_tiebreak_scores: Tuple[Optional[str], Optional[str]] = (
                player1_tiebreak_scores[i],
                player2_tiebreak_scores[i]
            )

            current_set_duration: Optional[str] = set_durations[i]

            # Append the current set's details to the match.
            self.current_match.append_set(
                set_number=set_number,
                score_set=current_set_scores,
                tiebreak_set=current_tiebreak_scores,
                duration=current_set_duration
            )
        
        self.current_match.calcul_score()

        return self.current_match

   
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # FINISH
    id = "Kx3ou23b"
    status = "FINISH"

    # # RETIRED
    # id = "C2238Yq4"
    # status = "RETIRED"

    # # WALKAVER
    # id = "OYu8QUV7"
    # status = "WALKOVER"

    player1 = Player(id          = "golem",
                     name        = "golem",
                     nationality = "golem",
                     link        = "golem")
    player2 = replace(player1)

    data = Match(
        match_id   = f"{id}",
        odds_link  = "golem",
        stats_link = "golem",
        score_link = f"https://2.flashscore.ninja/2/x/feed/df_sur_1_{id}",
        status_link= "golem",
        status     = status,
        winner     = -1,
        match_date = "golem",
        timestamp  = "golem",
        round      = "golem",
        player1    = player1,
        player2    = player2,
        )
    
    parser = FlashscoreMatchScoreProcessor()
    current_match = parser.process_data(match=data)

    print(" === match === ")
    print(current_match)

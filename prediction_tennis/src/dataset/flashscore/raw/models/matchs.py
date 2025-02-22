

from dataclasses import asdict, dataclass, field
import logging
from typing import Dict, List, Optional, Tuple, Union

from prediction_tennis.src.dataset.flashscore.raw.models.odds import CorrectScoreOdds, HomeAwayOdds, OverUnderOdds
from prediction_tennis.src.dataset.flashscore.raw.models.players import Player


logger = logging.getLogger("[DATACLASS] [MATCH]")


@dataclass
class Scores:
    """
    Data class representing the score details for a tennis set.

    Attributes:
        score (Optional[str]): The score value for the set (e.g., "6-4", "7-6").
        tiebreak (Optional[str]): Tiebreak score or details, if applicable.
        duration (Optional[str]): Duration or time information for the set.
    """
    score   : Optional[str] = field(default=None) 
    tiebreak: Optional[str] = field(default=None) 
    duration: Optional[str] = field(default=None)


@dataclass
class Match:
    """
    Data class representing a tennis match.

    Attributes:
        match_id (str): Unique identifier for the match.
        match_date (str): Formatted match date (e.g., "YYYY-MM-DD").
        timestamp (str): Timestamp when the match started.
        round (str): Tournament round (e.g., "Quarterfinal").
        player1 (Player): Player 1 object (assumed defined elsewhere).
        player2 (Player): Player 2 object (assumed defined elsewhere).
        odds_link (str): Link to match odds.
        stats_link (str): Link to match statistics.
        score_link (str): Link to detailed match scores.
        status_link (str): Link to match status details.
        status (str): Match status (default 'X'; possible values: 'X', 'Retired', 'Walkover', 'finish').
        winner (int): Indicator of winner (-1 default, 1 for player1, 2 for player2).
        p1_win_sets (int): Final sets won by player 1.
        p2_win_sets (int): Final sets won by player 2.
        global_duration (str): Overall match duration.
        p1_set1_score (Optional[str]): Inline score for player 1 in set 1.
        p1_set1_tiebreak (Optional[str]): Inline tiebreak details for player 1 in set 1.
        p1_set1_duration (Optional[str]): Inline duration for player 1 in set 1.
        p1_set2 to p1_set5 (Scores): Detailed set scores for player 1.
        p2_set1 to p2_set5 (Scores): Detailed set scores for player 2.
        p1_odd_home_away (List[HomeAwayOdds]): List of home-away odds for player 1.
        p2_odd_home_away (List[HomeAwayOdds]): List of home-away odds for player 2.
    """
    match_id: str
    match_date: str
    timestamp: str
    round: str
    player1: Player  # Player class should be defined elsewhere.
    player2: Player  # Player class should be defined elsewhere.

    odds_link  : str
    stats_link : str
    score_link : str
    status_link: str

    status: str = "X" # 'X' default; possible values: 'Retired', 'Walkover', 'finish'
    winner: int = -1  # (-1) default, 1 for player1, 2 for player2

    p1_win_sets: int = 0
    p2_win_sets: int = 0

    global_duration :str = ""

    p1_set1: Scores = field(default_factory=Scores)
    p1_set2: Scores = field(default_factory=Scores)
    p1_set3: Scores = field(default_factory=Scores)
    p1_set4: Scores = field(default_factory=Scores)
    p1_set5: Scores = field(default_factory=Scores)

    p2_set1: Scores = field(default_factory=Scores)
    p2_set2: Scores = field(default_factory=Scores)
    p2_set3: Scores = field(default_factory=Scores)
    p2_set4: Scores = field(default_factory=Scores)
    p2_set5: Scores = field(default_factory=Scores)

    p1_odd_home_away: List[HomeAwayOdds]     = field(default_factory=list)
    p2_odd_home_away: List[HomeAwayOdds]     = field(default_factory=list)
    over_odd        : List[OverUnderOdds]    = field(default_factory=list)
    under_odd       : List[OverUnderOdds]    = field(default_factory=list)
    correct_odd     : List[CorrectScoreOdds] = field(default_factory=list)

    def append_set(self, 
                   set_number  : int,
                   score_set   : Tuple[str, str],
                   tiebreak_set: Tuple[str, str],
                   duration    : str) -> None:
        
        """
        Append set details for both players.

        This method dynamically assigns a Scores instance to the corresponding set
        attribute for each player based on the provided set number. The Scores instance
        includes the set score, tiebreak details, and the duration of the set.

        Args:
            set_number (int): The set number (allowed values: 1 to 5).
            score_set (Tuple[str, str]): Tuple containing the set scores for player 1 and player 2.
            tiebreak_set (Tuple[str, str]): Tuple containing tiebreak details for player 1 and player 2.
            duration (str): The duration of the set.

        Raises:
            ValueError: If set_number is not between 1 and 5 (inclusive).
        """
        logger.debug("Appending set %d details.", set_number)
       
        if set_number not in range(1, 6):
            logger.error("Invalid set number: %d", set_number)
            raise ValueError("Set number must be 1, 2, 3, 4, or 5.")

        # Dynamically determine attribute names for both players.
        attr_player1 = f"p1_set{set_number}"
        attr_player2 = f"p2_set{set_number}"

        # Unpack the set details for both players.
        p1_score   , p2_score    = score_set
        p1_tiebreak, p2_tiebreak = tiebreak_set

        # Create Scores instances for each player's set.
        player1_scores = Scores(score=p1_score, tiebreak=p1_tiebreak, duration=duration)
        player2_scores = Scores(score=p2_score, tiebreak=p2_tiebreak, duration=duration)

        # Set the set details as attributes of the Match instance.
        setattr(self, attr_player1, player1_scores)
        setattr(self, attr_player2, player2_scores)
        
        logger.info(
            "Set %d appended for both players: Player1 %s, Player2 %s",
            set_number,
            player1_scores,
            player2_scores
        )

    def calcul_score(self) -> None:
        """
        Calculates the number of sets won by each player based on their scores.

        Updates:
            - p1_win_sets: Number of sets won by player 1.
            - p2_win_sets: Number of sets won by player 2.
        """
        self.p1_win_sets = 0
        self.p2_win_sets = 0

        for set_number in range(1, 6):
            set_p1: Optional[str] = getattr(self, f"p1_set{set_number}").score
            set_p2: Optional[str] = getattr(self, f"p2_set{set_number}").score
            
            logger.info("Set %d score: Player1: %s - Player2: %s", set_number, set_p1, set_p2)

            if set_p1 is None or set_p2 is None:
                logger.debug("Skipping set %d due to missing scores.", set_number)
                continue

            try:
                p1_games: int = int(set_p1)
                p2_games: int = int(set_p2)
            except ValueError:
                logger.error("Invalid score format in set %d: %s - %s", set_number, set_p1, set_p2)
                raise ValueError(f"Invalid score format in set {set_number}: {set_p1} - {set_p2}")
            
            if p1_games > p2_games:
                self.p1_win_sets += 1

            elif p2_games > p1_games:
                self.p2_win_sets += 1

            else:
                logger.warning("Unexpected tie score in set %d: %d - %d", set_number, p1_games, p2_games)     
                continue   
        
        logger.info("Final set counts: Player1: %d, Player2: %d", self.p1_win_sets, self.p2_win_sets)

    def append_home_away(self, 
                         player_1: HomeAwayOdds,
                         player_2: HomeAwayOdds) -> None:
        """
        Append a HomeAwayOdds instance for player 1&2 to the odds list.

        Args:
            player_1 (HomeAwayOdds): A HomeAwayOdds instance representing odds for player 1
            player_2 (HomeAwayOdds): A HomeAwayOdds instance representing odds for player 2
        """
        self.p1_odd_home_away.append(player_1)
        logger.debug("Appended home-away odds for player1: %s", player_1)

        self.p2_odd_home_away.append(player_1)
        logger.debug("Appended home-away odds for player2: %s", player_2)

    def append_over_under(self, 
                          over: OverUnderOdds,
                          under: OverUnderOdds) -> None:
        """
        Append a OverUnderOdds instance for over under to the odds list.

        Args:
            over  (OverUnderOdds): A OverUnderOdds instance representing odds for over
            under (OverUnderOdds): A OverUnderOdds instance representing odds for under
        """
        self.over_odd.append(over)
        logger.debug("Appended over-under odds for over: %s", over)

        self.under_odd.append(under)
        logger.debug("Appended over-under odds for under: %s", under)

    def append_correct_score(self, 
                                correct: CorrectScoreOdds) -> None:
        """
        Append a CorrectScoreOdds instance for correctsore to the odds list.

        Args:
            CorrectScoreOdds  (CorrectScoreOdds): A CorrectScoreOdds instance representing odds for orret score
        """
        self.correct_odd.append(correct)
        logger.debug("Appended correct odd: %s", correct)

    def __str__(self) -> str:
        return (f"[{self.match_id} - {self.match_date}][{self.round}] [{self.status}]\n"
                f"    player 1 -> {self.player1} [{self.p1_win_sets}] [{self.p1_set1.score} - {self.p1_set2.score} - {self.p1_set3.score} - {self.p1_set4.score} - {self.p1_set5.score}]\n"
                f"    player 2 -> {self.player2} [{self.p2_win_sets}] [{self.p2_set1.score} - {self.p2_set2.score} - {self.p2_set3.score} - {self.p2_set4.score} - {self.p2_set5.score}]\n")

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the Match instance to a flat dictionary with string keys and values.
        The inline score fields and nested Scores objects are flattened into individual keys.

        Returns:
            Dict[str, str]: A dictionary containing match details.
        """
        result: Dict[str, Union[int, str, None]] = {}
        # =======================================================================================
        # Top-level fields
        result["match_id"]   = self.match_id
        result["match_date"] = self.match_date
        result["timestamp"]  = self.timestamp
        result["round"]      = self.round
        
        # =======================================================================================
        # Player 
        result["player1_name"]        = self.player1.name
        result["player2_name"]        = self.player2.name
        result["player1_id"]          = self.player1.id
        result["player2_id"]          = self.player2.id
        result["player1_nationality"] = self.player1.nationality
        result["player2_nationality"] = self.player2.nationality
        result["player1_link"]        = self.player1.link
        result["player2_link"]        = self.player2.link
        
        # =======================================================================================
        result["odds_link"]       = self.odds_link
        result["stats_link"]      = self.stats_link
        result["score_link"]      = self.score_link
        result["status_link"]     = self.status_link
        result["status"]          = self.status
        result["winner"]          = self.winner
        result["p1_win_sets"]     = self.p1_win_sets
        result["p2_win_sets"]     = self.p2_win_sets
        result["global_duration"] = self.global_duration
        
        # =======================================================================================
        # Flatten nested Scores for player 1 (sets 1 to 5)
        for set_index, set_obj in enumerate(
            [self.p1_set1, self.p1_set2, self.p1_set3, self.p1_set4, self.p1_set5], start=1
        ):
            result[f"p1_set{set_index}_score"]    = set_obj.score 
            result[f"p1_set{set_index}_tiebreak"] = set_obj.tiebreak 
            result[f"p1_set{set_index}_duration"] = set_obj.duration 

        # Flatten nested Scores for player 2 (sets 1 to 5)
        for set_index, set_obj in enumerate(
            [self.p2_set1, self.p2_set2, self.p2_set3, self.p2_set4, self.p2_set5], start=1
        ):
            result[f"p2_set{set_index}_score"]    = set_obj.score 
            result[f"p2_set{set_index}_tiebreak"] = set_obj.tiebreak 
            result[f"p2_set{set_index}_duration"] = set_obj.duration
        
        # =======================================================================================
        #                            [ODD] HOME - AWAY
        # Flatten odds for player 1 & 2
        for odds_list, prefix in [(self.p1_odd_home_away, "p1"), (self.p2_odd_home_away, "p2")]:
            for odd in odds_list:
                key_start = f"{prefix}_odd_home_away_{odd.bookmaker}_{odd.bet_variant}_start"
                key_end   = f"{prefix}_odd_home_away_{odd.bookmaker}_{odd.bet_variant}_end"
                result[key_start] = odd.odd_start
                result[key_end]   = odd.odd_end
        
        # =======================================================================================
        #                            [ODD] OVER - UNDER
        # Flatten odds for over and under
        for odds_list, prefix in [(self.over_odd, "over"), (self.under_odd, "under")]:
            for odd in odds_list:
                key_start = f"{prefix}_odd_{odd.bookmaker}_{odd.bet_variant}_{odd.threshold_type}_{odd.threshold_value}_start"
                key_end   = f"{prefix}_odd_{odd.bookmaker}_{odd.bet_variant}_{odd.threshold_type}_{odd.threshold_value}_end"
                result[key_start] = odd.odd_start
                result[key_end]   = odd.odd_end
        
        # =======================================================================================
        #                            [ODD] CORRECT SCORE
        # Flatten odds for correct score
        for odd in self.correct_odd:
            key_start = f"correct_odd_{odd.bookmaker}_{odd.score}_start"
            key_end   = f"correct_odd_{odd.bookmaker}_{odd.score}_end"
            result[key_start] = odd.odd_start
            result[key_end]   = odd.odd_end
        
        # =======================================================================================
        
        logger.debug(f"Match to_dict() output: {result}")
        return result

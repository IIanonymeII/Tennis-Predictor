

from dataclasses import dataclass
import logging

from prediction_tennis.src.dataset.flashscore.models.players import Player


logger = logging.getLogger("[DATACLASS] [MATCH]")

@dataclass
class Match:
    match_id             : str
    formatted_match_date : str
    match_timestamp      : str
    round                : str
    player_1             : Player
    player_2             : Player

    # score_1
    # score_1

    # stat_1
    # stat_2

    # odd_1
    # odd_2

    def __str__(self) -> str:
        return (f"[{self.match_id} - {self.formatted_match_date}][{self.round}] \n"
                f"    player 1 -> {self.player_1}\n"
                f"    player 2 -> {self.player_2}\n")


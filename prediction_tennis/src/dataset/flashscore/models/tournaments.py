"""
Tournament dataclass module.

This module defines tournament dataclasses that represent tennis tournaments
with varying levels of detail, from minimal to comprehensive information
including matches and additional details.
"""

from dataclasses import dataclass, field
import logging
from typing import Dict, List

from prediction_tennis.src.dataset.flashscore.models.matchs import Match


logger = logging.getLogger("[DATACLASS] [TOURNAMENT]")


@dataclass
class TournamentsMinimaliste:
    """
    Minimal representation of a Tournament with essential attributes.

    This class stores the basic tournament information including unique identifier,
    slug, and link to archives.

    Parameters
    ----------
    id : str
        Unique identifier for the tournament
    slug : str
        URL-friendly identifier for the tournament
    link_archives : str
        URL link to the tournament archives
    """

    id: str
    slug: str
    link_archives: str

    def __post_init__(self):
        """Log the creation of a TournamentsMinimaliste instance."""
        logger.debug(f"TournamentsMinimaliste created: ID={self.id}, Slug={self.slug}")

    def __str__(self):
        """
        Return a formatted string representation of the minimal tournament.

        Returns
        -------
        str
            Formatted string showing the tournament slug and link archives
        """
        return f"[{self.slug}] => {self.link_archives}"


@dataclass
class Tournaments(TournamentsMinimaliste):
    """
    Full representation of a Tournament including matches and additional details.

    This class extends TournamentsMinimaliste to include comprehensive tournament
    information such as name, year, links, winner, and a list of matches.

    Parameters
    ----------
    id : str
        Unique identifier for the tournament (inherited)
    slug : str
        URL-friendly identifier for the tournament (inherited)
    link_archives : str
        URL link to the tournament archives (inherited)
    name : str
        Name of the tournament
    year : str
        Year of the tournament
    link : str
        Main URL link to the tournament
    link_results : str
        URL link to the tournament results
    winner_name : str
        Name of the tournament winner
    list_match : List[Match], optional
        List of Match instances associated with the tournament, by default empty list
    """

    name: str
    year: str
    link: str
    link_results: str
    winner_name: str
    list_match: List[Match] = field(default_factory=list)  # Avoid mutable default argument

    def __post_init__(self):
        """Log the creation of a Tournaments instance with tournament details."""
        super().__post_init__()  # Call parent post-init if needed
        logger.info(
            f"Tournaments created: Name={self.name}, Year={self.year}, Matches={len(self.list_match)}"
        )

    def add_match(self, match: Match) -> None:
        """
        Add a Match instance to the tournament's match list.

        Parameters
        ----------
        match : Match
            A Match instance to add to the tournament
        """
        self.list_match.append(match)
        logger.info(f"Added match {match.match_id} to tournament {self.name}")

    def __str__(self):
        """
        Return a formatted string representation of the tournament.

        Returns
        -------
        str
            Formatted string showing the centered tournament name and results link
        """
        return f"[{self.name.center(20)}] => {self.link_results}"

    def to_dict(self) -> List[Dict[str, str]]:
        """
        Convert the Tournament instance to a list of dictionaries.

        Each dictionary represents the tournament-level details merged with one match's details.

        Returns
        -------
        List[Dict[str, str]]
            A list where each element is a dictionary containing:
            "tournament_id", "tournament_slug", "tournament_name", "tournament_year"
            and match details for each match in list_match.
        """
        result_list: List[Dict[str, str]] = []

        # Base tournament info that will be merged with each match's details.
        base_info: Dict[str, str] = {
            "tournament_id": self.id,
            "tournament_slug": self.slug,
            "tournament_name": self.name,
            "tournament_year": self.year,
        }

        if not self.list_match:
            # No matches present, return the base info alone in a list.
            result_list.append(base_info)
        else:
            for match in self.list_match:
                # Each match should provide a flat dictionary of its details.
                match_dict = match.to_dict()
                # Merge tournament info with the match details.
                combined_dict = {**base_info, **match_dict}
                result_list.append(combined_dict)

        logger.info(f"Tournament to_dict() output {len(result_list)} result")
        return result_list

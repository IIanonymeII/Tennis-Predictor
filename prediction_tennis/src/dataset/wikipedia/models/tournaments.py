"""
Tournament dataclass module.

This module defines a Tournaments dataclass that represents tournament information
including name, year, type, prize money, and surface details.
"""

from dataclasses import asdict, dataclass
import logging


logger = logging.getLogger("[DATACLASS] [TOURNAMENT]")


@dataclass
class Tournaments:
    """
    Dataclass representing tournament information.

    This class stores essential tournament details including name, year,
    type, prize money, and playing surface information.

    Parameters
    ----------
    name : str
        Name of the tournament
    year : str
        Year of the tournament
    type : str
        Type or category of the tournament
    money : int
        Prize money amount for the tournament
    surface : str
        Playing surface type (e.g., clay, grass, hard)
    """

    name: str
    year: str
    type: str
    money: int
    surface: str

    def __str__(self) -> str:
        """
        Return a formatted string representation of the tournament.

        Returns
        -------
        str
            Formatted string representation of the tournament
        """
        return (
            f"[{self.year}][{self.name.center(20)}]({self.surface} - {self.type}) => {self.money}"
        )

    def to_dict(self) -> dict:
        """
        Convert the Tournaments instance to a dictionary.

        Uses dataclasses.asdict() to convert the dataclass instance
        into a dictionary representation.

        Returns
        -------
        dict
            Dictionary representation of the Tournaments instance
        """
        return asdict(self)
    
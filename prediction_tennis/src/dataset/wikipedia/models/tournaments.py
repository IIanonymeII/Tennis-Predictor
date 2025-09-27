from dataclasses import asdict, dataclass
import logging


logger = logging.getLogger("[DATACLASS] [TOURNAMENT]")


@dataclass
class Tournaments:
    name: str
    year: str
    type: str
    money: int
    surface: str

    def __str__(self):
        return (
            f"[{self.year}][{self.name.center(20)}]({self.surface} - {self.type}) => {self.money}"
        )

    def to_dict(self):
        return asdict(self)

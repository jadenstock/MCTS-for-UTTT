from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


Move = Tuple[int, int]


@dataclass(frozen=True)
class SearchBudget:
    max_seconds: float
    max_nodes: int


class Bot(ABC):
    bot_id: str

    @abstractmethod
    def choose_move(
        self,
        game,
        budget: SearchBudget,
        metadata: bool = True,
        verbose: bool = False,
    ) -> Optional[Move]:
        """Return (board, cell) or [board, cell, metadata] for compatibility."""


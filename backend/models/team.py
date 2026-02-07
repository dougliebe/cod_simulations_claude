"""Team model for CoD simulation."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Team:
    """Represents a Call of Duty team with their record and Elo rating."""

    name: str
    elo_rating: float
    match_wins: int = 0
    match_losses: int = 0
    map_wins: int = 0
    map_losses: int = 0

    @property
    def match_win_pct(self) -> float:
        """Calculate match win percentage."""
        total = self.match_wins + self.match_losses
        return self.match_wins / total if total > 0 else 0.0

    @property
    def map_win_pct(self) -> float:
        """Calculate map win percentage."""
        total = self.map_wins + self.map_losses
        return self.map_wins / total if total > 0 else 0.0

    @property
    def match_record(self) -> str:
        """Return match record as string (e.g., '7-4')."""
        return f"{self.match_wins}-{self.match_losses}"

    @property
    def map_record(self) -> str:
        """Return map record as string (e.g., '21-15')."""
        return f"{self.map_wins}-{self.map_losses}"

    @property
    def map_differential(self) -> int:
        """Calculate map differential (map wins - map losses)."""
        return self.map_wins - self.map_losses

    def reset_records(self) -> None:
        """Reset win/loss records for simulation."""
        self.match_wins = 0
        self.match_losses = 0
        self.map_wins = 0
        self.map_losses = 0

    def copy(self) -> 'Team':
        """Create a copy of this team for simulation purposes."""
        return Team(
            name=self.name,
            elo_rating=self.elo_rating,
            match_wins=self.match_wins,
            match_losses=self.match_losses,
            map_wins=self.map_wins,
            map_losses=self.map_losses
        )

    def __repr__(self) -> str:
        """String representation of team."""
        return f"Team({self.name}, Elo={self.elo_rating:.0f}, {self.match_record}, Maps: {self.map_record})"

"""Match model for CoD simulation."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Match:
    """Represents a Call of Duty match (best-of-5 series)."""

    id: str
    team1: str
    team2: str
    team1_score: Optional[int] = None
    team2_score: Optional[int] = None
    start_date: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        """Check if match has been played."""
        return self.team1_score is not None and self.team2_score is not None

    @property
    def winner(self) -> Optional[str]:
        """Return the winning team name, or None if not completed."""
        if not self.is_completed:
            return None
        return self.team1 if self.team1_score > self.team2_score else self.team2

    @property
    def loser(self) -> Optional[str]:
        """Return the losing team name, or None if not completed."""
        if not self.is_completed:
            return None
        return self.team2 if self.team1_score > self.team2_score else self.team1

    def is_valid_score(self) -> bool:
        """Validate that scores are valid for best-of-5 (one team has 3, other has 0-2)."""
        if not self.is_completed:
            return True

        score1, score2 = self.team1_score, self.team2_score

        # One team must have exactly 3 wins
        if score1 != 3 and score2 != 3:
            return False

        # Both scores must be in valid range
        if not (0 <= score1 <= 3 and 0 <= score2 <= 3):
            return False

        return True

    def __repr__(self) -> str:
        """String representation of match."""
        if self.is_completed:
            return f"Match({self.team1} {self.team1_score}-{self.team2_score} {self.team2})"
        else:
            return f"Match({self.team1} vs {self.team2} - Not Played)"

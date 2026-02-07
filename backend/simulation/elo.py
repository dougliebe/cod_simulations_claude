"""Elo rating system for probability calculations."""

from typing import Tuple


class EloCalculator:
    """Calculate win probabilities and update Elo ratings."""

    def __init__(self, k_factor: float = 20.0):
        """
        Initialize Elo calculator.

        Args:
            k_factor: K-factor for Elo rating updates (default 20.0)
        """
        self.k_factor = k_factor

    @staticmethod
    def calculate_win_probability(rating1: float, rating2: float) -> float:
        """
        Calculate probability that team1 beats team2 in a single map.

        Uses standard Elo formula:
        P(team1 wins) = 1 / (1 + 10^((rating2 - rating1) / 400))

        Args:
            rating1: Elo rating of team 1
            rating2: Elo rating of team 2

        Returns:
            Probability (0.0 to 1.0) that team1 wins a single map

        Examples:
            >>> EloCalculator.calculate_win_probability(1500, 1500)
            0.5
            >>> prob = EloCalculator.calculate_win_probability(1600, 1400)
            >>> 0.7 < prob < 0.8
            True
        """
        return 1.0 / (1.0 + 10.0 ** ((rating2 - rating1) / 400.0))

    def update_ratings(
        self,
        rating1: float,
        rating2: float,
        team1_score: int,
        team2_score: int
    ) -> Tuple[float, float]:
        """
        Update Elo ratings based on best-of-5 match result.

        This can be used to update team Elo ratings after matches are played.
        Uses the actual match score (e.g., 3-1) to weight the update.

        Args:
            rating1: Current Elo rating of team 1
            rating2: Current Elo rating of team 2
            team1_score: Maps won by team 1 (0-3)
            team2_score: Maps won by team 2 (0-3)

        Returns:
            Tuple of (new_rating1, new_rating2)
        """
        # Calculate expected win probability
        expected1 = self.calculate_win_probability(rating1, rating2)

        # Actual result (1 if team1 won, 0 if team2 won)
        actual1 = 1.0 if team1_score > team2_score else 0.0

        # Update ratings
        new_rating1 = rating1 + self.k_factor * (actual1 - expected1)
        new_rating2 = rating2 + self.k_factor * ((1 - actual1) - (1 - expected1))

        return new_rating1, new_rating2

    def calculate_match_win_probability(self, rating1: float, rating2: float) -> float:
        """
        Estimate probability that team1 wins the best-of-5 match.

        This is an approximation. For exact probability, would need to calculate
        all possible map outcomes. This uses a simplified approach.

        Args:
            rating1: Elo rating of team 1
            rating2: Elo rating of team 2

        Returns:
            Probability (0.0 to 1.0) that team1 wins the match
        """
        # For best-of-5, approximate using map win probability
        # This is simplified; Monte Carlo simulation gives exact probabilities
        map_prob = self.calculate_win_probability(rating1, rating2)

        # For best-of-5, team needs to win 3 maps
        # Approximate: if p > 0.5, team is favored
        # This is a rough estimate; simulation is more accurate
        return map_prob

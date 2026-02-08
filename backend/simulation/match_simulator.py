"""Match simulator for best-of-5 Call of Duty matches."""

import random
from typing import Tuple
from backend.simulation.elo import EloCalculator


class MatchSimulator:
    """Simulates best-of-5 matches using Elo-based probabilities."""

    def __init__(self, elo_calculator: EloCalculator):
        """
        Initialize match simulator.

        Args:
            elo_calculator: EloCalculator instance for probability calculations
        """
        self.elo = elo_calculator

    def simulate_match(self, rating1: float, rating2: float) -> Tuple[int, int]:
        """
        Simulate a best-of-5 match map-by-map.

        Algorithm:
        1. Calculate win probability for team1 on each map using Elo
        2. Simulate maps sequentially until one team reaches 3 wins
        3. Return final score (e.g., 3-1, 3-2)

        Args:
            rating1: Elo rating of team 1
            rating2: Elo rating of team 2

        Returns:
            Tuple of (team1_score, team2_score) where one score is 3

        Examples:
            >>> simulator = MatchSimulator(EloCalculator())
            >>> score1, score2 = simulator.simulate_match(1500, 1500)
            >>> (score1 == 3 or score2 == 3) and 0 <= score1 <= 3 and 0 <= score2 <= 3
            True
        """
        # Calculate win probability once (same for all maps)
        win_prob = self.elo.calculate_win_probability(rating1, rating2)

        team1_score = 0
        team2_score = 0

        # Simulate maps until one team wins 3
        while team1_score < 3 and team2_score < 3:
            # Simulate map result
            if random.random() < win_prob:
                team1_score += 1
            else:
                team2_score += 1

        return team1_score, team2_score

    def simulate_match_with_seed(
        self,
        rating1: float,
        rating2: float,
        seed: int
    ) -> Tuple[int, int]:
        """
        Simulate a match with a specific random seed for reproducibility.

        Useful for testing and debugging.

        Args:
            rating1: Elo rating of team 1
            rating2: Elo rating of team 2
            seed: Random seed for reproducible results

        Returns:
            Tuple of (team1_score, team2_score)
        """
        # Save current random state
        state = random.getstate()

        # Set seed and simulate
        random.seed(seed)
        result = self.simulate_match(rating1, rating2)

        # Restore random state
        random.setstate(state)

        return result

    def calculate_expected_score(self, rating1: float, rating2: float) -> Tuple[float, float]:
        """
        Calculate expected score for a best-of-5 match.

        This is the theoretical expected value, not a simulation.

        Args:
            rating1: Elo rating of team 1
            rating2: Elo rating of team 2

        Returns:
            Tuple of (expected_team1_maps, expected_team2_maps)
        """
        map_prob1 = self.elo.calculate_win_probability(rating1, rating2)

        # In a best-of-5, average number of maps played is ~4.2
        # This is a simplified approximation
        avg_maps = 4.2
        expected1 = map_prob1 * avg_maps
        expected2 = (1 - map_prob1) * avg_maps

        return expected1, expected2

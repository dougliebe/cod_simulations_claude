"""Tests for match simulator."""

import pytest
from backend.simulation.elo import EloCalculator
from backend.simulation.match_simulator import MatchSimulator


class TestMatchSimulator:
    """Test cases for MatchSimulator class."""

    @pytest.fixture
    def simulator(self):
        """Create a MatchSimulator instance for testing."""
        return MatchSimulator(EloCalculator())

    def test_match_score_is_valid_best_of_5(self, simulator):
        """Match scores should be valid best-of-5 results."""
        for _ in range(100):
            score1, score2 = simulator.simulate_match(1500, 1500)

            # One team must have exactly 3 wins
            assert score1 == 3 or score2 == 3

            # Both scores in valid range
            assert 0 <= score1 <= 3
            assert 0 <= score2 <= 3

            # Can't both have 3 (impossible in best-of-5)
            assert not (score1 == 3 and score2 == 3)

    def test_higher_elo_wins_more_often(self, simulator):
        """Team with higher Elo should win more frequently."""
        wins = 0
        num_simulations = 1000

        for _ in range(num_simulations):
            score1, score2 = simulator.simulate_match(1700, 1300)
            if score1 == 3:
                wins += 1

        win_rate = wins / num_simulations

        # With 400 point advantage, should win ~90% of matches
        assert win_rate > 0.80  # Allow some variance

    def test_equal_ratings_approximately_50_50(self, simulator):
        """Equal Elo ratings should result in ~50% win rate."""
        wins = 0
        num_simulations = 1000

        for _ in range(num_simulations):
            score1, score2 = simulator.simulate_match(1500, 1500)
            if score1 == 3:
                wins += 1

        win_rate = wins / num_simulations

        # Should be close to 50%
        assert 0.45 < win_rate < 0.55

    def test_possible_score_outcomes(self, simulator):
        """All valid best-of-5 scores should be possible."""
        possible_scores = {
            (3, 0), (3, 1), (3, 2),
            (0, 3), (1, 3), (2, 3)
        }
        observed_scores = set()

        # Run many simulations to observe all outcomes
        for _ in range(500):
            score = simulator.simulate_match(1500, 1500)
            observed_scores.add(score)

        # Should see most or all possible scores
        assert len(observed_scores) >= 4  # At least 4 different outcomes

    def test_simulate_match_with_seed_is_reproducible(self, simulator):
        """Simulations with same seed should produce same results."""
        score1 = simulator.simulate_match_with_seed(1600, 1400, seed=42)
        score2 = simulator.simulate_match_with_seed(1600, 1400, seed=42)

        assert score1 == score2

    def test_simulate_match_with_different_seeds(self, simulator):
        """Different seeds should produce different results (usually)."""
        results = set()

        for seed in range(10):
            score = simulator.simulate_match_with_seed(1500, 1500, seed=seed)
            results.add(score)

        # Should get at least a few different results
        assert len(results) >= 2

    def test_expected_score_returns_valid_values(self, simulator):
        """Expected score should return valid map counts."""
        exp1, exp2 = simulator.calculate_expected_score(1600, 1400)

        # Both should be positive
        assert exp1 > 0
        assert exp2 > 0

        # Higher rated team should have higher expected score
        assert exp1 > exp2

    def test_expected_score_equal_ratings(self, simulator):
        """Equal ratings should give equal expected scores."""
        exp1, exp2 = simulator.calculate_expected_score(1500, 1500)

        # Should be approximately equal
        assert abs(exp1 - exp2) < 0.1

    def test_sweeps_are_less_common_than_close_matches(self, simulator):
        """3-0 sweeps should be less common than closer matches for equal teams."""
        sweeps = 0
        close_matches = 0
        num_simulations = 1000

        for _ in range(num_simulations):
            score1, score2 = simulator.simulate_match(1500, 1500)

            if score1 == 3 and score2 == 0:
                sweeps += 1
            elif score2 == 3 and score1 == 0:
                sweeps += 1
            elif score1 == 3 and score2 == 2:
                close_matches += 1
            elif score2 == 3 and score1 == 2:
                close_matches += 1

        # For equal teams, close matches should be more common than sweeps
        assert close_matches > sweeps

    def test_large_rating_difference_produces_more_sweeps(self, simulator):
        """Large rating differences should produce more 3-0/3-1 results."""
        dominant_wins = 0  # 3-0 or 3-1
        num_simulations = 1000

        for _ in range(num_simulations):
            score1, score2 = simulator.simulate_match(1800, 1200)

            if score1 == 3 and score2 <= 1:
                dominant_wins += 1

        # Should have many dominant wins
        assert dominant_wins > 600  # At least 60%

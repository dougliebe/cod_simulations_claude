"""Tests for Elo calculator."""

import pytest
from backend.simulation.elo import EloCalculator


class TestEloCalculator:
    """Test cases for EloCalculator class."""

    def test_equal_ratings_50_percent_probability(self):
        """Equal Elo ratings should give 50% win probability."""
        prob = EloCalculator.calculate_win_probability(1500, 1500)
        assert prob == 0.5

    def test_higher_rating_higher_probability(self):
        """Higher Elo should give >50% win probability."""
        prob = EloCalculator.calculate_win_probability(1600, 1400)
        assert 0.5 < prob < 1.0

    def test_lower_rating_lower_probability(self):
        """Lower Elo should give <50% win probability."""
        prob = EloCalculator.calculate_win_probability(1400, 1600)
        assert 0.0 < prob < 0.5

    def test_large_rating_difference(self):
        """Large Elo difference should give strong probability."""
        # 400 point difference should give ~90% win probability
        prob = EloCalculator.calculate_win_probability(1800, 1400)
        assert 0.85 < prob < 0.95

    def test_probability_formula_accuracy(self):
        """Test specific probability calculations."""
        # 200 point advantage ≈ 76% win probability
        prob = EloCalculator.calculate_win_probability(1700, 1500)
        assert abs(prob - 0.76) < 0.01

    def test_symmetric_probabilities(self):
        """P(A beats B) + P(B beats A) should equal 1."""
        prob_a_wins = EloCalculator.calculate_win_probability(1600, 1450)
        prob_b_wins = EloCalculator.calculate_win_probability(1450, 1600)
        assert abs((prob_a_wins + prob_b_wins) - 1.0) < 0.001

    def test_extreme_rating_difference(self):
        """Extreme rating differences should approach 0 or 1."""
        # 1000 point difference should be nearly certain
        prob = EloCalculator.calculate_win_probability(2000, 1000)
        assert prob > 0.99

        prob_reverse = EloCalculator.calculate_win_probability(1000, 2000)
        assert prob_reverse < 0.01

    def test_update_ratings_winner_gains_points(self):
        """Winner should gain Elo points, loser should lose them."""
        calc = EloCalculator(k_factor=20.0)

        # Team 1 wins 3-1
        new_rating1, new_rating2 = calc.update_ratings(1500, 1500, 3, 1)

        assert new_rating1 > 1500  # Winner gains
        assert new_rating2 < 1500  # Loser loses

    def test_update_ratings_conservation(self):
        """Total Elo points should be conserved."""
        calc = EloCalculator(k_factor=20.0)

        rating1, rating2 = 1600, 1400
        new_rating1, new_rating2 = calc.update_ratings(rating1, rating2, 3, 2)

        # Total should be conserved
        assert abs((rating1 + rating2) - (new_rating1 + new_rating2)) < 0.01

    def test_update_ratings_upset_bonus(self):
        """Underdog should gain more points for upset win."""
        calc = EloCalculator(k_factor=20.0)

        # Underdog wins
        new_rating1, new_rating2 = calc.update_ratings(1400, 1600, 3, 1)
        underdog_gain = new_rating1 - 1400

        # Favorite wins
        new_rating3, new_rating4 = calc.update_ratings(1600, 1400, 3, 1)
        favorite_gain = new_rating3 - 1600

        # Underdog should gain more than favorite
        assert underdog_gain > favorite_gain

    def test_k_factor_affects_rating_change(self):
        """Higher K-factor should result in larger rating changes."""
        calc_low = EloCalculator(k_factor=10.0)
        calc_high = EloCalculator(k_factor=30.0)

        new_low_1, _ = calc_low.update_ratings(1500, 1500, 3, 1)
        new_high_1, _ = calc_high.update_ratings(1500, 1500, 3, 1)

        low_change = abs(new_low_1 - 1500)
        high_change = abs(new_high_1 - 1500)

        assert high_change > low_change

    def test_match_win_probability_returns_valid_range(self):
        """Match win probability should be between 0 and 1."""
        calc = EloCalculator()

        prob = calc.calculate_match_win_probability(1600, 1400)
        assert 0.0 <= prob <= 1.0

    def test_match_win_probability_equal_ratings(self):
        """Equal ratings should give approximately 50% match win probability."""
        calc = EloCalculator()

        prob = calc.calculate_match_win_probability(1500, 1500)
        assert abs(prob - 0.5) < 0.1  # Allow some approximation error

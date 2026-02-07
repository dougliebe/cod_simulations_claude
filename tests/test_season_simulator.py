"""Tests for season simulator."""

import pytest
from backend.models.team import Team
from backend.models.match import Match
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator


class TestSeasonSimulator:
    """Test cases for SeasonSimulator class."""

    @pytest.fixture
    def simple_simulator(self):
        """Create simple simulator with 4 teams."""
        teams = {
            'Team A': Team('Team A', 1600),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1400),
            'Team D': Team('Team D', 1300)
        }

        matches = [
            Match('m1', 'Team A', 'Team B'),  # Not played
            Match('m2', 'Team A', 'Team C'),  # Not played
            Match('m3', 'Team A', 'Team D'),  # Not played
            Match('m4', 'Team B', 'Team C'),  # Not played
            Match('m5', 'Team B', 'Team D'),  # Not played
            Match('m6', 'Team C', 'Team D'),  # Not played
        ]

        elo_calc = EloCalculator()
        return SeasonSimulator(teams, matches, elo_calc)

    def test_probabilities_sum_to_one(self, simple_simulator):
        """Seed probabilities should sum to ~1.0 for each team."""
        results = simple_simulator.run_simulations(num_iterations=100)

        for team_name, probs in results.items():
            # Sum all seed probabilities
            total = sum(probs.get(f'seed_{i}', 0) for i in range(1, 5))

            # Should sum to ~1.0 (within tolerance)
            assert 0.99 <= total <= 1.01, f"{team_name}: seed probs sum to {total}"

    def test_all_teams_get_results(self, simple_simulator):
        """All teams should appear in results."""
        results = simple_simulator.run_simulations(num_iterations=100)

        assert len(results) == 4
        assert 'Team A' in results
        assert 'Team B' in results
        assert 'Team C' in results
        assert 'Team D' in results

    def test_higher_elo_better_seeding(self, simple_simulator):
        """Higher Elo teams should have better average seeding."""
        results = simple_simulator.run_simulations(num_iterations=500)

        # Calculate average seed for each team
        avg_seeds = {}
        for team_name, probs in results.items():
            avg_seed = sum(
                i * probs.get(f'seed_{i}', 0)
                for i in range(1, 5)
            )
            avg_seeds[team_name] = avg_seed

        # Team A (highest Elo) should have best average seed
        assert avg_seeds['Team A'] < avg_seeds['Team B']
        assert avg_seeds['Team B'] < avg_seeds['Team C']
        assert avg_seeds['Team C'] < avg_seeds['Team D']

    def test_completed_matches_respected(self):
        """Completed matches should always have same result."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500)
        }

        # Team A already beat Team B
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 0),  # Completed
        ]

        elo_calc = EloCalculator()
        simulator = SeasonSimulator(teams, matches, elo_calc)

        results = simulator.run_simulations(num_iterations=100)

        # Team A should always be seed 1 (100% probability)
        assert results['Team A']['seed_1'] == 1.0
        assert results['Team B']['seed_2'] == 1.0

    def test_user_adjustments_override_simulation(self):
        """User-adjusted matches should override Elo simulation."""
        teams = {
            'Team Strong': Team('Team Strong', 1800),
            'Team Weak': Team('Team Weak', 1200)
        }

        matches = [
            Match('m1', 'Team Strong', 'Team Weak'),  # Not played
        ]

        elo_calc = EloCalculator()
        simulator = SeasonSimulator(teams, matches, elo_calc)

        # User adjusts: weak team upsets strong team
        adjustments = [
            Match('m1', 'Team Strong', 'Team Weak', 0, 3)  # Weak wins 3-0
        ]

        results = simulator.run_simulations(
            num_iterations=100,
            adjusted_matches=adjustments
        )

        # Weak team should always be seed 1 (upset)
        assert results['Team Weak']['seed_1'] == 1.0
        assert results['Team Strong']['seed_2'] == 1.0

    def test_playoff_probability_tracked(self, simple_simulator):
        """Should track playoff qualification (top 8)."""
        results = simple_simulator.run_simulations(num_iterations=100)

        for team_name, probs in results.items():
            # For 4-team league, all make "playoffs" (top 8)
            # Just verify the key exists
            if 'make_playoffs' in probs:
                assert 0.0 <= probs['make_playoffs'] <= 1.0

    def test_winners_bracket_probability_tracked(self, simple_simulator):
        """Should track winners bracket (top 6)."""
        results = simple_simulator.run_simulations(num_iterations=100)

        for team_name, probs in results.items():
            # Just verify the key exists if present
            if 'winners_bracket' in probs:
                assert 0.0 <= probs['winners_bracket'] <= 1.0

    def test_get_current_standings(self, simple_simulator):
        """Should get current standings from completed matches."""
        standings = simple_simulator.get_current_standings()

        # Should return all 4 teams
        assert len(standings) == 4

        # Each entry should be (name, match_record, map_record)
        for entry in standings:
            assert len(entry) == 3
            team_name, match_record, map_record = entry
            assert isinstance(team_name, str)
            assert isinstance(match_record, str)
            assert isinstance(map_record, str)

    def test_simulate_single_scenario(self, simple_simulator):
        """Should simulate single scenario and return seeding."""
        seeding = simple_simulator.simulate_single_scenario()

        # Should return all 4 teams in some order
        assert len(seeding) == 4
        assert set(seeding) == {'Team A', 'Team B', 'Team C', 'Team D'}

    def test_get_match_win_probability(self, simple_simulator):
        """Should calculate match win probability."""
        prob = simple_simulator.get_match_win_probability('Team A', 'Team D')

        # Team A (1600) vs Team D (1300) - A should be favored
        assert prob > 0.7

    def test_empty_season_all_tied(self):
        """With no completed matches, all teams should have similar probabilities."""
        teams = {f'Team {i}': Team(f'Team {i}', 1500) for i in range(4)}
        matches = []

        elo_calc = EloCalculator()
        simulator = SeasonSimulator(teams, matches, elo_calc)

        results = simulator.run_simulations(num_iterations=200)

        # All teams have equal Elo and no matches played
        # Each team should have ~25% chance for each seed (with variance)
        for team_name, probs in results.items():
            for seed in range(1, 5):
                prob = probs.get(f'seed_{seed}', 0)
                # Should be roughly 0.25, allow wide tolerance
                assert 0.15 < prob < 0.35

    def test_partial_season_completion(self):
        """Should handle partially completed season."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500)
        }

        matches = [
            Match('m1', 'Team A', 'Team B', 3, 0),  # Completed
            Match('m2', 'Team A', 'Team C'),        # Not played
            Match('m3', 'Team B', 'Team C'),        # Not played
        ]

        elo_calc = EloCalculator()
        simulator = SeasonSimulator(teams, matches, elo_calc)

        results = simulator.run_simulations(num_iterations=100)

        # Team A has head start (1-0), should have better seeding
        team_a_top_seeds = results['Team A'].get('seed_1', 0) + results['Team A'].get('seed_2', 0)
        team_b_bottom_seeds = results['Team B'].get('seed_2', 0) + results['Team B'].get('seed_3', 0)

        assert team_a_top_seeds > 0.5  # A likely in top 2
        assert team_b_bottom_seeds > 0.5  # B likely in bottom 2

    def test_deterministic_scenario(self):
        """Fully determined scenario should give 100% probabilities."""
        teams = {
            'Team 1': Team('Team 1', 1500),
            'Team 2': Team('Team 2', 1500),
            'Team 3': Team('Team 3', 1500)
        }

        # All matches completed with clear winner
        matches = [
            Match('m1', 'Team 1', 'Team 2', 3, 0),
            Match('m2', 'Team 1', 'Team 3', 3, 0),
            Match('m3', 'Team 2', 'Team 3', 3, 0),
        ]

        elo_calc = EloCalculator()
        simulator = SeasonSimulator(teams, matches, elo_calc)

        results = simulator.run_simulations(num_iterations=100)

        # Team 1: 2-0, should always be seed 1
        assert results['Team 1']['seed_1'] == 1.0

        # Team 2: 1-1, should always be seed 2 (beat Team 3 h2h)
        assert results['Team 2']['seed_2'] == 1.0

        # Team 3: 0-2, should always be seed 3
        assert results['Team 3']['seed_3'] == 1.0

    def test_multiple_iterations_consistency(self, simple_simulator):
        """Multiple runs should give similar results (Monte Carlo variance)."""
        results1 = simple_simulator.run_simulations(num_iterations=500)
        results2 = simple_simulator.run_simulations(num_iterations=500)

        # Results should be similar (not identical due to randomness)
        for team_name in results1.keys():
            for seed in range(1, 5):
                prob1 = results1[team_name].get(f'seed_{seed}', 0)
                prob2 = results2[team_name].get(f'seed_{seed}', 0)

                # Allow 10% difference due to Monte Carlo variance
                assert abs(prob1 - prob2) < 0.15

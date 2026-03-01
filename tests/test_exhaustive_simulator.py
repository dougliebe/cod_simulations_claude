"""Tests for exhaustive simulation method."""

import logging
import pytest
from backend.models.team import Team
from backend.models.match import Match
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator, OUTCOMES_PER_MATCH
from backend.simulation.tiebreaker import TiebreakerResolver
from backend.models.standings import SeasonStandings
from config import Config


class TestExhaustiveSimulator:
    """Test cases for exhaustive simulation."""

    @pytest.fixture
    def simulator_one_remaining(self):
        """4 teams, 5 matches completed, 1 remaining (6 scenarios)."""
        teams = {
            'Team A': Team('Team A', 1600),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1400),
            'Team D': Team('Team D', 1300)
        }
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 0),
            Match('m2', 'Team A', 'Team C', 3, 1),
            Match('m3', 'Team A', 'Team D', 3, 2),
            Match('m4', 'Team B', 'Team C', 0, 3),
            Match('m5', 'Team B', 'Team D', 1, 3),
            Match('m6', 'Team C', 'Team D', None, None),  # Only unplayed
        ]
        return SeasonSimulator(teams, matches, EloCalculator())

    @pytest.fixture
    def simulator_two_remaining(self):
        """4 teams, 4 matches completed, 2 remaining (36 scenarios)."""
        teams = {
            'Team A': Team('Team A', 1600),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1400),
            'Team D': Team('Team D', 1300)
        }
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 0),
            Match('m2', 'Team A', 'Team C', 3, 1),
            Match('m3', 'Team A', 'Team D', 3, 2),
            Match('m4', 'Team B', 'Team C', 0, 3),
            Match('m5', 'Team B', 'Team D', None, None),
            Match('m6', 'Team C', 'Team D', None, None),
        ]
        return SeasonSimulator(teams, matches, EloCalculator())

    def test_outcomes_per_match_valid(self):
        """OUTCOMES_PER_MATCH has 6 valid best-of-5 scores."""
        assert len(OUTCOMES_PER_MATCH) == 6
        for s1, s2 in OUTCOMES_PER_MATCH:
            assert (s1 == 3 or s2 == 3) and 0 <= s1 <= 3 and 0 <= s2 <= 3

    def test_exhaustive_one_match_structure(self, simulator_one_remaining):
        """Exhaustive with 1 remaining match yields expected structure."""
        result = simulator_one_remaining.run_exhaustive_simulations()
        results = result["probabilities"]

        assert len(results) == 4
        for team_name, probs in results.items():
            # Each team has at least one seed (the one they achieved)
            seed_keys = [k for k in probs if k.startswith('seed_')]
            assert len(seed_keys) >= 1
            assert 'make_play_ins' in probs
            assert 'make_bracket' in probs

    def test_exhaustive_probabilities_sum_to_one(self, simulator_one_remaining):
        """Seed probabilities sum to 1.0 per team for 1 remaining match."""
        result = simulator_one_remaining.run_exhaustive_simulations()
        results = result["probabilities"]

        for team_name, probs in results.items():
            total = sum(probs.get(f'seed_{i}', 0) for i in range(1, 5))
            assert abs(total - 1.0) < 0.001, f"{team_name}: {total}"

    def test_exhaustive_total_scenarios(self, simulator_one_remaining, simulator_two_remaining):
        """Exhaustive produces correct total scenario count."""
        r1 = simulator_one_remaining.run_exhaustive_simulations()
        probs1 = r1["probabilities"]
        # Each team's seed_* probs sum to 1, and we have 6 scenarios
        # So each prob is count/6
        for team_name, probs in probs1.items():
            for key, val in probs.items():
                if key.startswith('seed_'):
                    assert val * 6 == int(val * 6), f"Prob should be multiple of 1/6: {val}"

        r2 = simulator_two_remaining.run_exhaustive_simulations()
        probs2 = r2["probabilities"]
        for team_name, probs in probs2.items():
            for key, val in probs.items():
                if key.startswith('seed_'):
                    assert val * 36 == int(round(val * 36)), f"Prob should be multiple of 1/36: {val}"

    def test_exhaustive_too_many_raises(self):
        """Exhaustive raises when scenarios exceed max."""
        teams = {f'Team {i}': Team(f'Team {i}', 1500) for i in range(12)}
        matches = [Match(f'm{i}', f'Team {i % 12}', f'Team {(i + 1) % 12}') for i in range(66)]
        sim = SeasonSimulator(teams, matches, EloCalculator())

        with pytest.raises(ValueError) as exc_info:
            sim.run_exhaustive_simulations(max_scenarios=100)
        assert "Too many scenarios" in str(exc_info.value)

    def test_get_remaining_match_count(self, simulator_one_remaining, simulator_two_remaining):
        """get_remaining_match_count returns correct count."""
        assert simulator_one_remaining.get_remaining_match_count() == 1
        assert simulator_two_remaining.get_remaining_match_count() == 2

    def test_get_remaining_match_count_with_adjustments(self, simulator_two_remaining):
        """get_remaining_match_count respects adjusted matches."""
        adj = [
            Match('m5', 'Team B', 'Team D', 3, 1),
        ]
        assert simulator_two_remaining.get_remaining_match_count(adjusted_matches=adj) == 1


class TestTiebreakerDeterministic:
    """Test tier-7 deterministic behavior and logging."""

    def test_deterministic_tier7_alphabetical(self):
        """Tier 7 with deterministic=True returns alphabetical order."""
        teams = {
            'Team Z': Team('Team Z', 1500),
            'Team A': Team('Team A', 1500),
        }
        # No matches - both 0-0, will tie on all tiers, hit tier 7
        matches = [
            Match('m1', 'Team A', 'Team Z', None, None),
        ]
        for t in teams.values():
            t.reset_records()
        standings = SeasonStandings(teams, matches)
        # Don't update from matches - leave both at 0-0
        resolver = TiebreakerResolver(standings, deterministic=True)
        result = resolver.resolve_tie(['Team Z', 'Team A'])
        assert result == ['Team A', 'Team Z']

    def test_deterministic_tier7_logging(self, caplog):
        """Tier 7 in deterministic mode logs the scenario."""
        caplog.set_level(logging.INFO)
        teams = {
            'Team B': Team('Team B', 1500),
            'Team A': Team('Team A', 1500),
        }
        matches = [Match('m1', 'Team A', 'Team B', None, None)]
        for t in teams.values():
            t.reset_records()
        standings = SeasonStandings(teams, matches)
        resolver = TiebreakerResolver(standings, deterministic=True)
        resolver.resolve_tie(['Team B', 'Team A'])

        assert any(
            'Tier 7 tiebreaker' in rec.message and 'alphabetically' in rec.message and 'deterministic' in rec.message
            for rec in caplog.records
        )

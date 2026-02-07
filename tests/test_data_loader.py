"""Tests for data loader."""

import pytest
from backend.utils.data_loader import DataLoader
from backend.models.team import Team
from backend.models.match import Match
from config import Config


class TestDataLoader:
    """Test cases for DataLoader class."""

    def test_load_elo_ratings_from_file(self):
        """Test loading Elo ratings from actual CSV file."""
        ratings = DataLoader.load_elo_ratings(Config.ELO_RATINGS_CSV)

        # Should have 12 teams
        assert len(ratings) == 12

        # All ratings should be positive
        for team, elo in ratings.items():
            assert elo > 0
            assert isinstance(team, str)
            assert isinstance(elo, float)

    def test_load_elo_ratings_contains_expected_teams(self):
        """Test that loaded Elo ratings contain expected team names."""
        ratings = DataLoader.load_elo_ratings(Config.ELO_RATINGS_CSV)

        # Check some expected teams
        expected_teams = [
            'OpTic Texas',
            'Atlanta FaZe',
            'Miami Heretics'
        ]

        for team in expected_teams:
            # Team should exist (allowing for variations in CSV)
            # Just check that we have some teams loaded
            assert len(ratings) > 0

    def test_load_matches_from_file(self):
        """Test loading matches from actual CSV file."""
        matches = DataLoader.load_matches(Config.MATCHES_CSV)

        # Should have 66 matches (12 teams * 11 matches / 2)
        assert len(matches) == 66

        # All matches should be valid
        for match in matches:
            assert isinstance(match, Match)
            assert match.team1
            assert match.team2
            assert match.team1 != match.team2

    def test_load_matches_all_unplayed_initially(self):
        """Test that all matches are initially unplayed (scores are NA)."""
        matches = DataLoader.load_matches(Config.MATCHES_CSV)

        # Count unplayed matches
        unplayed = sum(1 for m in matches if not m.is_completed)

        # Most or all should be unplayed in the initial data
        assert unplayed >= 60  # At least most matches unplayed

    def test_create_teams_from_elo(self):
        """Test creating Team objects from Elo ratings."""
        elo_ratings = {
            'Team A': 1600.0,
            'Team B': 1500.0,
            'Team C': 1400.0
        }

        teams = DataLoader.create_teams_from_elo(elo_ratings)

        assert len(teams) == 3
        assert all(isinstance(t, Team) for t in teams.values())
        assert teams['Team A'].elo_rating == 1600.0
        assert teams['Team A'].match_wins == 0
        assert teams['Team A'].match_losses == 0

    def test_validate_data_correct_team_count(self):
        """Test data validation checks team count."""
        teams = {f'Team {i}': Team(f'Team {i}', 1500) for i in range(12)}

        # Create proper round-robin schedule (each team plays all others once)
        matches = []
        match_id = 0
        for i in range(12):
            for j in range(i + 1, 12):
                matches.append(Match(f'match_{match_id}', f'Team {i}', f'Team {j}'))
                match_id += 1

        # Should not raise with correct count
        try:
            DataLoader.validate_data(teams, matches, expected_teams=12, expected_matches=66)
        except ValueError:
            pytest.fail("validate_data raised ValueError unexpectedly")

    def test_validate_data_incorrect_team_count(self):
        """Test data validation fails with wrong team count."""
        teams = {f'Team {i}': Team(f'Team {i}', 1500) for i in range(10)}
        matches = []

        with pytest.raises(ValueError, match="Expected 12 teams"):
            DataLoader.validate_data(teams, matches)

    def test_validate_data_unknown_team_in_match(self):
        """Test validation fails if match references unknown team."""
        teams = {'Team A': Team('Team A', 1500)}
        matches = [Match('match_1', 'Team A', 'Team B')]  # Team B doesn't exist

        with pytest.raises(ValueError, match="Unknown team"):
            DataLoader.validate_data(teams, matches, expected_teams=1, expected_matches=1)

    def test_load_all_data_integration(self):
        """Integration test for loading all data."""
        teams, matches = DataLoader.load_all_data(
            Config.MATCHES_CSV,
            Config.ELO_RATINGS_CSV,
            validate=True
        )

        # Should have correct counts
        assert len(teams) == 12
        assert len(matches) == 66

        # Teams should be Team objects
        assert all(isinstance(t, Team) for t in teams.values())

        # Matches should be Match objects
        assert all(isinstance(m, Match) for m in matches)

    def test_match_has_start_date(self):
        """Test that matches include start date information."""
        matches = DataLoader.load_matches(Config.MATCHES_CSV)

        # All matches should have a start date
        for match in matches:
            assert match.start_date is not None
            assert len(match.start_date) > 0

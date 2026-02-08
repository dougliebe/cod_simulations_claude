"""Tests for standings calculator."""

import pytest
from backend.models.team import Team
from backend.models.match import Match
from backend.models.standings import SeasonStandings


class TestSeasonStandings:
    """Test cases for SeasonStandings class."""

    @pytest.fixture
    def basic_standings(self):
        """Create basic standings with 4 teams."""
        teams = {
            'Team A': Team('Team A', 1600),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1400),
            'Team D': Team('Team D', 1300)
        }

        matches = [
            Match('m1', 'Team A', 'Team B', 3, 1),  # A beats B
            Match('m2', 'Team A', 'Team C', 3, 0),  # A beats C
            Match('m3', 'Team B', 'Team C', 3, 2),  # B beats C
            Match('m4', 'Team A', 'Team D', 3, 1),  # A beats D
            Match('m5', 'Team B', 'Team D', 3, 2),  # B beats D
            Match('m6', 'Team C', 'Team D', 3, 2),  # C beats D
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()
        return standings

    def test_update_team_records_from_matches(self, basic_standings):
        """Test that team records are correctly updated from matches."""
        teams = basic_standings.teams

        # Team A: 3-0 in matches
        assert teams['Team A'].match_wins == 3
        assert teams['Team A'].match_losses == 0

        # Team A map record: (3+3+3)-(1+0+1) = 9-2
        assert teams['Team A'].map_wins == 9
        assert teams['Team A'].map_losses == 2

        # Team D: 0-3 in matches
        assert teams['Team D'].match_wins == 0
        assert teams['Team D'].match_losses == 3

    def test_get_completed_matches(self, basic_standings):
        """Test getting completed matches."""
        completed = basic_standings.get_completed_matches()
        assert len(completed) == 6
        assert all(m.is_completed for m in completed)

    def test_get_head_to_head_matches(self, basic_standings):
        """Test getting h2h matches between specific teams."""
        h2h = basic_standings.get_head_to_head_matches(['Team A', 'Team B'])

        # Should only get match between A and B
        assert len(h2h) == 1
        assert h2h[0].id == 'm1'

    def test_all_teams_played_each_other_true(self, basic_standings):
        """Test detection when all teams played each other."""
        # Teams A, B, C have all played each other
        result = basic_standings.all_teams_played_each_other(['Team A', 'Team B', 'Team C'])
        assert result is True

    def test_all_teams_played_each_other_false(self):
        """Test detection when teams haven't all played each other."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500)
        }

        # Only A vs B played, missing A vs C and B vs C
        matches = [Match('m1', 'Team A', 'Team B', 3, 1)]

        standings = SeasonStandings(teams, matches)
        result = standings.all_teams_played_each_other(['Team A', 'Team B', 'Team C'])
        assert result is False

    def test_get_head_to_head_record_matches(self, basic_standings):
        """Test h2h match record calculation."""
        h2h_records = basic_standings.get_head_to_head_record(
            ['Team A', 'Team B', 'Team C'],
            use_maps=False
        )

        # Team A: 2-0 (beat B and C)
        assert h2h_records['Team A'] == (2, 0)

        # Team B: 1-1 (lost to A, beat C)
        assert h2h_records['Team B'] == (1, 1)

        # Team C: 0-2 (lost to both)
        assert h2h_records['Team C'] == (0, 2)

    def test_get_head_to_head_record_maps(self, basic_standings):
        """Test h2h map record calculation."""
        h2h_records = basic_standings.get_head_to_head_record(
            ['Team A', 'Team B'],
            use_maps=True
        )

        # Match was A 3-1 B
        assert h2h_records['Team A'] == (3, 1)
        assert h2h_records['Team B'] == (1, 3)

    def test_calculate_strength_of_schedule_matches(self, basic_standings):
        """Test strength of schedule calculation using match win %."""
        # Team D played A, B, C (all lost to D)
        # A: 3-0 overall = 100%
        # B: 2-1 overall = 66.67%
        # C: 1-2 overall = 33.33%
        # SOS for D = (1.0 + 0.6667 + 0.3333) / 3 = 0.6667

        sos = basic_standings.calculate_strength_of_schedule('Team D', use_maps=False)
        assert abs(sos - 0.6667) < 0.01

    def test_get_teams_by_record(self, basic_standings):
        """Test getting teams sorted by win percentage."""
        sorted_teams = basic_standings.get_teams_by_record(use_maps=False)

        # Order should be: A (3-0), B (2-1), C (1-2), D (0-3)
        assert sorted_teams[0] == 'Team A'
        assert sorted_teams[1] == 'Team B'
        assert sorted_teams[2] == 'Team C'
        assert sorted_teams[3] == 'Team D'

    def test_group_teams_by_record_no_ties(self, basic_standings):
        """Test grouping when no teams are tied."""
        groups = basic_standings.group_teams_by_record(use_maps=False)

        # All teams have different records
        assert len(groups) == 4
        assert all(len(group) == 1 for group in groups)

    def test_group_teams_by_record_with_ties(self):
        """Test grouping when teams have identical records."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500),
            'Team D': Team('Team D', 1500)
        }

        matches = [
            Match('m1', 'Team A', 'Team C', 3, 0),
            Match('m2', 'Team B', 'Team D', 3, 0),
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        groups = standings.group_teams_by_record(use_maps=False)

        # Should have 2 groups: [A, B] with 1-0, [C, D] with 0-1
        assert len(groups) == 2
        assert len(groups[0]) == 2  # Teams A and B tied
        assert len(groups[1]) == 2  # Teams C and D tied

    def test_empty_standings(self):
        """Test standings with no completed matches."""
        teams = {f'Team {i}': Team(f'Team {i}', 1500) for i in range(4)}
        matches = [Match(f'm{i}', 'Team 0', 'Team 1') for i in range(4)]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        # All teams should have 0-0 record
        for team in teams.values():
            assert team.match_wins == 0
            assert team.match_losses == 0

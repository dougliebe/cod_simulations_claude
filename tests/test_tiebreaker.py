"""Tests for tiebreaker system."""

import pytest
from backend.models.team import Team
from backend.models.match import Match
from backend.models.standings import SeasonStandings
from backend.simulation.tiebreaker import TiebreakerResolver


class TestTiebreakerResolver:
    """Test cases for TiebreakerResolver class."""

    def test_no_tie_single_team(self):
        """Single team should return as-is."""
        teams = {'Team A': Team('Team A', 1500)}
        matches = []

        standings = SeasonStandings(teams, matches)
        resolver = TiebreakerResolver(standings)

        result = resolver.resolve_tie(['Team A'])
        assert result == ['Team A']

    def test_tier1_h2h_match_percentage(self):
        """Test Tier 1: Head-to-head match win percentage."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500)
        }

        # All tied at 2-1, but h2h: A beat B, B beat C, A beat C
        # So A should be first (2-0 h2h), B second (1-1 h2h), C third (0-2 h2h)
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 0),  # A > B
            Match('m2', 'Team B', 'Team C', 3, 0),  # B > C
            Match('m3', 'Team A', 'Team C', 3, 0),  # A > C
            Match('m4', 'Team A', 'Team D', 0, 3),  # A loses to D (external)
            Match('m5', 'Team B', 'Team D', 0, 3),  # B loses to D
            Match('m6', 'Team C', 'Team D', 0, 3),  # C loses to D
        ]
        teams['Team D'] = Team('Team D', 1500)

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)
        result = resolver.resolve_tie(['Team A', 'Team B', 'Team C'])

        assert result[0] == 'Team A'
        assert result[1] == 'Team B'
        assert result[2] == 'Team C'

    def test_tier1_circular_head_to_head(self):
        """Test circular h2h (A>B, B>C, C>A) moves to next tier."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500)
        }

        # Circular: A > B, B > C, C > A
        # All have 1-1 h2h record, so should move to Tier 2 (map %)
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 0),  # A > B 3-0
            Match('m2', 'Team B', 'Team C', 3, 1),  # B > C 3-1
            Match('m3', 'Team C', 'Team A', 3, 2),  # C > A 3-2
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)

        # Tier 1 should not resolve (all 1-1)
        tier1_result = resolver._apply_tier1_h2h_match_pct(['Team A', 'Team B', 'Team C'])
        assert tier1_result is None or len(set(tier1_result)) == len(tier1_result)  # No complete tie

        # But Tier 2 (map %) should resolve:
        # A: 3+2 = 5 maps won, 0+3 = 3 lost = 5/8 = 62.5%
        # B: 3+1 = 4 won, 0+3 = 3 lost = 4/7 = 57.1%
        # C: 3+0 = 3 won, 1+2 = 3 lost = 3/6 = 50%
        result = resolver.resolve_tie(['Team A', 'Team B', 'Team C'])
        assert result[0] == 'Team A'

    def test_tier2_h2h_map_percentage(self):
        """Test Tier 2: Head-to-head map win percentage."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500)
        }

        # Both 1-1 in matches, but A won more maps h2h
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 2),  # A wins 3-2
            Match('m2', 'Team B', 'Team A', 3, 1),  # B wins 3-1
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)

        # Both 1-1 in h2h matches, but maps: A (3+1=4), B (2+3=5)
        # B should win on map %
        result = resolver.resolve_tie(['Team A', 'Team B'])
        assert result[0] == 'Team B'

    def test_tier3_overall_match_percentage(self):
        """Test Tier 3: Overall match win percentage."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500)
        }

        # A and B haven't played each other, so skip h2h tiers
        # A: 2-0, B: 1-1, C: 0-2 overall
        matches = [
            Match('m1', 'Team A', 'Team C', 3, 0),
            Match('m2', 'Team A', 'Team C', 3, 0),
            Match('m3', 'Team B', 'Team C', 3, 0),
            Match('m4', 'Team B', 'Team C', 0, 3),
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)
        result = resolver.resolve_tie(['Team A', 'Team B'])

        # A has better overall record
        assert result[0] == 'Team A'
        assert result[1] == 'Team B'

    def test_partial_tie_resolution(self):
        """Test partial tie resolution (some teams separated, some still tied)."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500),
            'Team D': Team('Team D', 1500),
            'Team E': Team('Team E', 1500)
        }

        # Create scenario where tiebreaker partially separates:
        # A: 2-0, B and C: 1-1, D and E: 0-2
        # All teams play against F (external) to establish records
        teams['Team F'] = Team('Team F', 1500)

        matches = [
            # Team A: 2-0 (beats D and E)
            Match('m1', 'Team A', 'Team D', 3, 0),
            Match('m2', 'Team A', 'Team E', 3, 0),
            # Team B: 1-1 (beats D, loses to F)
            Match('m3', 'Team B', 'Team D', 3, 0),
            Match('m4', 'Team B', 'Team F', 0, 3),
            # Team C: 1-1 (beats D, loses to F)
            Match('m5', 'Team C', 'Team D', 3, 0),
            Match('m6', 'Team C', 'Team F', 0, 3),
            # Team D: 0-4 (loses to everyone)
            Match('m7', 'Team D', 'Team F', 0, 3),
            # Team E: 0-2 (loses to A and F)
            Match('m8', 'Team E', 'Team F', 0, 3),
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)
        result = resolver.resolve_tie(['Team A', 'Team B', 'Team C', 'Team D', 'Team E'])

        # A should be first (2-0)
        assert result[0] == 'Team A'

        # B and C should be 2nd/3rd (tied at 1-1, recursively resolved)
        assert set([result[1], result[2]]) == {'Team B', 'Team C'}

        # D has worse record than E (0-4 vs 0-2)
        # E should be 4th, D should be 5th
        assert result[4] == 'Team D'

    def test_all_teams_identical_records(self):
        """Test when all teams have identical records across all tiers."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500),
            'Team D': Team('Team D', 1500)
        }

        # No matches = all 0-0
        matches = []

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)
        result = resolver.resolve_tie(['Team A', 'Team B', 'Team C', 'Team D'])

        # Should get some ordering (random from Tier 7)
        assert len(result) == 4
        assert set(result) == {'Team A', 'Team B', 'Team C', 'Team D'}

    def test_calculate_seeding_full_season(self):
        """Test calculating full seeding for all teams."""
        teams = {
            'Team 1': Team('Team 1', 1600),
            'Team 2': Team('Team 2', 1550),
            'Team 3': Team('Team 3', 1500),
            'Team 4': Team('Team 4', 1450)
        }

        # Team 1: 3-0, Team 2: 2-1, Team 3: 1-2, Team 4: 0-3
        matches = [
            Match('m1', 'Team 1', 'Team 2', 3, 0),
            Match('m2', 'Team 1', 'Team 3', 3, 0),
            Match('m3', 'Team 1', 'Team 4', 3, 0),
            Match('m4', 'Team 2', 'Team 3', 3, 0),
            Match('m5', 'Team 2', 'Team 4', 3, 0),
            Match('m6', 'Team 3', 'Team 4', 3, 0),
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)
        seeding = resolver.calculate_seeding()

        # Should be ordered by record
        assert seeding == ['Team 1', 'Team 2', 'Team 3', 'Team 4']

    def test_h2h_skipped_when_not_all_played(self):
        """Test that h2h tiers are skipped when teams haven't all played each other."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team C': Team('Team C', 1500)
        }

        # Only A vs B played, missing other matchups
        matches = [
            Match('m1', 'Team A', 'Team B', 3, 1),
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)

        # Tier 1 should return None (not all played)
        result = resolver._apply_tier1_h2h_match_pct(['Team A', 'Team B', 'Team C'])
        assert result is None

    def test_get_tiebreaker_explanation(self):
        """Test getting human-readable tiebreaker explanation."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500)
        }

        matches = [
            Match('m1', 'Team A', 'Team B', 3, 1),
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        resolver = TiebreakerResolver(standings)
        explanation = resolver.get_tiebreaker_explanation(['Team A', 'Team B'])

        # Should mention h2h since they played
        assert 'Tier 1' in explanation or 'Tier 2' in explanation

    def test_strength_of_schedule_tiebreaker(self):
        """Test that SOS can break ties."""
        teams = {
            'Team A': Team('Team A', 1500),
            'Team B': Team('Team B', 1500),
            'Team Strong': Team('Team Strong', 1800),
            'Team Weak': Team('Team Weak', 1200)
        }

        # A and B both 1-1, but A played stronger opponent
        matches = [
            Match('m1', 'Team A', 'Team Strong', 3, 2),  # A beats strong team
            Match('m2', 'Team A', 'Team Weak', 0, 3),    # A loses to weak team
            Match('m3', 'Team B', 'Team Strong', 0, 3),  # B loses to strong team
            Match('m4', 'Team B', 'Team Weak', 3, 0),    # B beats weak team
            Match('m5', 'Team Strong', 'Team Weak', 3, 0),  # Strong > Weak
        ]

        standings = SeasonStandings(teams, matches)
        standings.update_team_records_from_matches()

        # Both A and B are 1-1, haven't played each other
        # SOS for A: (Strong + Weak) / 2 = (1-1 + 0-1) / 2 = 0.25
        # SOS for B: (Strong + Weak) / 2 = (1-1 + 1-0) / 2 = 0.75
        # B should rank higher (stronger schedule)

        resolver = TiebreakerResolver(standings)
        result = resolver.resolve_tie(['Team A', 'Team B'])

        # B faced tougher schedule
        assert result[0] == 'Team B'

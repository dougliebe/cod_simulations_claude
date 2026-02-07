"""Standings calculator for Call of Duty season."""

from typing import Dict, List, Set, Tuple, FrozenSet
from backend.models.team import Team
from backend.models.match import Match


class SeasonStandings:
    """Calculate and manage season standings with head-to-head tracking."""

    def __init__(self, teams: Dict[str, Team], matches: List[Match]):
        """
        Initialize standings calculator.

        Args:
            teams: Dictionary mapping team name to Team object
            matches: List of all matches (completed and upcoming)
        """
        self.teams = teams
        self.matches = matches
        self._h2h_cache = {}  # Cache for head-to-head calculations

    def get_completed_matches(self) -> List[Match]:
        """Get all completed matches."""
        return [m for m in self.matches if m.is_completed]

    def get_head_to_head_matches(self, team_names: List[str]) -> List[Match]:
        """
        Get all completed matches between a specific set of teams.

        Args:
            team_names: List of team names to consider

        Returns:
            List of completed matches between these teams only
        """
        team_set = set(team_names)
        return [
            m for m in self.matches
            if m.is_completed and m.team1 in team_set and m.team2 in team_set
        ]

    def all_teams_played_each_other(self, team_names: List[str]) -> bool:
        """
        Check if all teams in the group have played each other.

        Required for head-to-head tiebreakers to be valid.

        Args:
            team_names: List of team names

        Returns:
            True if all teams played each other, False otherwise
        """
        if len(team_names) < 2:
            return True

        # Build set of required matchups
        required_matchups: Set[FrozenSet[str]] = set()
        for i, team1 in enumerate(team_names):
            for team2 in team_names[i + 1:]:
                required_matchups.add(frozenset([team1, team2]))

        # Build set of actual matchups from completed matches
        actual_matchups: Set[FrozenSet[str]] = set()
        for match in self.get_head_to_head_matches(team_names):
            actual_matchups.add(frozenset([match.team1, match.team2]))

        # All required matchups must exist
        return required_matchups.issubset(actual_matchups)

    def get_head_to_head_record(
        self,
        team_names: List[str],
        use_maps: bool = False
    ) -> Dict[str, Tuple[int, int]]:
        """
        Calculate head-to-head records among a set of teams.

        Args:
            team_names: List of team names to consider
            use_maps: If True, return map wins/losses; if False, match wins/losses

        Returns:
            Dictionary mapping team name to (wins, losses) tuple
        """
        records = {team: (0, 0) for team in team_names}
        h2h_matches = self.get_head_to_head_matches(team_names)

        for match in h2h_matches:
            if use_maps:
                # Map-level record
                wins1, losses1 = records[match.team1]
                wins2, losses2 = records[match.team2]

                records[match.team1] = (wins1 + match.team1_score, losses1 + match.team2_score)
                records[match.team2] = (wins2 + match.team2_score, losses2 + match.team1_score)
            else:
                # Match-level record
                winner = match.winner
                loser = match.loser

                wins, losses = records[winner]
                records[winner] = (wins + 1, losses)

                wins, losses = records[loser]
                records[loser] = (wins, losses + 1)

        return records

    def calculate_strength_of_schedule(
        self,
        team_name: str,
        use_maps: bool = False
    ) -> float:
        """
        Calculate strength of schedule for a team.

        SOS = average win percentage of all opponents faced.
        Excludes games against the team itself.

        Args:
            team_name: Team to calculate SOS for
            use_maps: If True, use map win %; if False, use match win %

        Returns:
            Strength of schedule (0.0 to 1.0)
        """
        # Find all opponents
        opponents = []
        for match in self.get_completed_matches():
            if match.team1 == team_name:
                opponents.append(match.team2)
            elif match.team2 == team_name:
                opponents.append(match.team1)

        if not opponents:
            return 0.0

        # Calculate win percentage for each opponent (excluding games vs team_name)
        opponent_win_pcts = []
        for opp in opponents:
            opp_team = self.teams[opp]

            if use_maps:
                # Calculate map win % excluding games vs team_name
                opp_wins = opp_team.map_wins
                opp_losses = opp_team.map_losses

                # Subtract maps from games vs team_name
                for match in self.get_completed_matches():
                    if match.team1 == opp and match.team2 == team_name:
                        opp_wins -= match.team1_score
                        opp_losses -= match.team2_score
                    elif match.team2 == opp and match.team1 == team_name:
                        opp_wins -= match.team2_score
                        opp_losses -= match.team1_score

                total = opp_wins + opp_losses
                win_pct = opp_wins / total if total > 0 else 0.0
            else:
                # Calculate match win % excluding games vs team_name
                opp_wins = opp_team.match_wins
                opp_losses = opp_team.match_losses

                # Subtract match vs team_name
                for match in self.get_completed_matches():
                    if (match.team1 == opp and match.team2 == team_name) or \
                       (match.team2 == opp and match.team1 == team_name):
                        if match.winner == opp:
                            opp_wins -= 1
                        else:
                            opp_losses -= 1

                total = opp_wins + opp_losses
                win_pct = opp_wins / total if total > 0 else 0.0

            opponent_win_pcts.append(win_pct)

        # Return average opponent win percentage
        return sum(opponent_win_pcts) / len(opponent_win_pcts)

    def get_teams_by_record(self, use_maps: bool = False) -> List[str]:
        """
        Get teams sorted by win percentage (no tiebreakers applied).

        Args:
            use_maps: If True, sort by map win %; if False, sort by match win %

        Returns:
            List of team names sorted by win percentage (highest to lowest)
        """
        if use_maps:
            return sorted(
                self.teams.keys(),
                key=lambda t: self.teams[t].map_win_pct,
                reverse=True
            )
        else:
            return sorted(
                self.teams.keys(),
                key=lambda t: self.teams[t].match_win_pct,
                reverse=True
            )

    def group_teams_by_record(self, use_maps: bool = False) -> List[List[str]]:
        """
        Group teams that have identical records.

        Args:
            use_maps: If True, group by map record; if False, group by match record

        Returns:
            List of groups, where each group is a list of team names with identical records
        """
        groups = []
        current_group = []
        current_pct = None

        for team in self.get_teams_by_record(use_maps):
            pct = self.teams[team].map_win_pct if use_maps else self.teams[team].match_win_pct

            if current_pct is None or abs(pct - current_pct) < 0.0001:
                # Same percentage (within floating point tolerance)
                current_group.append(team)
                current_pct = pct
            else:
                # Different percentage - start new group
                if current_group:
                    groups.append(current_group)
                current_group = [team]
                current_pct = pct

        # Add last group
        if current_group:
            groups.append(current_group)

        return groups

    def update_team_records_from_matches(self) -> None:
        """
        Update all team records based on completed matches.

        Call this after adding/updating match results.
        """
        # Reset all records
        for team in self.teams.values():
            team.reset_records()

        # Apply all completed matches
        for match in self.get_completed_matches():
            team1 = self.teams[match.team1]
            team2 = self.teams[match.team2]

            # Update match records
            if match.team1_score > match.team2_score:
                team1.match_wins += 1
                team2.match_losses += 1
            else:
                team1.match_losses += 1
                team2.match_wins += 1

            # Update map records
            team1.map_wins += match.team1_score
            team1.map_losses += match.team2_score
            team2.map_wins += match.team2_score
            team2.map_losses += match.team1_score

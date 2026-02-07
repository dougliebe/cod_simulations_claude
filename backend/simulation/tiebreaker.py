"""7-tier tiebreaker system for Call of Duty standings."""

import random
from typing import List, Dict, Tuple, Optional
from backend.models.standings import SeasonStandings
from config import Config


class TiebreakerResolver:
    """Implements the 7-tier tiebreaker system with recursive resolution."""

    def __init__(self, standings: SeasonStandings):
        """
        Initialize tiebreaker resolver.

        Args:
            standings: SeasonStandings object with team records and matches
        """
        self.standings = standings

    def calculate_seeding(self) -> List[str]:
        """
        Calculate final seeding for all teams using tiebreaker rules.

        Returns:
            List of team names ordered by seed (1st to 12th)
        """
        # Start with teams grouped by match win percentage
        groups = self.standings.group_teams_by_record(use_maps=False)

        # Resolve ties within each group
        final_seeding = []
        for group in groups:
            resolved = self.resolve_tie(group)
            final_seeding.extend(resolved)

        return final_seeding

    def resolve_tie(self, tied_teams: List[str]) -> List[str]:
        """
        Resolve ties among a group of teams using 7-tier system.

        Recursively handles partial tie resolution.

        Args:
            tied_teams: List of team names that are tied

        Returns:
            Ordered list of team names (ties broken)
        """
        # Base case: no tie to resolve
        if len(tied_teams) <= 1:
            return tied_teams

        # Try each tiebreaker tier in order
        result = self._apply_tier1_h2h_match_pct(tied_teams)
        if result:
            return result

        result = self._apply_tier2_h2h_map_pct(tied_teams)
        if result:
            return result

        result = self._apply_tier3_overall_match_pct(tied_teams)
        if result:
            return result

        result = self._apply_tier4_overall_map_pct(tied_teams)
        if result:
            return result

        result = self._apply_tier5_sos_match(tied_teams)
        if result:
            return result

        result = self._apply_tier6_sos_map(tied_teams)
        if result:
            return result

        # Final tier: seed-specific rules or random
        return self._apply_tier7_seed_specific(tied_teams)

    def _apply_tier1_h2h_match_pct(self, teams: List[str]) -> Optional[List[str]]:
        """
        Tier 1: Head-to-head match win percentage.
        Skip if not all teams played each other.
        """
        # Check if all teams played each other
        if not self.standings.all_teams_played_each_other(teams):
            return None

        # Calculate h2h match records
        h2h_records = self.standings.get_head_to_head_record(teams, use_maps=False)

        # Calculate win percentages
        win_pcts = {}
        for team, (wins, losses) in h2h_records.items():
            total = wins + losses
            win_pcts[team] = wins / total if total > 0 else 0.0

        # Sort by h2h win percentage
        sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)

        # Handle partial separation
        return self._handle_partial_separation(sorted_teams, win_pcts)

    def _apply_tier2_h2h_map_pct(self, teams: List[str]) -> Optional[List[str]]:
        """
        Tier 2: Head-to-head map win percentage.
        Skip if not all teams played each other.
        """
        # Check if all teams played each other
        if not self.standings.all_teams_played_each_other(teams):
            return None

        # Calculate h2h map records
        h2h_records = self.standings.get_head_to_head_record(teams, use_maps=True)

        # Calculate win percentages
        win_pcts = {}
        for team, (wins, losses) in h2h_records.items():
            total = wins + losses
            win_pcts[team] = wins / total if total > 0 else 0.0

        # Sort by h2h map win percentage
        sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)

        # Handle partial separation
        return self._handle_partial_separation(sorted_teams, win_pcts)

    def _apply_tier3_overall_match_pct(self, teams: List[str]) -> Optional[List[str]]:
        """
        Tier 3: Overall match win percentage.
        """
        # Get match win percentages
        win_pcts = {
            team: self.standings.teams[team].match_win_pct
            for team in teams
        }

        # Sort by overall match win percentage
        sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)

        # Handle partial separation
        return self._handle_partial_separation(sorted_teams, win_pcts)

    def _apply_tier4_overall_map_pct(self, teams: List[str]) -> Optional[List[str]]:
        """
        Tier 4: Overall map win percentage.
        """
        # Get map win percentages
        win_pcts = {
            team: self.standings.teams[team].map_win_pct
            for team in teams
        }

        # Sort by overall map win percentage
        sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)

        # Handle partial separation
        return self._handle_partial_separation(sorted_teams, win_pcts)

    def _apply_tier5_sos_match(self, teams: List[str]) -> Optional[List[str]]:
        """
        Tier 5: Strength of schedule (match win percentage).
        """
        # Calculate SOS for each team
        sos_values = {
            team: self.standings.calculate_strength_of_schedule(team, use_maps=False)
            for team in teams
        }

        # Sort by SOS (higher is better)
        sorted_teams = sorted(teams, key=lambda t: sos_values[t], reverse=True)

        # Handle partial separation
        return self._handle_partial_separation(sorted_teams, sos_values)

    def _apply_tier6_sos_map(self, teams: List[str]) -> Optional[List[str]]:
        """
        Tier 6: Strength of schedule (map win percentage).
        """
        # Calculate SOS for each team
        sos_values = {
            team: self.standings.calculate_strength_of_schedule(team, use_maps=True)
            for team in teams
        }

        # Sort by SOS (higher is better)
        sorted_teams = sorted(teams, key=lambda t: sos_values[t], reverse=True)

        # Handle partial separation
        return self._handle_partial_separation(sorted_teams, sos_values)

    def _apply_tier7_seed_specific(self, teams: List[str]) -> List[str]:
        """
        Tier 7: Seed-specific rules.

        - Seeds 1/2/3/8: Tiebreaker match (simulated as random for now)
        - Seeds 4/9/10/11: Coin flip (random)
        - Other seeds: Random or higher seed chooses

        For simulation purposes, use random selection.
        """
        # In actual implementation, would check which seeds these teams are competing for
        # For now, use random shuffle
        shuffled = list(teams)
        random.shuffle(shuffled)
        return shuffled

    def _handle_partial_separation(
        self,
        sorted_teams: List[str],
        metric_values: Dict[str, float]
    ) -> Optional[List[str]]:
        """
        Handle case where tiebreaker partially separates teams.

        If tiebreaker creates groups (some teams tied, some separated),
        recursively resolve ties within each group.

        Args:
            sorted_teams: Teams sorted by the metric
            metric_values: Dictionary of metric values for each team

        Returns:
            Fully resolved ordering, or None if no separation occurred
        """
        # Group teams by metric value (with tolerance for floating point)
        groups = []
        current_group = [sorted_teams[0]]
        current_value = metric_values[sorted_teams[0]]

        for team in sorted_teams[1:]:
            value = metric_values[team]

            if abs(value - current_value) < 1e-9:  # Floating point tolerance
                # Same value - add to current group
                current_group.append(team)
            else:
                # Different value - finalize current group and start new one
                groups.append(current_group)
                current_group = [team]
                current_value = value

        # Add last group
        groups.append(current_group)

        # If only one group, no separation occurred
        if len(groups) == 1:
            return None

        # Partial or full separation occurred
        # Recursively resolve ties within each group
        resolved = []
        for group in groups:
            if len(group) == 1:
                resolved.extend(group)
            else:
                # Recursively resolve this tied group
                resolved.extend(self.resolve_tie(group))

        return resolved

    def get_tiebreaker_explanation(self, teams: List[str]) -> str:
        """
        Get human-readable explanation of how a tie was broken.

        Useful for debugging and displaying to users.

        Args:
            teams: List of tied teams

        Returns:
            String explaining which tiebreaker tier was used
        """
        if len(teams) <= 1:
            return "No tie to break"

        # Try each tier and see which one would separate
        if self.standings.all_teams_played_each_other(teams):
            h2h_records = self.standings.get_head_to_head_record(teams, use_maps=False)
            win_pcts = {
                team: (wins / (wins + losses) if wins + losses > 0 else 0)
                for team, (wins, losses) in h2h_records.items()
            }
            if len(set(win_pcts.values())) > 1:
                return "Tier 1: Head-to-head match win percentage"

            h2h_records = self.standings.get_head_to_head_record(teams, use_maps=True)
            win_pcts = {
                team: (wins / (wins + losses) if wins + losses > 0 else 0)
                for team, (wins, losses) in h2h_records.items()
            }
            if len(set(win_pcts.values())) > 1:
                return "Tier 2: Head-to-head map win percentage"

        match_pcts = {team: self.standings.teams[team].match_win_pct for team in teams}
        if len(set(match_pcts.values())) > 1:
            return "Tier 3: Overall match win percentage"

        map_pcts = {team: self.standings.teams[team].map_win_pct for team in teams}
        if len(set(map_pcts.values())) > 1:
            return "Tier 4: Overall map win percentage"

        sos_match = {
            team: self.standings.calculate_strength_of_schedule(team, use_maps=False)
            for team in teams
        }
        if len(set(sos_match.values())) > 1:
            return "Tier 5: Strength of schedule (match win %)"

        sos_map = {
            team: self.standings.calculate_strength_of_schedule(team, use_maps=True)
            for team in teams
        }
        if len(set(sos_map.values())) > 1:
            return "Tier 6: Strength of schedule (map win %)"

        return "Tier 7: Seed-specific rules (coin flip/tiebreaker match)"

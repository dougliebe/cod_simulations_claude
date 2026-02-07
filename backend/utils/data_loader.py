"""Data loading and validation utilities."""

import csv
from typing import Dict, List
from backend.models.team import Team
from backend.models.match import Match


class DataLoader:
    """Load and validate CSV data for CoD simulations."""

    @staticmethod
    def load_elo_ratings(filepath: str) -> Dict[str, float]:
        """
        Load Elo ratings from CSV.

        Expected format: team_id,elo

        Args:
            filepath: Path to CSV file

        Returns:
            Dictionary mapping team name to Elo rating

        Raises:
            ValueError: If Elo rating is invalid (negative)
            FileNotFoundError: If file doesn't exist
        """
        ratings = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                team = row['team_id'].strip()
                elo = float(row['elo'])

                if elo < 0:
                    raise ValueError(f"Invalid Elo rating for {team}: {elo}")

                ratings[team] = elo

        return ratings

    @staticmethod
    def load_matches(filepath: str) -> List[Match]:
        """
        Load matches from CSV.

        Expected format: start_date,team1_id,team2_id,team1_score,team2_score
        Scores can be "NA" for unplayed matches or integers for completed matches.

        Args:
            filepath: Path to CSV file

        Returns:
            List of Match objects

        Raises:
            ValueError: If match data is invalid
            FileNotFoundError: If file doesn't exist
        """
        matches = []
        seen_matchups = set()

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader):
                team1 = row['team1_id'].strip()
                team2 = row['team2_id'].strip()
                start_date = row['start_date'].strip()

                # Parse scores (handle "NA" for unplayed matches)
                team1_score_str = row['team1_score'].strip()
                team2_score_str = row['team2_score'].strip()

                team1_score = None
                team2_score = None

                if team1_score_str and team1_score_str.upper() != 'NA':
                    team1_score = int(team1_score_str)

                if team2_score_str and team2_score_str.upper() != 'NA':
                    team2_score = int(team2_score_str)

                # Create match
                match = Match(
                    id=f"match_{idx}",
                    team1=team1,
                    team2=team2,
                    team1_score=team1_score,
                    team2_score=team2_score,
                    start_date=start_date
                )

                # Validate scores if completed
                if match.is_completed and not match.is_valid_score():
                    raise ValueError(
                        f"Invalid best-of-5 score for {team1} vs {team2}: "
                        f"{team1_score}-{team2_score}"
                    )

                matches.append(match)

                # Track matchups (note: teams can play multiple times)
                matchup = frozenset([team1, team2])
                seen_matchups.add(matchup)

        return matches

    @staticmethod
    def create_teams_from_elo(elo_ratings: Dict[str, float]) -> Dict[str, Team]:
        """
        Create Team objects from Elo ratings dictionary.

        Args:
            elo_ratings: Dictionary mapping team name to Elo rating

        Returns:
            Dictionary mapping team name to Team object
        """
        teams = {}
        for name, elo in elo_ratings.items():
            teams[name] = Team(name=name, elo_rating=elo)
        return teams

    @staticmethod
    def validate_data(
        teams: Dict[str, Team],
        matches: List[Match],
        expected_teams: int = 12,
        expected_matches: int = 66
    ) -> None:
        """
        Validate loaded data for consistency.

        Args:
            teams: Dictionary of Team objects
            matches: List of Match objects
            expected_teams: Expected number of teams (default 12)
            expected_matches: Expected number of matches (default 66)

        Raises:
            ValueError: If data validation fails
        """
        # Check team count
        if len(teams) != expected_teams:
            raise ValueError(
                f"Expected {expected_teams} teams, found {len(teams)}"
            )

        # Check match count
        if len(matches) != expected_matches:
            raise ValueError(
                f"Expected {expected_matches} matches, found {len(matches)}"
            )

        # Verify all teams in matches exist in teams dict
        all_team_names = set(teams.keys())
        for match in matches:
            if match.team1 not in all_team_names:
                raise ValueError(f"Unknown team in match: {match.team1}")
            if match.team2 not in all_team_names:
                raise ValueError(f"Unknown team in match: {match.team2}")

        # Verify each team plays expected number of matches (11 in round-robin)
        team_match_counts = {team: 0 for team in all_team_names}
        for match in matches:
            team_match_counts[match.team1] += 1
            team_match_counts[match.team2] += 1

        expected_matches_per_team = expected_teams - 1  # Each team plays all others
        for team, count in team_match_counts.items():
            if count != expected_matches_per_team:
                raise ValueError(
                    f"Team {team} has {count} matches, expected {expected_matches_per_team}"
                )

    @staticmethod
    def load_all_data(
        matches_file: str,
        elo_file: str,
        validate: bool = True
    ) -> tuple[Dict[str, Team], List[Match]]:
        """
        Load all data from CSV files.

        Convenience method that loads both teams and matches.

        Args:
            matches_file: Path to matches CSV
            elo_file: Path to Elo ratings CSV
            validate: Whether to validate data consistency (default True)

        Returns:
            Tuple of (teams_dict, matches_list)
        """
        elo_ratings = DataLoader.load_elo_ratings(elo_file)
        teams = DataLoader.create_teams_from_elo(elo_ratings)
        matches = DataLoader.load_matches(matches_file)

        if validate:
            DataLoader.validate_data(teams, matches)

        return teams, matches

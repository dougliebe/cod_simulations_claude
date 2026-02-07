"""Monte Carlo season simulator for Call of Duty."""

import copy
from collections import defaultdict
from typing import Dict, List, Optional
from backend.models.team import Team
from backend.models.match import Match
from backend.models.standings import SeasonStandings
from backend.simulation.elo import EloCalculator
from backend.simulation.match_simulator import MatchSimulator
from backend.simulation.tiebreaker import TiebreakerResolver


class SeasonSimulator:
    """Run Monte Carlo simulations to calculate playoff probabilities."""

    def __init__(
        self,
        teams: Dict[str, Team],
        matches: List[Match],
        elo_calculator: EloCalculator
    ):
        """
        Initialize season simulator.

        Args:
            teams: Dictionary mapping team name to Team object
            matches: List of all matches (completed and upcoming)
            elo_calculator: EloCalculator instance for probability calculations
        """
        self.base_teams = teams
        self.base_matches = matches
        self.elo_calculator = elo_calculator
        self.match_simulator = MatchSimulator(elo_calculator)

    def run_simulations(
        self,
        num_iterations: int = 1000,
        adjusted_matches: Optional[List[Match]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Run Monte Carlo simulations to calculate probabilities.

        Algorithm:
        1. For each iteration:
            a. Reset all team records
            b. Apply completed matches (from CSV)
            c. Apply user-adjusted matches (if any)
            d. Simulate remaining matches using Elo
            e. Calculate final seeding with tiebreakers
            f. Record results (playoffs, seed)
        2. Aggregate results into probabilities

        Args:
            num_iterations: Number of simulations to run
            adjusted_matches: Optional list of user-adjusted match results

        Returns:
            Dictionary mapping team name to probability dictionary:
            {
                "Team A": {
                    "make_playoffs": 0.85,
                    "seed_1": 0.12,
                    "seed_2": 0.23,
                    ...
                }
            }
        """
        # Track results for each team
        results = defaultdict(lambda: defaultdict(int))

        # Run simulations
        for iteration in range(num_iterations):
            # Create fresh copies for this iteration
            sim_teams = self._create_fresh_teams()
            sim_matches = copy.deepcopy(self.base_matches)

            # Apply user adjustments if provided
            if adjusted_matches:
                sim_matches = self._apply_user_adjustments(sim_matches, adjusted_matches)

            # Create standings
            standings = SeasonStandings(sim_teams, sim_matches)

            # Update team records from completed matches
            standings.update_team_records_from_matches()

            # Simulate remaining matches
            self._simulate_remaining_matches(standings)

            # Calculate final seeding
            resolver = TiebreakerResolver(standings)
            final_seeding = resolver.calculate_seeding()

            # Record results
            for seed, team_name in enumerate(final_seeding, 1):
                results[team_name][f"seed_{seed}"] += 1

                # Track play-in qualification (top 10)
                if seed <= 10:
                    results[team_name]["make_play_ins"] += 1

                # Track bracket qualification (top 6)
                if seed <= 6:
                    results[team_name]["make_bracket"] += 1

        # Convert counts to probabilities
        return self._calculate_probabilities(results, num_iterations)

    def _create_fresh_teams(self) -> Dict[str, Team]:
        """Create fresh team copies with reset records."""
        fresh_teams = {}
        for name, team in self.base_teams.items():
            fresh_teams[name] = Team(
                name=name,
                elo_rating=team.elo_rating,
                match_wins=0,
                match_losses=0,
                map_wins=0,
                map_losses=0
            )
        return fresh_teams

    def _apply_user_adjustments(
        self,
        matches: List[Match],
        adjusted_matches: List[Match]
    ) -> List[Match]:
        """
        Apply user-adjusted match results.

        Replaces matches in the match list with user-provided results.

        Args:
            matches: Original match list
            adjusted_matches: User-adjusted matches

        Returns:
            Updated match list with adjustments applied
        """
        # Create dict for quick lookup
        adjustments = {
            (m.team1, m.team2): m for m in adjusted_matches
        }

        # Also allow reverse lookup (team2, team1)
        for m in adjusted_matches:
            adjustments[(m.team2, m.team1)] = Match(
                id=m.id,
                team1=m.team2,
                team2=m.team1,
                team1_score=m.team2_score,
                team2_score=m.team1_score,
                start_date=m.start_date
            )

        # Apply adjustments
        updated_matches = []
        for match in matches:
            key = (match.team1, match.team2)
            if key in adjustments:
                updated_matches.append(adjustments[key])
            else:
                updated_matches.append(match)

        return updated_matches

    def _simulate_remaining_matches(self, standings: SeasonStandings) -> None:
        """
        Simulate all unplayed matches using Elo probabilities.

        Updates team records in place.

        Args:
            standings: SeasonStandings object
        """
        for match in standings.matches:
            if not match.is_completed:
                # Get teams
                team1 = standings.teams[match.team1]
                team2 = standings.teams[match.team2]

                # Simulate match
                team1_score, team2_score = self.match_simulator.simulate_match(
                    team1.elo_rating,
                    team2.elo_rating
                )

                # Update match result
                match.team1_score = team1_score
                match.team2_score = team2_score

                # Update team records
                if team1_score > team2_score:
                    team1.match_wins += 1
                    team2.match_losses += 1
                else:
                    team1.match_losses += 1
                    team2.match_wins += 1

                team1.map_wins += team1_score
                team1.map_losses += team2_score
                team2.map_wins += team2_score
                team2.map_losses += team1_score

    def _calculate_probabilities(
        self,
        results: Dict[str, Dict[str, int]],
        num_iterations: int
    ) -> Dict[str, Dict[str, float]]:
        """
        Convert result counts to probabilities.

        Args:
            results: Dictionary of counts for each team
            num_iterations: Total number of iterations

        Returns:
            Dictionary of probabilities for each team
        """
        probabilities = {}

        for team_name, counts in results.items():
            team_probs = {}

            # Convert each count to probability
            for key, count in counts.items():
                team_probs[key] = count / num_iterations

            probabilities[team_name] = team_probs

        return probabilities

    def get_current_standings(
        self,
        adjusted_matches: Optional[List[Match]] = None
    ) -> List[tuple[str, str, str]]:
        """
        Get current standings based on completed matches and optional adjustments.

        Args:
            adjusted_matches: Optional list of user-adjusted match results

        Returns:
            List of tuples (team_name, match_record, map_record) ordered by seeding
        """
        # Create standings with completed matches
        sim_teams = self._create_fresh_teams()
        sim_matches = copy.deepcopy(self.base_matches)

        # Apply user adjustments if provided
        if adjusted_matches:
            sim_matches = self._apply_user_adjustments(sim_matches, adjusted_matches)

        standings = SeasonStandings(sim_teams, sim_matches)
        standings.update_team_records_from_matches()

        # Calculate seeding
        resolver = TiebreakerResolver(standings)
        seeding = resolver.calculate_seeding()

        # Build result
        result = []
        for team_name in seeding:
            team = sim_teams[team_name]
            result.append((
                team_name,
                team.match_record,
                team.map_record
            ))

        return result

    def simulate_single_scenario(
        self,
        adjusted_matches: Optional[List[Match]] = None
    ) -> List[str]:
        """
        Simulate a single scenario and return the final seeding.

        Useful for testing specific outcomes.

        Args:
            adjusted_matches: Optional user-adjusted matches

        Returns:
            List of team names in final seeding order
        """
        # Run single simulation
        results = self.run_simulations(num_iterations=1, adjusted_matches=adjusted_matches)

        # Extract the seeding from results
        # Find which seed each team got (will be 1.0 probability for that seed)
        seeding = [None] * len(self.base_teams)

        for team_name, probs in results.items():
            for key, prob in probs.items():
                if key.startswith('seed_') and prob == 1.0:
                    seed = int(key.split('_')[1])
                    seeding[seed - 1] = team_name
                    break

        return seeding

    def get_match_win_probability(self, team1: str, team2: str) -> float:
        """
        Get approximate win probability for team1 vs team2.

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            Probability (0-1) that team1 wins the match
        """
        elo1 = self.base_teams[team1].elo_rating
        elo2 = self.base_teams[team2].elo_rating

        # Use map-level probability as approximation
        return self.elo_calculator.calculate_win_probability(elo1, elo2)

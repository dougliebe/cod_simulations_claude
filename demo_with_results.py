"""Demo with hypothetical completed matches to show more interesting probabilities."""

import time
from backend.utils.data_loader import DataLoader
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator
from backend.models.match import Match
from config import Config


def main():
    print("=" * 80)
    print("SCENARIO: 10 MATCHES COMPLETED")
    print("=" * 80)
    print()

    # Load data
    teams, matches = DataLoader.load_all_data(
        Config.MATCHES_CSV,
        Config.ELO_RATINGS_CSV,
        validate=True
    )

    # Simulate some completed matches
    # Let's say OpTic Texas and FaZe Vegas have strong starts
    matches[0].team1_score = 3  # OpTic wins
    matches[0].team2_score = 1
    matches[1].team1_score = 3
    matches[1].team2_score = 0
    matches[2].team1_score = 3
    matches[2].team2_score = 1

    # FaZe also winning
    matches[10].team1_score = 3
    matches[10].team2_score = 0
    matches[11].team1_score = 3
    matches[11].team2_score = 2

    # Boston struggling
    matches[5].team1_score = 0
    matches[5].team2_score = 3
    matches[6].team1_score = 1
    matches[6].team2_score = 3

    # Some close matches
    matches[15].team1_score = 3
    matches[15].team2_score = 2
    matches[20].team1_score = 2
    matches[20].team2_score = 3

    completed = sum(1 for m in matches if m.is_completed)
    print(f"Completed matches: {completed}")
    print()

    # Create simulator
    elo_calc = EloCalculator()
    simulator = SeasonSimulator(teams, matches, elo_calc)

    # Show current standings
    print("CURRENT STANDINGS:")
    print("-" * 80)
    standings = simulator.get_current_standings()
    print(f"{'Seed':<6} {'Team':<30} {'Match':<10} {'Maps':<10}")
    print("-" * 80)
    for i, (team, match_rec, map_rec) in enumerate(standings, 1):
        print(f"{i:<6} {team:<30} {match_rec:<10} {map_rec:<10}")
    print()

    # Run simulations
    print("Running 1000 simulations...")
    start = time.time()
    results = simulator.run_simulations(num_iterations=1000)
    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.3f}s ({elapsed/1000*1000:.2f} ms/sim)\n")

    # Show top teams
    print("=" * 80)
    print("TOP 8 PLAYOFF PROBABILITIES")
    print("=" * 80)

    playoff_probs = [(team, probs.get('make_playoffs', 0))
                     for team, probs in results.items()]
    playoff_probs.sort(key=lambda x: x[1], reverse=True)

    for i, (team, playoff_prob) in enumerate(playoff_probs[:8], 1):
        seed_1_prob = results[team].get('seed_1', 0)
        top_3_prob = sum(results[team].get(f'seed_{s}', 0) for s in [1,2,3])

        print(f"{i}. {team:<30} Playoffs: {playoff_prob*100:5.1f}%  "
              f"Top 3: {top_3_prob*100:5.1f}%  "
              f"#1 Seed: {seed_1_prob*100:4.1f}%")

    print()
    print("=" * 80)


if __name__ == '__main__':
    main()

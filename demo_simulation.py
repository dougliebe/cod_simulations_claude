"""Demo script to run simulations and show results."""

import time
from backend.utils.data_loader import DataLoader
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator
from config import Config


def format_probability(prob):
    """Format probability as percentage."""
    return f"{prob*100:.1f}%"


def main():
    print("=" * 80)
    print("CALL OF DUTY SEASON SIMULATION - MAJOR 2 2026")
    print("=" * 80)
    print()

    # Load data
    print("Loading data...")
    teams, matches = DataLoader.load_all_data(
        Config.MATCHES_CSV,
        Config.ELO_RATINGS_CSV,
        validate=True
    )
    print(f"✓ Loaded {len(teams)} teams")
    print(f"✓ Loaded {len(matches)} matches")

    # Count completed vs upcoming
    completed = sum(1 for m in matches if m.is_completed)
    upcoming = len(matches) - completed
    print(f"  - {completed} completed")
    print(f"  - {upcoming} upcoming")
    print()

    # Create simulator
    elo_calc = EloCalculator()
    simulator = SeasonSimulator(teams, matches, elo_calc)

    # Show current standings
    print("CURRENT STANDINGS (from completed matches):")
    print("-" * 80)
    standings = simulator.get_current_standings()
    print(f"{'Seed':<6} {'Team':<30} {'Match Record':<15} {'Map Record':<15}")
    print("-" * 80)
    for i, (team, match_rec, map_rec) in enumerate(standings, 1):
        print(f"{i:<6} {team:<30} {match_rec:<15} {map_rec:<15}")
    print()

    # Run simulations with timing
    print("=" * 80)
    print("RUNNING MONTE CARLO SIMULATION")
    print("=" * 80)

    num_sims = 1000
    print(f"Simulating remaining {upcoming} matches x {num_sims} iterations...")
    print()

    start = time.time()
    results = simulator.run_simulations(num_iterations=num_sims)
    elapsed = time.time() - start

    print(f"✓ Completed {num_sims} simulations in {elapsed:.3f} seconds")
    print(f"  - Average: {elapsed/num_sims*1000:.2f} ms per simulation")
    print(f"  - Speed: {num_sims/elapsed:.0f} simulations/second")
    print()

    # Show playoff probabilities
    print("=" * 80)
    print("PLAYOFF PROBABILITIES (Top 8 Make Playoffs)")
    print("=" * 80)

    # Sort teams by playoff probability
    playoff_probs = [(team, probs.get('make_playoffs', 0))
                     for team, probs in results.items()]
    playoff_probs.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Rank':<6} {'Team':<30} {'Playoff %':<12} {'Winners Bracket %':<20}")
    print("-" * 80)
    for i, (team, playoff_prob) in enumerate(playoff_probs, 1):
        wb_prob = results[team].get('winners_bracket', 0)
        print(f"{i:<6} {team:<30} {format_probability(playoff_prob):<12} "
              f"{format_probability(wb_prob):<20}")
    print()

    # Show detailed seeding probabilities for top 6 teams
    print("=" * 80)
    print("DETAILED SEEDING PROBABILITIES (Top 6 Teams)")
    print("=" * 80)
    print()

    for i, (team, _) in enumerate(playoff_probs[:6]):
        probs = results[team]
        print(f"{team}:")
        print(f"  Playoff Probability: {format_probability(probs.get('make_playoffs', 0))}")
        print(f"  Winners Bracket:     {format_probability(probs.get('winners_bracket', 0))}")
        print(f"  Seed Probabilities:")

        for seed in range(1, 13):
            prob = probs.get(f'seed_{seed}', 0)
            if prob > 0.01:  # Only show seeds with >1% probability
                bar_length = int(prob * 50)
                bar = "█" * bar_length
                print(f"    Seed {seed:2d}: {format_probability(prob):>6} {bar}")
        print()

    # Show most likely final standings
    print("=" * 80)
    print("MOST LIKELY FINAL SEEDING")
    print("=" * 80)
    print(f"{'Seed':<6} {'Team':<30} {'Probability':<15}")
    print("-" * 80)

    for seed in range(1, 13):
        # Find team with highest probability for this seed
        best_team = None
        best_prob = 0

        for team, probs in results.items():
            prob = probs.get(f'seed_{seed}', 0)
            if prob > best_prob:
                best_prob = prob
                best_team = team

        print(f"{seed:<6} {best_team:<30} {format_probability(best_prob):<15}")

    print()
    print("=" * 80)
    print(f"Simulation complete! ({elapsed:.3f}s for {num_sims} iterations)")
    print("=" * 80)


if __name__ == '__main__':
    main()

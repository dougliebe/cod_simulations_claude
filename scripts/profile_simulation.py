"""
Profiling script for CoD simulation performance analysis.
Measures baseline performance and identifies bottlenecks.
"""

import cProfile
import pstats
import time
from io import StringIO
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.data_loader import DataLoader
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator
from config import Config


def profile_with_cprofile(simulator, iterations=1000):
    """Profile using cProfile to identify hot spots."""
    print("=" * 80)
    print(f"PROFILING WITH cProfile ({iterations} iterations)")
    print("=" * 80)

    profiler = cProfile.Profile()
    profiler.enable()

    # Run simulation
    simulator.run_simulations(num_iterations=iterations)

    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions

    print(s.getvalue())
    print()


def benchmark_iterations(simulator):
    """Benchmark different iteration counts."""
    print("=" * 80)
    print("BENCHMARKING DIFFERENT ITERATION COUNTS")
    print("=" * 80)

    counts = [100, 500, 1000, 5000]

    for count in counts:
        start = time.perf_counter()
        simulator.run_simulations(num_iterations=count)
        elapsed = time.perf_counter() - start

        rate = count / elapsed
        per_sim = (elapsed / count) * 1000  # milliseconds

        print(f"{count:>6,} sims: {elapsed:>6.3f}s  "
              f"({rate:>7,.0f} sims/sec, {per_sim:>5.3f} ms/sim)")

    print()


def estimate_10k_performance(simulator):
    """Estimate 10k simulation performance."""
    print("=" * 80)
    print("ESTIMATING 10K SIMULATION PERFORMANCE")
    print("=" * 80)

    # Run 1000 sims to get rate
    start = time.perf_counter()
    simulator.run_simulations(num_iterations=1000)
    elapsed = time.perf_counter() - start

    rate = 1000 / elapsed

    # Estimate 10k time
    estimated_10k = 10000 / rate

    print(f"Current rate: {rate:,.0f} sims/sec")
    print(f"Estimated 10k time: {estimated_10k:.2f}s")
    print(f"Target: <2.0s")
    print(f"Speedup needed: {estimated_10k / 2.0:.1f}x")
    print()


def main():
    """Run all profiling analysis."""
    print("\n" + "=" * 80)
    print("CoD Simulation Performance Profiling")
    print("=" * 80)
    print()

    # Load data
    print("Loading data...")
    teams, matches = DataLoader.load_all_data(
        Config.MATCHES_CSV,
        Config.ELO_RATINGS_CSV,
        validate=True
    )
    print(f"✓ Loaded {len(teams)} teams and {len(matches)} matches\n")

    # Create simulator
    elo_calc = EloCalculator()
    simulator = SeasonSimulator(teams, matches, elo_calc)

    # Run benchmarks
    benchmark_iterations(simulator)

    # Estimate 10k performance
    estimate_10k_performance(simulator)

    # Run detailed profiling
    profile_with_cprofile(simulator, iterations=1000)

    print("=" * 80)
    print("Profiling complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()

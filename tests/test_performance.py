"""Performance tests for simulation speed."""

import pytest
import time
from backend.utils.data_loader import DataLoader
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator
from config import Config


class TestPerformance:
    """Test cases for simulation performance."""

    @pytest.fixture
    def full_season_simulator(self):
        """Create simulator with full 12-team season data."""
        teams, matches = DataLoader.load_all_data(
            Config.MATCHES_CSV,
            Config.ELO_RATINGS_CSV,
            validate=True
        )

        elo_calc = EloCalculator()
        return SeasonSimulator(teams, matches, elo_calc)

    def test_1000_simulations_under_2_seconds(self, full_season_simulator):
        """1000 iterations should complete in <2 seconds."""
        start = time.time()

        results = full_season_simulator.run_simulations(num_iterations=1000)

        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0, f"Took {elapsed:.2f}s, target is <2.0s"

        # Verify results are valid
        assert len(results) == 12

    def test_100_simulations_fast(self, full_season_simulator):
        """100 iterations should be very fast (<0.3s)."""
        start = time.time()

        results = full_season_simulator.run_simulations(num_iterations=100)

        elapsed = time.time() - start

        # Should complete very quickly
        assert elapsed < 0.3, f"Took {elapsed:.2f}s, target is <0.3s"

        # Verify results are valid
        assert len(results) == 12

    def test_simulation_scales_linearly(self, full_season_simulator):
        """Simulation time should scale roughly linearly with iterations."""
        # Time 100 iterations (serial mode for fair comparison)
        start = time.time()
        full_season_simulator.run_simulations(num_iterations=100, parallel=False)
        time_100 = time.time() - start

        # Time 500 iterations (serial mode for fair comparison)
        start = time.time()
        full_season_simulator.run_simulations(num_iterations=500, parallel=False)
        time_500 = time.time() - start

        # 500 iterations should take ~5x as long as 100
        # Allow 3x to 7x range (some overhead)
        ratio = time_500 / time_100
        assert 3.0 < ratio < 7.0, f"Scaling ratio: {ratio:.2f} (expected ~5x)"

    def test_current_standings_fast(self, full_season_simulator):
        """Getting current standings should be instant."""
        start = time.time()

        standings = full_season_simulator.get_current_standings()

        elapsed = time.time() - start

        # Should be nearly instant
        assert elapsed < 0.05, f"Took {elapsed:.3f}s"
        assert len(standings) == 12

    def test_single_scenario_fast(self, full_season_simulator):
        """Single scenario simulation should be very fast."""
        start = time.time()

        seeding = full_season_simulator.simulate_single_scenario()

        elapsed = time.time() - start

        # Should complete very quickly
        assert elapsed < 0.01, f"Took {elapsed:.3f}s"
        assert len(seeding) == 12

    def test_probability_calculation_performance(self, full_season_simulator):
        """Test that full season gives reasonable probabilities quickly."""
        # Run decent number of simulations
        start = time.time()

        results = full_season_simulator.run_simulations(num_iterations=500)

        elapsed = time.time() - start

        # Should be fast
        assert elapsed < 1.0, f"Took {elapsed:.2f}s"

        # All teams should have complete probability distribution
        for team_name, probs in results.items():
            total = sum(probs.get(f'seed_{i}', 0) for i in range(1, 13))
            assert 0.99 <= total <= 1.01

    @pytest.mark.slow
    def test_5000_simulations_benchmark(self, full_season_simulator):
        """Benchmark with 5000 iterations (optional slow test)."""
        start = time.time()

        results = full_season_simulator.run_simulations(num_iterations=5000)

        elapsed = time.time() - start

        print(f"\n5000 iterations completed in {elapsed:.2f}s")
        print(f"Average: {elapsed/5000*1000:.2f}ms per iteration")

        # Should complete in reasonable time
        assert elapsed < 10.0, f"Took {elapsed:.2f}s"

    def test_memory_efficiency(self, full_season_simulator):
        """Verify simulator doesn't accumulate memory across iterations."""
        import sys

        # Get baseline memory for a result
        result1 = full_season_simulator.run_simulations(num_iterations=10)
        size1 = sys.getsizeof(result1)

        # Run many more iterations
        result2 = full_season_simulator.run_simulations(num_iterations=100)
        size2 = sys.getsizeof(result2)

        # Result size should be similar (not growing with iterations)
        # Both should contain same structure (12 teams x probabilities)
        assert abs(size2 - size1) < size1 * 0.1  # Within 10%

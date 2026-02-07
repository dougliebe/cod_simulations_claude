# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Call of Duty competitive season seeding simulation tool. Allows users to explore how different match outcomes impact final playoff seeding through Monte Carlo simulation with a 7-tier tiebreaker system.

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tiebreaker.py -v

# Run performance benchmarks
pytest tests/test_performance.py -v

# Run demo simulation
python demo_simulation.py
```

### Flask API
```bash
# Start Flask development server
python app.py

# API will be available at http://localhost:5000

# API endpoints:
# GET  /api/initial-state     - Get current standings and baseline probabilities
# POST /api/simulate          - Run simulation with user-adjusted matches
# POST /api/reset             - Reset to baseline probabilities
# GET  /api/match-details/:id - Get match details and win probabilities
# GET  /api/health            - Health check
```

### Testing
```bash
# Run all tests (excluding slow benchmarks)
pytest tests/ -m "not slow"

# Run with coverage
pytest tests/ --cov=backend

# Run API tests only
pytest tests/test_api.py -v
```

## Architecture

### Backend Components

**Data Layer** (`backend/models/`)
- `team.py` - Team model with match/map records, win percentages, Elo ratings
- `match.py` - Match model for best-of-5 series validation
- `standings.py` - Standings calculator with head-to-head tracking, strength of schedule

**Simulation Engine** (`backend/simulation/`)
- `elo.py` - Elo rating calculator for win probabilities
- `match_simulator.py` - Best-of-5 map-by-map simulation using Elo
- `season_simulator.py` - Monte Carlo engine (1000+ simulations in <2s)
- `tiebreaker.py` - 7-tier tiebreaker system with recursive partial resolution

**Utilities** (`backend/utils/`)
- `data_loader.py` - CSV parsing and validation for teams and matches

**API** (`app.py`)
- Flask REST API with CORS support
- Endpoints for getting probabilities and running simulations

### Key Algorithms

**Monte Carlo Simulation** (`season_simulator.py:run_simulations`)
1. For each iteration:
   - Reset team records
   - Apply completed matches from CSV
   - Apply user-adjusted matches (if any)
   - Simulate remaining matches using Elo
   - Calculate final seeding with tiebreakers
   - Record results (playoff qualification, seed achieved)
2. Aggregate counts into probabilities

**Map-Level Elo Simulation** (`match_simulator.py:simulate_match`)
- Uses Elo rating to calculate win probability for each individual map
- Simulates best-of-5 sequentially until one team reaches 3 wins
- Returns realistic score distributions (3-0, 3-1, 3-2)

**7-Tier Tiebreaker System** (`tiebreaker.py:resolve_tie`)
1. Head-to-head match win % (skip if not all teams played)
2. Head-to-head map win % (skip if not all teams played)
3. Overall match win %
4. Overall map win %
5. Strength of schedule (match win %)
6. Strength of schedule (map win %)
7. Seed-specific rules (coin flip/tiebreaker match)

**Critical Feature**: Recursive partial resolution
- If tiebreaker splits teams into groups (e.g., 5 teams → [2 tied] + [3 tied])
- Recursively applies tiebreakers within each group
- Handles complex scenarios like circular head-to-head (A>B, B>C, C>A)

### Data Format

**matches.csv** (`data/upcoming_matches_2026_major2.csv`)
```csv
start_date,team1_id,team2_id,team1_score,team2_score
2026-03-08T00:30:00+00:00,Cloud9 New York,Boston Breach,NA,NA
2026-03-08T19:00:00+00:00,Miami Heretics,Los Angeles Thieves,3,2
```
- `NA` = match not yet played
- Scores must be valid best-of-5 (one team = 3, other ≤ 2)

**teams_elo.csv** (`data/teams_elo.csv`)
```csv
team_id,elo
OpTic Texas,1720
Atlanta FaZe,1680
```

### Configuration

All settings in `config.py`:
- `NUM_TEAMS = 12`
- `TOTAL_MATCHES = 66` (round-robin)
- `NUM_SIMULATIONS = 1000`
- `BEST_OF = 5`
- `PLAYOFF_TEAMS = 8` (top 8 make playoffs)
- `WINNERS_BRACKET_TEAMS = 6` (top 6 get winners bracket)

## Performance

- **1000 simulations in <1 second** (typically 0.7s)
- **~1,400 simulations/second**
- Full 12-team, 66-match season
- All 77+ tests pass in <2 seconds

## Common Tasks

### Add new match results
1. Update `data/upcoming_matches_2026_major2.csv` with scores
2. Restart Flask app to reload data

### Adjust simulation parameters
1. Edit `config.py`
2. Change `NUM_SIMULATIONS` (default 1000)
3. Restart Flask app

### Test tiebreaker scenarios
Use `tests/test_tiebreaker.py` as examples for creating specific scenarios

### Run performance benchmarks
```bash
pytest tests/test_performance.py::TestPerformance::test_5000_simulations_benchmark -v -s
```

## Project Structure

```
cod_simulations_claude/
├── app.py                          # Flask API entry point
├── config.py                       # Configuration
├── requirements.txt                # Python dependencies
├── data/
│   ├── teams_elo.csv              # Team Elo ratings
│   └── upcoming_matches_2026_major2.csv  # Match schedule
├── backend/
│   ├── models/                    # Data models
│   ├── simulation/                # Simulation engine
│   ├── utils/                     # Utilities
│   └── api/                       # API (currently in app.py)
├── tests/                         # Comprehensive test suite (77+ tests)
│   ├── test_elo.py
│   ├── test_match_simulator.py
│   ├── test_tiebreaker.py        # Complex tiebreaker tests
│   ├── test_season_simulator.py
│   ├── test_performance.py       # Benchmarks
│   └── test_api.py               # API endpoint tests
└── frontend/                      # (To be implemented)
    ├── static/
    └── templates/
```

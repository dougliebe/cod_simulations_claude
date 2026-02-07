# Call of Duty Seeding Simulation

Interactive web application for exploring how match outcomes impact final playoff seeding in Call of Duty competitive seasons. Uses Monte Carlo simulation with a sophisticated 7-tier tiebreaker system to calculate probability distributions for all possible seeding scenarios.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![Tests](https://img.shields.io/badge/tests-91%20passing-brightgreen.svg)
![Performance](https://img.shields.io/badge/performance-1000%20sims%2F0.7s-orange.svg)

## Features

### Interactive Web Interface
- **Probability Table**: Real-time playoff and seeding probabilities for all 12 teams
- **Match Score Editor**: Adjust upcoming match scores to explore "what-if" scenarios
- **Live Simulation**: Instant probability updates with 1000+ Monte Carlo iterations
- **Professional UI**: Dark-themed interface with color-coded probabilities and responsive design

### Sophisticated Simulation Engine
- **Map-Level Elo**: Best-of-5 matches simulated map-by-map using Elo ratings
- **7-Tier Tiebreaker System**: Handles complex tie scenarios including:
  - Head-to-head records (match and map)
  - Overall win percentages
  - Strength of schedule calculations
  - Recursive partial tie resolution
- **High Performance**: 1,400+ simulations per second (~0.7s for 1000 iterations)

### Playoff Structure
- **12 Teams**: Full round-robin (66 matches)
- **Top 8 Make Playoffs**: Seeds 1-8 qualify
- **Winners Bracket**: Seeds 1-6 start in winners bracket
- **Play-In**: Seeds 7-8 start in play-in bracket

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dougliebe/cod_simulations_claude.git
cd cod_simulations_claude

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
# Start the Flask server
python app.py

# Open your browser to http://localhost:5000
```

The application will:
1. Load team data and match schedule from CSV files
2. Compute baseline probabilities (1000 simulations)
3. Start the web server on port 5000

### Run Tests

```bash
# Run all tests (91 tests)
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run performance benchmarks
pytest tests/test_performance.py -v
```

## Usage

### Web Interface

1. **View Current Probabilities**
   - Open http://localhost:5000
   - See probability table with baseline scenarios
   - Teams ranked by current standings

2. **Adjust Match Scores**
   - Scroll to "Upcoming Matches" section
   - Enter scores (0-3) for both teams in any match
   - Boxes highlight blue when adjusted
   - Invalid scores show red border

3. **Run Simulation**
   - Click "Simulate with Adjusted Scores"
   - View updated probabilities in table
   - See simulation time and iteration count

4. **Reset**
   - Click "Reset All" to clear adjustments
   - Returns to baseline probabilities

### API Endpoints

```bash
# Get initial state and baseline probabilities
GET http://localhost:5000/api/initial-state

# Run simulation with adjusted matches
POST http://localhost:5000/api/simulate
{
  "adjusted_matches": [
    {
      "id": "match_0",
      "team1": "OpTic Texas",
      "team2": "Atlanta FaZe",
      "team1_score": 3,
      "team2_score": 1
    }
  ]
}

# Reset to baseline
POST http://localhost:5000/api/reset

# Get match details
GET http://localhost:5000/api/match-details/match_0

# Health check
GET http://localhost:5000/api/health
```

## Data Format

### Match Schedule (`data/upcoming_matches_2026_major2.csv`)

```csv
start_date,team1_id,team2_id,team1_score,team2_score
2026-03-08T00:30:00+00:00,Cloud9 New York,Boston Breach,NA,NA
2026-03-08T19:00:00+00:00,Miami Heretics,Los Angeles Thieves,3,2
```

- **Unplayed matches**: Use `NA` for both scores
- **Completed matches**: Valid best-of-5 scores (one team = 3, other ≤ 2)

### Team Elo Ratings (`data/teams_elo.csv`)

```csv
team_id,elo
OpTic Texas,1720
Atlanta FaZe,1680
LA Thieves,1650
```

## Technical Details

### Architecture

```
Frontend (Vanilla JS)
    ↓
Flask REST API (CORS enabled)
    ↓
Season Simulator (Monte Carlo)
    ↓
├─ Match Simulator (Elo-based best-of-5)
├─ Standings Calculator (records, SoS)
└─ Tiebreaker Resolver (7 tiers, recursive)
```

### Simulation Algorithm

For each of 1000+ iterations:
1. Reset all team records
2. Apply completed matches from CSV
3. Apply user-adjusted matches (if any)
4. Simulate remaining matches using Elo probabilities
5. Calculate final standings with tiebreakers
6. Record results (seed achieved, playoff qualification)

Results aggregated into probability distributions.

### 7-Tier Tiebreaker System

1. **Head-to-head match win %** (skipped if not all teams played)
2. **Head-to-head map win %** (skipped if not all teams played)
3. **Overall match win %**
4. **Overall map win %**
5. **Strength of schedule (match)**
6. **Strength of schedule (map)**
7. **Seed-specific rules** (coin flip or tiebreaker match)

**Critical Feature**: Recursive partial resolution
- When a tiebreaker separates some but not all teams
- Example: 5 teams → [1st: Team A] + [tied: Teams B,C,D] + [5th: Team E]
- Recursively resolve ties within each group

### Performance Metrics

- **1000 simulations**: ~0.7 seconds
- **Throughput**: ~1,400 simulations/second
- **Test suite**: 91 tests, all passing in <5 seconds
- **API response time**: <3 seconds (includes simulation + network)

## Configuration

Edit `config.py` to adjust parameters:

```python
NUM_TEAMS = 12                    # Teams in league
TOTAL_MATCHES = 66                # Round-robin matches
NUM_SIMULATIONS = 1000            # Iterations per simulation
BEST_OF = 5                       # Maps per match
PLAYOFF_TEAMS = 8                 # Top 8 make playoffs
WINNERS_BRACKET_TEAMS = 6         # Top 6 start in winners
ELO_K_FACTOR = 20.0              # Elo adjustment rate
```

## Project Structure

```
cod_simulations_claude/
├── app.py                        # Flask application entry point
├── config.py                     # Configuration constants
├── requirements.txt              # Python dependencies
├── data/
│   ├── teams_elo.csv            # Team Elo ratings
│   └── upcoming_matches_2026_major2.csv  # Match schedule
├── backend/
│   ├── models/
│   │   ├── team.py              # Team data model
│   │   ├── match.py             # Match data model
│   │   └── standings.py         # Standings calculator
│   ├── simulation/
│   │   ├── elo.py               # Elo probability calculator
│   │   ├── match_simulator.py   # Best-of-5 simulator
│   │   ├── season_simulator.py  # Monte Carlo engine
│   │   └── tiebreaker.py        # 7-tier tiebreaker system
│   └── utils/
│       └── data_loader.py       # CSV loader and validator
├── frontend/
│   ├── templates/
│   │   └── index.html           # Main page
│   └── static/
│       ├── css/
│       │   └── styles.css       # Styling
│       └── js/
│           ├── api.js           # API client
│           ├── table.js         # Probability table renderer
│           ├── gameBoxes.js     # Match editor
│           └── main.js          # App coordinator
└── tests/
    ├── test_elo.py              # Elo calculator tests
    ├── test_match_simulator.py  # Match simulation tests
    ├── test_tiebreaker.py       # Tiebreaker tests (complex scenarios)
    ├── test_season_simulator.py # Monte Carlo tests
    ├── test_performance.py      # Performance benchmarks
    └── test_api.py              # API endpoint tests
```

## Development

### Running Demo Scripts

```bash
# Basic simulation demo
python demo_simulation.py

# Demo with hypothetical results
python demo_with_results.py
```

### Adding New Match Results

1. Update `data/upcoming_matches_2026_major2.csv` with actual scores
2. Replace `NA` with match scores (e.g., `3,2`)
3. Restart Flask app to reload data

### Debugging

```bash
# Enable debug logging in Flask
# Edit app.py: app.run(debug=True)

# Run specific test with output
pytest tests/test_tiebreaker.py::test_partial_tie_resolution -v -s

# Performance profiling
python -m cProfile -o profile.stats demo_simulation.py
```

## Technology Stack

- **Backend**: Python 3.8+, Flask 3.0.0
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Testing**: Pytest 8.3.0
- **Data**: CSV files (pandas-free for minimal dependencies)

## License

This project is for educational and analytical purposes.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## Author

Built with Claude Code (claude.ai/code)

## Acknowledgments

- Elo rating system for competitive matchmaking
- Monte Carlo simulation methodology
- Call of Duty competitive community

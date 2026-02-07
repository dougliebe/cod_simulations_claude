# Call of Duty Seeding Simulation Website - Plan

## Initial Understanding

User wants to build a website for exploring CoD competitive regular season seeding scenarios with:

### Core Features
1. **Probability Table**: Shows current win probabilities and scenario percentages for playoffs/seeding
2. **Interactive Matchup UI**: Adjust upcoming match scores to see real-time seeding impacts

### Simulation Requirements
- Map-level simulation (best-of-5 series) using Elo scores
- Track match records and map records for tiebreakers
- Complex tiebreaker logic (7 tiers of rules)
- Performance: Must handle 1000+ simulations efficiently

### Data Input
- CSV with schedule: team1, team2, team1_score, team2_score (scores populated if complete)
- Elo scores for teams
- Current season standings

## Clarified Requirements

- **Tech Stack**: Python Flask backend + JavaScript frontend with API calls
- **Deployment**: Local Flask server, frontend makes API calls for simulations
- **League**: 12 teams, each plays 11 games (66 total matches)
- **Cutoffs**: Top 6 = winners bracket, Top 10 = play-ins, Bottom 2 = eliminated
- **Simulation**: Backend runs Monte Carlo simulation on API call when user adjusts scores
- **Data**: User provides schedule CSV and Elo ratings

## Architecture Overview

**Tech Stack**: Python Flask backend + JavaScript frontend with API calls
- Flask backend handles all simulation logic (Elo, Monte Carlo, tiebreakers)
- Frontend makes API calls when user adjusts scores
- All computation in Python for speed and maintainability

**Key Components**:
1. Elo-based map-level simulator (best-of-5 matches)
2. Monte Carlo season simulator (1000+ iterations)
3. 7-tier tiebreaker system with recursive resolution
4. Flask API endpoints for simulation requests
5. Interactive frontend for score adjustments

## Directory Structure

```
cod_simulations_claude/
├── app.py                      # Flask entry point
├── requirements.txt            # Dependencies (Flask, pytest, etc.)
├── config.py                   # Configuration constants
├── data/
│   ├── matches.csv            # Schedule: team1,team2,team1_score,team2_score
│   └── elo_ratings.csv        # Team Elo ratings
├── backend/
│   ├── simulation/
│   │   ├── elo.py            # Elo probability calculator
│   │   ├── match_simulator.py # Best-of-5 map simulation
│   │   ├── season_simulator.py # Monte Carlo engine
│   │   └── tiebreaker.py     # 7-tier tiebreaker logic
│   ├── models/
│   │   ├── team.py           # Team class (records, win %)
│   │   ├── match.py          # Match class
│   │   └── standings.py      # Standings calculator
│   ├── utils/
│   │   └── data_loader.py    # CSV validation & loading
│   └── api/
│       └── endpoints.py      # Flask route handlers
├── frontend/
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/
│   │       ├── main.js       # App initialization
│   │       ├── api.js        # API client
│   │       ├── ui.js         # Table rendering
│   │       └── scoreAdjuster.js # Score input handling
│   └── templates/
│       └── index.html
└── tests/
    ├── test_elo.py
    ├── test_match_simulator.py
    ├── test_tiebreaker.py      # Critical: validate complex logic
    ├── test_season_simulator.py
    └── test_performance.py     # Benchmark: target <2s for 1000 sims
```

## Core Algorithm Flow

### 1. Simulation Pipeline
```
User adjusts scores → POST /api/simulate → Monte Carlo (1000 iterations) → Aggregate results → Return probabilities
```

**Per Iteration**:
1. Reset team records
2. Apply completed matches (from CSV)
3. Apply user adjustments (override Elo simulation)
4. Simulate remaining matches using Elo
5. Calculate final seeding with tiebreakers
6. Record: playoffs made, seed achieved

**Aggregate Results**: Convert counts to probabilities (e.g., "made playoffs 850/1000 = 85%")

### 2. Map-Level Simulation (Best-of-5)
```python
def simulate_match(elo1, elo2):
    team1_score = team2_score = 0
    while team1_score < 3 and team2_score < 3:
        win_prob = 1 / (1 + 10^((elo2 - elo1) / 400))
        if random() < win_prob:
            team1_score += 1
        else:
            team2_score += 1
    return (team1_score, team2_score)  # e.g., (3, 1)
```

### 3. Tiebreaker System (7 Tiers)

**Recursive Algorithm**: Try each tier in order until teams are separated

**Tier 1**: Head-to-head match win % (skip if not all teams played each other)
**Tier 2**: Head-to-head map win % (skip if not all teams played each other)
**Tier 3**: Overall match win %
**Tier 4**: Overall map win %
**Tier 5**: Strength of schedule (match win %)
**Tier 6**: Strength of schedule (map win %)
**Tier 7**: Seed-specific rules
- Seeds 1/2/3/8: Tiebreaker match (use h2h or random in simulation)
- Seeds 4/9/10/11: Coin flip (random)
- Seeds 5/6/7: Higher seed chooses opponent (random in simulation)

**Critical Feature**: Partial tie resolution
- If tiebreaker splits 5 teams into [2 tied] + [3 tied], recursively resolve each group
- Example: Match win % splits [TeamA: 8-3] > [TeamB, TeamC, TeamD: 7-4] > [TeamE: 6-5]
  - TeamA ranked 1st (separated)
  - Recursively resolve TeamB/C/D for ranks 2-4
  - TeamE ranked 5th (separated)

**Strength of Schedule**: Average opponent win % (excluding games vs calculating team)

## API Endpoints

### GET /api/initial-state
Returns current standings, baseline probabilities, completed/upcoming matches, Elo ratings

### POST /api/simulate
**Request**: `{"adjusted_matches": [{"id": "match_45", "team1": "OpTic", "team2": "FaZe", "team1_score": 3, "team2_score": 1}]}`
**Response**: `{"probabilities": {...}, "simulation_time": 1.23, "iterations": 1000}`

### POST /api/reset
Clears all user adjustments

## Data Models

### Team
- name, elo_rating
- match_wins, match_losses, map_wins, map_losses
- Methods: match_win_pct(), map_win_pct(), reset_records()

### Match
- id, team1, team2, team1_score, team2_score
- Properties: is_completed(), winner()

### SeasonStandings
- teams: Dict[str, Team]
- matches: List[Match]
- Methods: calculate_seeding(), get_head_to_head_record(), calculate_strength_of_schedule()

## Testing Strategy

### Critical Tests
1. **Elo Calculator**
   - Equal ratings → 50% win probability
   - Higher Elo → >50% win probability
   - Correct formula: 1 / (1 + 10^((rating2 - rating1) / 400))

2. **Match Simulator**
   - Valid best-of-5 scores (one team = 3, other ≤ 2)
   - Higher Elo wins more frequently (statistical test over 1000 matches)

3. **Tiebreaker Logic** (Most Complex!)
   - Single tier breaks tie correctly
   - Skips h2h when teams haven't all played
   - Partial tie resolution (5 teams → 2 groups → recursive)
   - 3-way circular h2h (A>B, B>C, C>A → moves to next tier)
   - Strength of schedule calculated correctly
   - Seed-specific rules applied

4. **Season Simulator**
   - Probabilities sum to ~1.0 per team
   - Completed matches respected (same result every iteration)
   - User adjustments override Elo simulation
   - All iterations produce valid final standings

5. **Performance**
   - 1000 simulations complete in <2 seconds
   - API response time <2.5 seconds

### Edge Cases
- All 12 teams tied with identical records
- 3-way tie with circular head-to-head
- Partial season (only 10% of matches completed)
- Full season (all 66 matches completed)
- Invalid Elo ratings (negative, zero)
- Invalid match scores (4-3 in best-of-5)

## Configuration

Key parameters in `config.py`:
- NUM_TEAMS = 12
- MATCHES_PER_TEAM = 11
- TOTAL_MATCHES = 66
- NUM_SIMULATIONS = 1000
- BEST_OF = 5
- PLAYOFF_TEAMS = 8 (top 6 winners bracket, 7-8 play-in lower bracket)
- ELO_K_FACTOR = 20.0
- SIMULATION_TIMEOUT = 5.0 seconds

## CSV Formats

### matches.csv
```
team1,team2,team1_score,team2_score
OpTic Texas,Atlanta FaZe,3,1
LA Thieves,New York Subliners,3,2
Toronto Ultra,Seattle Surge,,
```
- Empty scores = match not yet played
- Scores must be valid best-of-5 (one team = 3, other ≤ 2)

### elo_ratings.csv
```
team,elo_rating
OpTic Texas,1720
Atlanta FaZe,1680
...
```

## Performance Optimizations

1. **Pre-compute head-to-head matrix** (12x12) once per iteration
2. **Use dictionaries** for O(1) team lookups
3. **Cache SOS calculations** during standings computation
4. **Profile with cProfile** to identify hotspots
5. **Optimize tiebreaker** (most complex/expensive component)

Future: Multiprocessing to parallelize iterations across CPU cores

## Frontend Features

1. **Probability Table**
   - Team name, current record (W-L matches, map differential)
   - Playoff probability (top 8)
   - Seed probabilities (1-12) with color coding
   - Winners bracket (top 6) vs play-in (7-8) vs eliminated (9-12)

2. **Match Adjuster UI**
   - List of upcoming matches
   - Win probability per match (from Elo)
   - Dropdown/input for score adjustment (0-0, 3-0, 3-1, 3-2, 2-3, 1-3, 0-3)
   - "Simulate" button triggers API call
   - Loading spinner during simulation
   - Display simulation time

3. **Current Standings**
   - Table sorted by current seeding (using tiebreakers)
   - Match record, map record

## Implementation Order

### Phase 1: Core Simulation (Priority 1)
Files to implement first:
1. `backend/simulation/elo.py` - Foundation for all probability calculations
2. `backend/simulation/match_simulator.py` - Map-by-map best-of-5 simulation
3. `backend/models/team.py`, `backend/models/match.py` - Data structures
4. `backend/utils/data_loader.py` - CSV loading & validation
5. `tests/test_elo.py`, `tests/test_match_simulator.py` - Validate core logic

### Phase 2: Tiebreaker System (Priority 2)
6. `backend/simulation/tiebreaker.py` - Most complex component, implement carefully
7. `backend/models/standings.py` - Standings calculator with SOS
8. `tests/test_tiebreaker.py` - Comprehensive edge case testing

### Phase 3: Season Simulator (Priority 3)
9. `backend/simulation/season_simulator.py` - Orchestrates Monte Carlo
10. `tests/test_season_simulator.py` - End-to-end simulation tests
11. `tests/test_performance.py` - Benchmark and optimize

### Phase 4: Flask Backend (Priority 4)
12. `app.py` - Flask application setup
13. `backend/api/endpoints.py` - API routes
14. `config.py` - Configuration management
15. `tests/test_api.py` - API endpoint tests

### Phase 5: Frontend (Priority 5)
16. `frontend/templates/index.html` - HTML structure
17. `frontend/static/css/styles.css` - Styling
18. `frontend/static/js/api.js` - API client
19. `frontend/static/js/ui.js` - Table rendering
20. `frontend/static/js/scoreAdjuster.js` - Score inputs
21. `frontend/static/js/main.js` - App initialization

### Phase 6: Polish (Priority 6)
22. Update `CLAUDE.md` with commands and architecture
23. Add comprehensive README.md
24. Performance profiling and optimization
25. UI/UX improvements

## Verification Plan

After implementation, verify end-to-end:

1. **Data Loading**: Load matches.csv and elo_ratings.csv successfully
2. **Baseline Simulation**: Run 1000 simulations with no adjustments, verify probabilities sum to 1.0
3. **Manual Test Case**: Create scenario with known outcome (e.g., 3 teams tied, TeamA beat both h2h) → verify TeamA ranks highest
4. **UI Test**: Adjust a match score → verify probability table updates correctly
5. **Performance**: Benchmark 1000 simulations complete in <2 seconds
6. **Edge Cases**: Test all tiebreaker edge cases from test suite

## Key Decisions & Tradeoffs

1. **Flask + API over static**: Allows Python for simulation (faster than JS), easier testing
2. **Monte Carlo over analytical**: Some scenarios too complex to calculate analytically (circular h2h, multi-way ties)
3. **Recursive tiebreakers**: Handles partial tie resolution elegantly
4. **Best-of-5 map-level**: More accurate than match-level Elo (accounts for variance)
5. **Pre-compute nothing**: Real-time simulation gives full flexibility, fast enough with optimized Python

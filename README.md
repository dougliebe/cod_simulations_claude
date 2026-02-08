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

**See detailed implementation breakdown in the [Tiebreaker System Deep Dive](#tiebreaker-system-deep-dive) section below.**

### Performance Metrics

- **1000 simulations**: ~0.7 seconds
- **Throughput**: ~1,400 simulations/second
- **Test suite**: 91 tests, all passing in <5 seconds
- **API response time**: <3 seconds (includes simulation + network)

## Tiebreaker System Deep Dive

This section provides a complete breakdown of how the 7-tier tiebreaker system is implemented, including inputs, outputs, code examples, and edge case handling.

### Overview

The tiebreaker system (`backend/simulation/tiebreaker.py`) is invoked at the end of each simulation iteration to convert team records into final seeding positions (1st through 12th). It implements a cascading 7-tier system where each tier attempts to break ties, and if teams remain tied, the next tier is applied.

### Inputs and Outputs

**Inputs (from `SeasonStandings`):**
- `teams`: Dictionary of `Team` objects with match/map records
- `matches`: List of `Match` objects (both completed and upcoming)
- Team records updated via `standings.update_team_records_from_matches()`

**Outputs:**
- `List[str]`: Ordered list of team names from 1st seed to 12th seed

**Entry Point:**
```python
# Called from season_simulator.py after all matches simulated
resolver = TiebreakerResolver(standings)
final_seeding = resolver.calculate_seeding()
# Returns: ['OpTic Texas', 'Atlanta FaZe', 'LA Thieves', ...]
```

### Step-by-Step Implementation

#### Initial Grouping

Before applying tiebreakers, teams are grouped by their match win percentage:

```python
# From tiebreaker.py:28-36
def calculate_seeding(self) -> List[str]:
    # Start with teams grouped by match win percentage
    groups = self.standings.group_teams_by_record(use_maps=False)
    # groups might look like:
    # [['Team A'], ['Team B', 'Team C', 'Team D'], ['Team E', 'Team F'], ...]

    final_seeding = []
    for group in groups:
        resolved = self.resolve_tie(group)  # Apply tiebreakers to each group
        final_seeding.extend(resolved)

    return final_seeding
```

**Key Implementation Detail (`standings.py:206-238`):**
```python
def group_teams_by_record(self, use_maps: bool = False) -> List[List[str]]:
    groups = []
    current_group = []
    current_pct = None

    for team in self.get_teams_by_record(use_maps):
        pct = self.teams[team].map_win_pct if use_maps else self.teams[team].match_win_pct

        # Floating point tolerance check
        if current_pct is None or abs(pct - current_pct) < 0.0001:
            current_group.append(team)
            current_pct = pct
        else:
            if current_group:
                groups.append(current_group)
            current_group = [team]
            current_pct = pct

    if current_group:
        groups.append(current_group)

    return groups
```

**Edge Case Handled:** Uses `abs(pct - current_pct) < 0.0001` to avoid floating-point precision issues when comparing win percentages.

---

#### Tier 1: Head-to-Head Match Win Percentage

**Rule:** Among tied teams, the one with the best match win percentage in games between ONLY these teams wins.

**Implementation (`tiebreaker.py:83-105`):**
```python
def _apply_tier1_h2h_match_pct(self, teams: List[str]) -> Optional[List[str]]:
    # CRITICAL: Skip if not all teams played each other
    if not self.standings.all_teams_played_each_other(teams):
        return None  # Move to next tier

    # Calculate h2h match records (wins, losses)
    h2h_records = self.standings.get_head_to_head_record(teams, use_maps=False)
    # Returns: {'Team A': (2, 0), 'Team B': (1, 1), 'Team C': (0, 2)}

    # Calculate win percentages
    win_pcts = {}
    for team, (wins, losses) in h2h_records.items():
        total = wins + losses
        win_pcts[team] = wins / total if total > 0 else 0.0

    # Sort by h2h win percentage (descending)
    sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)

    # Handle partial separation (see below)
    return self._handle_partial_separation(sorted_teams, win_pcts)
```

**Validation Check (`standings.py:43-70`):**
```python
def all_teams_played_each_other(self, team_names: List[str]) -> bool:
    if len(team_names) < 2:
        return True

    # Build set of required matchups
    required_matchups: Set[FrozenSet[str]] = set()
    for i, team1 in enumerate(team_names):
        for team2 in team_names[i + 1:]:
            required_matchups.add(frozenset([team1, team2]))
    # For 3 teams: {frozenset({'A','B'}), frozenset({'A','C'}), frozenset({'B','C'})}

    # Check actual matchups from completed matches
    actual_matchups: Set[FrozenSet[str]] = set()
    for match in self.get_head_to_head_matches(team_names):
        actual_matchups.add(frozenset([match.team1, match.team2]))

    # All required matchups must exist
    return required_matchups.issubset(actual_matchups)
```

**Example Scenario:**
```python
# 3 teams tied at 5-6 overall
# H2H results: A beat B (3-0), B beat C (3-1), A beat C (3-2)
# H2H records: A (2-0), B (1-1), C (0-2)
# Win %: A (100%), B (50%), C (0%)
# Result: ['Team A', 'Team B', 'Team C']
```

**Edge Case: Circular Head-to-Head**
```python
# A > B (3-0), B > C (3-1), C > A (3-2)
# H2H records: A (1-1), B (1-1), C (1-1)
# All teams have 50% h2h win rate → No separation → Returns None → Move to Tier 2
```

---

#### Tier 2: Head-to-Head Map Win Percentage

**Rule:** Same as Tier 1, but uses individual map wins/losses instead of match wins/losses.

**Implementation (`tiebreaker.py:107-129`):**
```python
def _apply_tier2_h2h_map_pct(self, teams: List[str]) -> Optional[List[str]]:
    if not self.standings.all_teams_played_each_other(teams):
        return None

    # Calculate h2h MAP records
    h2h_records = self.standings.get_head_to_head_record(teams, use_maps=True)
    # Returns: {'Team A': (5, 3), 'Team B': (4, 7), 'Team C': (3, 6)}

    win_pcts = {}
    for team, (wins, losses) in h2h_records.items():
        total = wins + losses
        win_pcts[team] = wins / total if total > 0 else 0.0

    sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)
    return self._handle_partial_separation(sorted_teams, win_pcts)
```

**Map Record Calculation (`standings.py:92-97`):**
```python
for match in h2h_matches:
    if use_maps:
        # Map-level record
        wins1, losses1 = records[match.team1]
        wins2, losses2 = records[match.team2]

        records[match.team1] = (wins1 + match.team1_score, losses1 + match.team2_score)
        records[match.team2] = (wins2 + match.team2_score, losses2 + match.team1_score)
```

**Example Scenario (Circular Tiebreaker Resolution):**
```python
# A > B (3-0), B > C (3-1), C > A (3-2)
# Tier 1 fails (all 1-1 in matches)
# Map records in h2h:
#   A: 3 + 2 = 5 maps won, 0 + 3 = 3 maps lost → 5/8 = 62.5%
#   B: 3 + 1 = 4 won, 0 + 3 = 3 lost → 4/7 = 57.1%
#   C: 3 + 0 = 3 won, 1 + 2 = 3 lost → 3/6 = 50%
# Result: ['Team A', 'Team B', 'Team C']
```

---

#### Tier 3: Overall Match Win Percentage

**Rule:** Compare overall match records (including games outside the tied group).

**Implementation (`tiebreaker.py:131-145`):**
```python
def _apply_tier3_overall_match_pct(self, teams: List[str]) -> Optional[List[str]]:
    # Get OVERALL match win percentages (pre-calculated in Team objects)
    win_pcts = {
        team: self.standings.teams[team].match_win_pct
        for team in teams
    }
    # Team.match_win_pct = match_wins / (match_wins + match_losses)

    sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)
    return self._handle_partial_separation(sorted_teams, win_pcts)
```

**When This Tier Applies:**
- Teams haven't all played each other (Tier 1/2 skipped)
- OR Tier 1/2 couldn't separate teams

**Example Scenario:**
```python
# Team A vs Team B (never played each other)
# A: 7-4 overall (63.6%), B: 6-5 overall (54.5%)
# Result: ['Team A', 'Team B']
```

---

#### Tier 4: Overall Map Win Percentage

**Rule:** Compare overall map records.

**Implementation (`tiebreaker.py:147-161`):**
```python
def _apply_tier4_overall_map_pct(self, teams: List[str]) -> Optional[List[str]]:
    win_pcts = {
        team: self.standings.teams[team].map_win_pct
        for team in teams
    }
    # Team.map_win_pct = map_wins / (map_wins + map_losses)

    sorted_teams = sorted(teams, key=lambda t: win_pcts[t], reverse=True)
    return self._handle_partial_separation(sorted_teams, win_pcts)
```

**Example Scenario:**
```python
# Both teams 5-5 in matches (50%)
# A: 18-17 in maps (51.4%), B: 16-19 in maps (45.7%)
# Result: ['Team A', 'Team B']
```

---

#### Tier 5: Strength of Schedule (Match Win %)

**Rule:** Average win percentage of all opponents faced.

**Implementation (`tiebreaker.py:163-177`):**
```python
def _apply_tier5_sos_match(self, teams: List[str]) -> Optional[List[str]]:
    # Calculate SOS for each team
    sos_values = {
        team: self.standings.calculate_strength_of_schedule(team, use_maps=False)
        for team in teams
    }

    sorted_teams = sorted(teams, key=lambda t: sos_values[t], reverse=True)
    return self._handle_partial_separation(sorted_teams, sos_values)
```

**SOS Calculation (`standings.py:111-152`):**
```python
def calculate_strength_of_schedule(self, team_name: str, use_maps: bool = False) -> float:
    # Find all opponents
    opponents = []
    for match in self.get_completed_matches():
        if match.team1 == team_name:
            opponents.append(match.team2)
        elif match.team2 == team_name:
            opponents.append(match.team1)

    if not opponents:
        return 0.0

    # Calculate win percentage for each opponent using their full record
    opponent_win_pcts = []
    for opp in opponents:
        opp_team = self.teams[opp]

        if use_maps:
            win_pct = opp_team.map_win_pct
        else:
            win_pct = opp_team.match_win_pct

        opponent_win_pcts.append(win_pct)

    # Return average opponent win percentage
    return sum(opponent_win_pcts) / len(opponent_win_pcts)
```

**Example Scenario:**
```python
# Team A: beat Team Strong (8-3), lost to Team Weak (2-9)
# Team B: beat Team Weak (2-9), lost to Team Strong (8-3)
#
# SOS for A: (Strong: 8/11 + Weak: 2/11) / 2 = (0.727 + 0.182) / 2 = 0.455
# SOS for B: (Weak: 2/11 + Strong: 8/11) / 2 = (0.182 + 0.727) / 2 = 0.455
# TIED → No separation → Move to Tier 6
```

**Implementation Note:** SOS uses each opponent's full win percentage (including games against the team being evaluated). This is simpler than excluding specific games and matches standard practice in most sports leagues.

---

#### Tier 6: Strength of Schedule (Map Win %)

**Rule:** Same as Tier 5, but uses map win percentage of opponents.

**Implementation (`tiebreaker.py:179-193`):**
```python
def _apply_tier6_sos_map(self, teams: List[str]) -> Optional[List[str]]:
    sos_values = {
        team: self.standings.calculate_strength_of_schedule(team, use_maps=True)
        for team in teams
    }

    sorted_teams = sorted(teams, key=lambda t: sos_values[t], reverse=True)
    return self._handle_partial_separation(sorted_teams, sos_values)
```

**When This Applies:** Teams have identical overall records AND identical match-based SOS, but different map-based SOS.

---

#### Tier 7: Seed-Specific Rules (Random)

**Rule:** If all 6 previous tiers fail to separate teams, use seed-specific rules (coin flip for most seeds, tiebreaker match for specific seeds).

**Implementation (`tiebreaker.py:195-209`):**
```python
def _apply_tier7_seed_specific(self, teams: List[str]) -> List[str]:
    """
    Tier 7: Seed-specific rules.

    - Seeds 1/2/3/8: Tiebreaker match (simulated as random for now)
    - Seeds 4/9/10/11: Coin flip (random)
    - Other seeds: Random or higher seed chooses

    For simulation purposes, use random selection.
    """
    shuffled = list(teams)
    random.shuffle(shuffled)  # Simulates coin flip/random selection
    return shuffled
```

**Note:** This tier ALWAYS returns a result (never `None`), guaranteeing the recursive tiebreaker eventually terminates.

---

### Recursive Partial Resolution

The most critical feature of the tiebreaker system is its ability to handle **partial separation** — when a tiebreaker separates SOME teams but leaves others tied.

**Implementation (`tiebreaker.py:211-263`):**
```python
def _handle_partial_separation(
    self,
    sorted_teams: List[str],
    metric_values: Dict[str, float]
) -> Optional[List[str]]:
    """
    Handle case where tiebreaker partially separates teams.

    If tiebreaker creates groups (some teams tied, some separated),
    recursively resolve ties within each group.
    """
    # Group teams by metric value (with floating point tolerance)
    groups = []
    current_group = [sorted_teams[0]]
    current_value = metric_values[sorted_teams[0]]

    for team in sorted_teams[1:]:
        value = metric_values[team]

        if abs(value - current_value) < 1e-9:  # Floating point tolerance
            current_group.append(team)  # Same value → tied
        else:
            # Different value → finalize current group, start new one
            groups.append(current_group)
            current_group = [team]
            current_value = value

    groups.append(current_group)  # Add last group

    # If only one group, NO separation occurred
    if len(groups) == 1:
        return None  # Try next tier

    # Partial or full separation occurred
    # Recursively resolve ties within each group
    resolved = []
    for group in groups:
        if len(group) == 1:
            resolved.extend(group)  # No tie
        else:
            # RECURSIVE CALL: Restart tiebreaker process for this subgroup
            resolved.extend(self.resolve_tie(group))

    return resolved
```

**Example: 5-Way Tie Partial Resolution**
```python
# Initial: ['A', 'B', 'C', 'D', 'E'] all tied at 5-6 overall
#
# Tier 3 (overall match %): All 5-6 (45.5%) → No separation
# Tier 4 (overall map %):
#   A: 20-16 (55.5%)
#   B: 18-18 (50%)
#   C: 18-18 (50%)
#   D: 18-18 (50%)
#   E: 16-20 (44.4%)
#
# Groups formed: [[A], [B, C, D], [E]]
#
# Result after recursive resolution:
#   1. A → No tie
#   2. resolve_tie([B, C, D]) → (recursive call, tries Tier 1-7 again on just these 3)
#   3. E → No tie
```

**Recursive Call Flow:**
```
resolve_tie(['B', 'C', 'D'])
  → Tier 1 (h2h match %): B beat C, C beat D, D beat B → All 1-1 → None
  → Tier 2 (h2h map %): B (6 maps), C (5 maps), D (4 maps) → ['B', 'C', 'D']

Final seeding: ['A', 'B', 'C', 'D', 'E']
```

---

### Edge Cases and Special Handling

#### 1. Floating-Point Precision

**Problem:** Win percentages are floats (e.g., 0.545454...), which can have precision issues.

**Solution:** Use tolerance checks throughout:
```python
# In group_teams_by_record (standings.py:223)
if current_pct is None or abs(pct - current_pct) < 0.0001:

# In _handle_partial_separation (tiebreaker.py:237)
if abs(value - current_value) < 1e-9:
```

#### 2. Teams Haven't Played Each Other

**Problem:** Can't use head-to-head tiebreakers if teams haven't all played each other.

**Solution:** Validation check returns `None`, skipping to next tier:
```python
if not self.standings.all_teams_played_each_other(teams):
    return None
```

**Test Case (`test_tiebreaker.py:233-253`):**
```python
# Only A vs B played, missing A-C and B-C matchups
matches = [Match('m1', 'Team A', 'Team B', 3, 1)]

result = resolver._apply_tier1_h2h_match_pct(['Team A', 'Team B', 'Team C'])
assert result is None  # Skips tier
```

#### 3. Circular Head-to-Head

**Problem:** A beats B, B beats C, C beats A → All have 1-1 h2h record.

**Solution:** Tier 1 returns `None` (no separation), moves to Tier 2 (map percentage).

**Test Case (`test_tiebreaker.py:54-85`):**
```python
matches = [
    Match('m1', 'Team A', 'Team B', 3, 0),  # A > B
    Match('m2', 'Team B', 'Team C', 3, 1),  # B > C
    Match('m3', 'Team C', 'Team A', 3, 2),  # C > A (circular!)
]

# Tier 1 can't separate (all 1-1)
# Tier 2 uses map %: A (5-3), B (4-3), C (3-3)
result = resolver.resolve_tie(['Team A', 'Team B', 'Team C'])
assert result[0] == 'Team A'
```

#### 4. No Matches Played (All 0-0)

**Problem:** New season with no matches → all teams 0-0 in every metric.

**Solution:** Falls through to Tier 7 (random):
```python
matches = []  # No matches
result = resolver.resolve_tie(['Team A', 'Team B', 'Team C', 'Team D'])
# Returns random ordering
assert len(result) == 4
assert set(result) == {'Team A', 'Team B', 'Team C', 'Team D'}
```

#### 5. Division by Zero in Win Percentages

**Problem:** Team has no matches → `0 / 0` when calculating win percentage.

**Solution:** Explicit zero-check in every percentage calculation:
```python
total = wins + losses
win_pcts[team] = wins / total if total > 0 else 0.0
```

#### 6. Multiple Recursion Levels

**Problem:** Partial separation can occur at multiple levels.

**Example:**
```
Initial: [A, B, C, D, E, F, G, H] all tied
Tier 4 → [[A, B], [C, D, E], [F], [G, H]]
  resolve_tie([A, B]) → Tier 5 → [[A], [B]]
  resolve_tie([C, D, E]) → Tier 2 → [[C], [D, E]]
    resolve_tie([D, E]) → Tier 7 → random
  resolve_tie([G, H]) → Tier 1 → [[G], [H]]
```

**Solution:** Recursive algorithm naturally handles this:
```python
for group in groups:
    if len(group) == 1:
        resolved.extend(group)
    else:
        resolved.extend(self.resolve_tie(group))  # Recursive call
```

---

### Testing and Validation

The tiebreaker system has **comprehensive test coverage** in `tests/test_tiebreaker.py`:

- **Basic tier tests**: Each tier independently tested
- **Circular tiebreaker**: A>B>C>A scenario
- **Partial resolution**: 5-team tie splitting into sub-groups
- **Edge cases**: No matches, missing matchups, all identical records
- **SOS calculation**: Correct opponent record exclusion
- **Full integration**: Complete seeding calculation

Run tests:
```bash
pytest tests/test_tiebreaker.py -v
```

Expected output: All tests passing, demonstrating correct handling of all scenarios.

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

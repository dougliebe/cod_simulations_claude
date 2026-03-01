"""Flask application entry point for CoD simulation API."""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from backend.utils.data_loader import DataLoader
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator
from backend.models.match import Match
from backend.models.team import Team
from config import Config
import time

# Create Flask app
app = Flask(__name__,
            static_folder='frontend/static',
            template_folder='frontend/templates')
app.config.from_object(Config)

# Enable CORS for frontend requests
CORS(app)

# Load data on startup
print("Loading data...")
teams, matches = DataLoader.load_all_data(
    Config.MATCHES_CSV,
    Config.ELO_RATINGS_CSV,
    validate=True
)
print(f"✓ Loaded {len(teams)} teams and {len(matches)} matches")

# Equal-elo teams (all 1500) for toggle - records are computed from matches
teams_equal_elo = {name: Team(name=name, elo_rating=Config.DEFAULT_ELO) for name in teams}

# Initialize simulators for both Elo modes
elo_calc = EloCalculator(k_factor=Config.ELO_K_FACTOR)
simulator = SeasonSimulator(teams, matches, elo_calc)
simulator_equal_elo = SeasonSimulator(teams_equal_elo, matches, elo_calc)

# Store baseline results (lazy init per mode)
baseline_result = None
baseline_result_equal_elo = None
baseline_simulation_time = None
baseline_simulation_time_equal_elo = None

def get_simulator(use_equal_elo: bool):
    """Return simulator for the given Elo mode."""
    return simulator_equal_elo if use_equal_elo else simulator

def get_teams(use_equal_elo: bool):
    """Return teams for the given Elo mode."""
    return teams_equal_elo if use_equal_elo else teams

def get_baseline_result(use_equal_elo: bool = False):
    """Get full baseline result (probabilities + cutoffs) for the given Elo mode."""
    global baseline_result, baseline_result_equal_elo, baseline_simulation_time, baseline_simulation_time_equal_elo
    sim = get_simulator(use_equal_elo)
    if use_equal_elo:
        if baseline_result_equal_elo is None:
            print("Computing baseline probabilities (equal Elo)...")
            start_time = time.time()
            baseline_result_equal_elo = sim.run_simulations(Config.NUM_SIMULATIONS, parallel=True)
            baseline_simulation_time_equal_elo = time.time() - start_time
            print(f"✓ Baseline (equal Elo) computed in {baseline_simulation_time_equal_elo:.3f}s")
        return baseline_result_equal_elo, baseline_simulation_time_equal_elo
    else:
        if baseline_result is None:
            print("Computing baseline probabilities...")
            start_time = time.time()
            baseline_result = sim.run_simulations(Config.NUM_SIMULATIONS, parallel=True)
            baseline_simulation_time = time.time() - start_time
            print(f"✓ Baseline probabilities computed in {baseline_simulation_time:.3f}s")
        return baseline_result, baseline_simulation_time

def recompute_baseline_probabilities(use_equal_elo: bool = False):
    """Force recomputation of baseline probabilities for the given Elo mode."""
    global baseline_result, baseline_result_equal_elo, baseline_simulation_time, baseline_simulation_time_equal_elo
    sim = get_simulator(use_equal_elo)
    print(f"Recomputing baseline probabilities ({'equal Elo' if use_equal_elo else 'CSV Elo'})...")
    start_time = time.time()
    result = sim.run_simulations(Config.NUM_SIMULATIONS, parallel=True)
    elapsed = time.time() - start_time
    if use_equal_elo:
        baseline_result_equal_elo = result
        baseline_simulation_time_equal_elo = elapsed
    else:
        baseline_result = result
        baseline_simulation_time = elapsed
    print(f"✓ Baseline recomputed in {elapsed:.3f}s")
    return result["probabilities"]


@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template('index.html')


@app.route('/api/initial-state', methods=['GET'])
def get_initial_state():
    """
    Get initial state with current standings and baseline probabilities.

    Query params:
        use_equal_elo: 'true' to use equal Elo (1500) for all teams instead of CSV values

    Returns:
        JSON with teams, probabilities, matches, and Elo ratings
    """
    use_equal_elo = request.args.get('use_equal_elo', 'false').lower() == 'true'
    sim = get_simulator(use_equal_elo)
    teams_for_mode = get_teams(use_equal_elo)
    baseline, sim_time = get_baseline_result(use_equal_elo)

    # Get current standings
    current_standings = sim.get_current_standings()

    # Format teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        team = teams_for_mode[team_name]
        teams_data.append({
            'name': team.name,
            'match_wins': team.match_wins,
            'match_losses': team.match_losses,
            'map_wins': team.map_wins,
            'map_losses': team.map_losses,
            'match_record': match_record,
            'map_record': map_record,
            'elo_rating': team.elo_rating
        })

    # Format matches data
    completed_matches = [
        {
            'id': m.id,
            'team1': m.team1,
            'team2': m.team2,
            'team1_score': m.team1_score,
            'team2_score': m.team2_score,
            'start_date': m.start_date
        }
        for m in matches if m.is_completed
    ]

    upcoming_matches = [
        {
            'id': m.id,
            'team1': m.team1,
            'team2': m.team2,
            'team1_score': None,
            'team2_score': None,
            'start_date': m.start_date,
            'win_probability_team1': sim.get_match_win_probability(m.team1, m.team2)
        }
        for m in matches if not m.is_completed
    ]

    elo_ratings = {team.name: team.elo_rating for team in teams_for_mode.values()}

    return jsonify({
        'teams': teams_data,
        'probabilities': baseline['probabilities'],
        'completed_matches': completed_matches,
        'upcoming_matches': upcoming_matches,
        'elo_ratings': elo_ratings,
        'num_simulations': Config.NUM_SIMULATIONS,
        'simulation_time': sim_time or 0,
        'use_equal_elo': use_equal_elo,
        'median_bracket_cutoff': baseline.get('median_bracket_cutoff'),
        'median_playin_cutoff': baseline.get('median_playin_cutoff'),
    })


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Run simulation with user-adjusted match results.

    Request body:
        {
            "adjusted_matches": [
                {"id": "match_1", "team1": "OpTic", "team2": "FaZe", "team1_score": 3, "team2_score": 1}
            ]
        }

    Returns:
        JSON with updated probabilities and simulation metadata
    """
    data = request.get_json()

    if not data or 'adjusted_matches' not in data:
        return jsonify({'error': 'Missing adjusted_matches in request body'}), 400

    # Parse adjusted matches
    adjusted_matches = []
    for match_data in data['adjusted_matches']:
        try:
            match = Match(
                id=match_data.get('id', ''),
                team1=match_data['team1'],
                team2=match_data['team2'],
                team1_score=match_data.get('team1_score'),
                team2_score=match_data.get('team2_score'),
                start_date=match_data.get('start_date', '')
            )

            # Validate score if provided
            if match.is_completed and not match.is_valid_score():
                return jsonify({
                    'error': f'Invalid score for {match.team1} vs {match.team2}: '
                            f'{match.team1_score}-{match.team2_score}'
                }), 400

            adjusted_matches.append(match)
        except KeyError as e:
            return jsonify({'error': f'Missing required field: {str(e)}'}), 400

    use_equal_elo = data.get('use_equal_elo', False)
    sim = get_simulator(use_equal_elo)
    teams_for_mode = get_teams(use_equal_elo)

    # Choose simulation method: auto | monte_carlo | exhaustive
    # Only apply auto threshold (exhaustive vs MC) when we would use MC - i.e. when method is auto or monte_carlo
    simulation_method_param = (data.get('simulation_method') or 'auto').lower()
    remaining_count = sim.get_remaining_match_count(adjusted_matches)
    total_scenarios = 6 ** remaining_count
    use_exhaustive = (
        simulation_method_param == 'exhaustive'
        or (
            simulation_method_param in ('auto', 'monte_carlo')
            and total_scenarios < Config.EXHAUSTIVE_MAX_SCENARIOS
        )
    )

    # Run simulation with adjustments
    start_time = time.time()
    simulation_method = 'exhaustive'
    iterations = total_scenarios
    try:
        if use_exhaustive:
            sim_result = sim.run_exhaustive_simulations(
                adjusted_matches=adjusted_matches
            )
        else:
            sim_result = sim.run_simulations(
                num_iterations=Config.NUM_SIMULATIONS,
                adjusted_matches=adjusted_matches
            )
            simulation_method = 'monte_carlo'
            iterations = Config.NUM_SIMULATIONS
    except ValueError:
        # Fallback to Monte Carlo only when we were trying to use exhaustive due to MC-mode logic
        if simulation_method_param in ('auto', 'monte_carlo'):
            sim_result = sim.run_simulations(
                num_iterations=Config.NUM_SIMULATIONS,
                adjusted_matches=adjusted_matches
            )
            simulation_method = 'monte_carlo'
            iterations = Config.NUM_SIMULATIONS
        else:
            raise
    elapsed = time.time() - start_time
    probabilities = sim_result['probabilities']

    # Get updated standings with adjusted matches applied
    current_standings = sim.get_current_standings(adjusted_matches=adjusted_matches)

    # Format updated teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        team = teams_for_mode[team_name]

        # Parse match record to get wins/losses
        match_parts = match_record.split('-')
        match_wins = int(match_parts[0])
        match_losses = int(match_parts[1])

        # Parse map record to get wins/losses
        map_parts = map_record.split('-')
        map_wins = int(map_parts[0])
        map_losses = int(map_parts[1])

        teams_data.append({
            'name': team_name,
            'match_wins': match_wins,
            'match_losses': match_losses,
            'map_wins': map_wins,
            'map_losses': map_losses,
            'match_record': match_record,
            'map_record': map_record,
            'elo_rating': team.elo_rating
        })

    return jsonify({
        'probabilities': probabilities,
        'teams': teams_data,
        'simulation_time': round(elapsed, 3),
        'simulation_method': simulation_method,
        'iterations': iterations,
        'total_scenarios': total_scenarios if simulation_method == 'exhaustive' else None,
        'median_bracket_cutoff': sim_result.get('median_bracket_cutoff'),
        'median_playin_cutoff': sim_result.get('median_playin_cutoff'),
        'use_equal_elo': use_equal_elo,
    })


@app.route('/api/reset', methods=['POST'])
def reset():
    """
    Reset to baseline probabilities (no user adjustments).

    Request body: { "use_equal_elo": false } (optional)
    """
    data = request.get_json(silent=True) or {}
    use_equal_elo = data.get('use_equal_elo', False)
    sim = get_simulator(use_equal_elo)
    teams_for_mode = get_teams(use_equal_elo)
    baseline, sim_time = get_baseline_result(use_equal_elo)

    # Get original standings (no adjustments)
    current_standings = sim.get_current_standings()

    # Format teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        team = teams_for_mode[team_name]
        match_parts = match_record.split('-')
        map_parts = map_record.split('-')
        teams_data.append({
            'name': team_name,
            'match_wins': int(match_parts[0]),
            'match_losses': int(match_parts[1]),
            'map_wins': int(map_parts[0]),
            'map_losses': int(map_parts[1]),
            'match_record': match_record,
            'map_record': map_record,
            'elo_rating': team.elo_rating
        })

    return jsonify({
        'status': 'success',
        'message': 'Reset to baseline probabilities',
        'probabilities': baseline['probabilities'],
        'teams': teams_data,
        'simulation_time': sim_time,
        'iterations': Config.NUM_SIMULATIONS,
        'median_bracket_cutoff': baseline.get('median_bracket_cutoff'),
        'median_playin_cutoff': baseline.get('median_playin_cutoff'),
        'use_equal_elo': use_equal_elo,
    })


@app.route('/api/recompute-baseline', methods=['POST'])
def recompute_baseline():
    """
    Force recomputation of baseline probabilities.

    Request body: { "use_equal_elo": false } (optional)
    """
    data = request.get_json(silent=True) or {}
    use_equal_elo = data.get('use_equal_elo', False)
    sim = get_simulator(use_equal_elo)
    teams_for_mode = get_teams(use_equal_elo)

    # Force recomputation
    recompute_baseline_probabilities(use_equal_elo)
    baseline, sim_time = get_baseline_result(use_equal_elo)

    # Get current standings
    current_standings = sim.get_current_standings()

    # Format teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        team = teams_for_mode[team_name]

        # Parse match record
        match_parts = match_record.split('-')
        match_wins = int(match_parts[0])
        match_losses = int(match_parts[1])

        # Parse map record
        map_parts = map_record.split('-')
        map_wins = int(map_parts[0])
        map_losses = int(map_parts[1])

        teams_data.append({
            'name': team_name,
            'match_wins': match_wins,
            'match_losses': match_losses,
            'map_wins': map_wins,
            'map_losses': map_losses,
            'match_record': match_record,
            'map_record': map_record,
            'elo_rating': team.elo_rating
        })

    return jsonify({
        'status': 'success',
        'message': 'Baseline probabilities recomputed',
        'probabilities': baseline['probabilities'],
        'teams': teams_data,
        'simulation_time': sim_time,
        'iterations': Config.NUM_SIMULATIONS,
        'median_bracket_cutoff': baseline.get('median_bracket_cutoff'),
        'median_playin_cutoff': baseline.get('median_playin_cutoff'),
        'use_equal_elo': use_equal_elo,
    })


@app.route('/api/match-details/<match_id>', methods=['GET'])
def get_match_details(match_id):
    """
    Get detailed information about a specific match.

    Args:
        match_id: Match identifier

    Returns:
        JSON with match details and win probabilities
    """
    # Find the match
    match = None
    for m in matches:
        if m.id == match_id:
            match = m
            break

    if not match:
        return jsonify({'error': f'Match {match_id} not found'}), 404

    # Get win probability
    win_prob_team1 = simulator.get_match_win_probability(match.team1, match.team2)

    return jsonify({
        'match_id': match.id,
        'team1': match.team1,
        'team2': match.team2,
        'team1_score': match.team1_score,
        'team2_score': match.team2_score,
        'start_date': match.start_date,
        'is_completed': match.is_completed,
        'win_probability_team1': win_prob_team1,
        'win_probability_team2': 1 - win_prob_team1
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'teams_loaded': len(teams),
        'matches_loaded': len(matches),
        'simulations_per_request': Config.NUM_SIMULATIONS
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("CoD Seeding Simulation API")
    print("=" * 80)
    print(f"Teams: {len(teams)}")
    print(f"Matches: {len(matches)}")
    print(f"Simulations per request: {Config.NUM_SIMULATIONS}")
    print("=" * 80)
    print("\nStarting Flask server...")
    print("API available at: http://localhost:5000")
    print("API documentation:")
    print("  GET  /api/initial-state     - Get current state and baseline probabilities")
    print("  POST /api/simulate          - Run simulation with adjusted matches")
    print("  POST /api/reset             - Reset to baseline")
    print("  GET  /api/match-details/:id - Get match details")
    print("  GET  /api/health            - Health check")
    print("=" * 80 + "\n")

    app.run(debug=Config.DEBUG, port=5000)

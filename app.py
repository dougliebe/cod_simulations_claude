"""Flask application entry point for CoD simulation API."""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from backend.utils.data_loader import DataLoader
from backend.simulation.elo import EloCalculator
from backend.simulation.season_simulator import SeasonSimulator
from backend.models.match import Match
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

# Initialize simulator (will be reused for requests)
elo_calc = EloCalculator(k_factor=Config.ELO_K_FACTOR)
simulator = SeasonSimulator(teams, matches, elo_calc)

# Store baseline probabilities (computed once at startup)
# Use serial mode to avoid Windows multiprocessing issues with Flask debug mode
print("Computing baseline probabilities...")
baseline_probabilities = simulator.run_simulations(Config.NUM_SIMULATIONS, parallel=False)
print("✓ Baseline probabilities computed")


@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template('index.html')


@app.route('/api/initial-state', methods=['GET'])
def get_initial_state():
    """
    Get initial state with current standings and baseline probabilities.

    Returns:
        JSON with teams, probabilities, matches, and Elo ratings
    """
    # Get current standings
    current_standings = simulator.get_current_standings()

    # Format teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        team = teams[team_name]
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
            'win_probability_team1': simulator.get_match_win_probability(m.team1, m.team2)
        }
        for m in matches if not m.is_completed
    ]

    # Get Elo ratings
    elo_ratings = {team.name: team.elo_rating for team in teams.values()}

    return jsonify({
        'teams': teams_data,
        'probabilities': baseline_probabilities,
        'completed_matches': completed_matches,
        'upcoming_matches': upcoming_matches,
        'elo_ratings': elo_ratings,
        'num_simulations': Config.NUM_SIMULATIONS
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

    # Run simulation with adjustments
    start_time = time.time()
    probabilities = simulator.run_simulations(
        num_iterations=Config.NUM_SIMULATIONS,
        adjusted_matches=adjusted_matches
    )
    elapsed = time.time() - start_time

    # Get updated standings with adjusted matches applied
    current_standings = simulator.get_current_standings(adjusted_matches=adjusted_matches)

    # Format updated teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        # Get the team from base teams to access Elo
        team = teams[team_name]

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
        'iterations': Config.NUM_SIMULATIONS
    })


@app.route('/api/reset', methods=['POST'])
def reset():
    """
    Reset to baseline probabilities (no user adjustments).

    Returns:
        JSON with success status, baseline probabilities, and original standings
    """
    # Get original standings (no adjustments)
    current_standings = simulator.get_current_standings()

    # Format teams data
    teams_data = []
    for team_name, match_record, map_record in current_standings:
        team = teams[team_name]

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
        'message': 'Reset to baseline probabilities',
        'probabilities': baseline_probabilities,
        'teams': teams_data
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

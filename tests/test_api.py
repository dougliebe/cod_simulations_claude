"""Tests for Flask API endpoints."""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIEndpoints:
    """Test cases for API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['teams_loaded'] == 12
        assert data['matches_loaded'] == 66

    def test_get_initial_state(self, client):
        """Test GET /api/initial-state endpoint."""
        response = client.get('/api/initial-state')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check structure
        assert 'teams' in data
        assert 'probabilities' in data
        assert 'completed_matches' in data
        assert 'upcoming_matches' in data
        assert 'elo_ratings' in data

        # Check teams
        assert len(data['teams']) == 12
        team = data['teams'][0]
        assert 'name' in team
        assert 'match_wins' in team
        assert 'match_losses' in team
        assert 'elo_rating' in team

        # Check probabilities
        assert len(data['probabilities']) == 12
        for team_name, probs in data['probabilities'].items():
            # Should have seed probabilities
            assert any(key.startswith('seed_') for key in probs.keys())

        # Check Elo ratings
        assert len(data['elo_ratings']) == 12

    def test_simulate_with_adjustments(self, client):
        """Test POST /api/simulate with user adjustments."""
        # Make a request with adjusted matches
        request_data = {
            'adjusted_matches': [
                {
                    'id': 'match_0',
                    'team1': 'Cloud9 New York',
                    'team2': 'Boston Breach',
                    'team1_score': 3,
                    'team2_score': 0
                }
            ]
        }

        response = client.post(
            '/api/simulate',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check response structure
        assert 'probabilities' in data
        assert 'teams' in data
        assert 'simulation_time' in data
        assert 'iterations' in data

        # Check probabilities
        assert len(data['probabilities']) == 12

        # Check teams data includes updated standings
        assert len(data['teams']) == 12
        team = data['teams'][0]
        assert 'name' in team
        assert 'match_wins' in team
        assert 'match_losses' in team
        assert 'map_wins' in team
        assert 'map_losses' in team
        assert 'match_record' in team
        assert 'map_record' in team
        assert 'elo_rating' in team

        # Verify that adjusted match affected the standings
        # Cloud9 should have at least 1 match win and 3 map wins
        c9_team = next((t for t in data['teams'] if t['name'] == 'Cloud9 New York'), None)
        assert c9_team is not None
        assert c9_team['match_wins'] >= 1
        assert c9_team['map_wins'] >= 3

        # Check simulation metadata
        assert isinstance(data['simulation_time'], (int, float))
        assert data['iterations'] == 1000

    def test_simulate_missing_body(self, client):
        """Test POST /api/simulate with missing body."""
        response = client.post(
            '/api/simulate',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_simulate_invalid_score(self, client):
        """Test POST /api/simulate with invalid best-of-5 score."""
        request_data = {
            'adjusted_matches': [
                {
                    'id': 'match_0',
                    'team1': 'Cloud9 New York',
                    'team2': 'Boston Breach',
                    'team1_score': 4,  # Invalid: >3
                    'team2_score': 3
                }
            ]
        }

        response = client.post(
            '/api/simulate',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid score' in data['error']

    def test_simulate_multiple_adjustments(self, client):
        """Test POST /api/simulate with multiple adjusted matches."""
        request_data = {
            'adjusted_matches': [
                {
                    'id': 'match_0',
                    'team1': 'Cloud9 New York',
                    'team2': 'Boston Breach',
                    'team1_score': 3,
                    'team2_score': 1
                },
                {
                    'id': 'match_1',
                    'team1': 'Miami Heretics',
                    'team2': 'Los Angeles Thieves',
                    'team1_score': 3,
                    'team2_score': 2
                }
            ]
        }

        response = client.post(
            '/api/simulate',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'probabilities' in data

    def test_reset(self, client):
        """Test POST /api/reset endpoint."""
        response = client.post('/api/reset')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['status'] == 'success'
        assert 'probabilities' in data
        assert 'teams' in data
        assert len(data['probabilities']) == 12
        assert len(data['teams']) == 12

        # Verify teams data structure
        team = data['teams'][0]
        assert 'name' in team
        assert 'match_wins' in team
        assert 'match_losses' in team
        assert 'match_record' in team
        assert 'map_record' in team

    def test_get_match_details_valid(self, client):
        """Test GET /api/match-details with valid match ID."""
        response = client.get('/api/match-details/match_0')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check structure
        assert 'match_id' in data
        assert 'team1' in data
        assert 'team2' in data
        assert 'win_probability_team1' in data
        assert 'win_probability_team2' in data

        # Check win probabilities sum to 1
        total_prob = data['win_probability_team1'] + data['win_probability_team2']
        assert abs(total_prob - 1.0) < 0.01

    def test_get_match_details_invalid_id(self, client):
        """Test GET /api/match-details with invalid match ID."""
        response = client.get('/api/match-details/invalid_match_id')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_api_response_time(self, client):
        """Test that API responses are reasonably fast."""
        import time

        # Test initial-state endpoint
        start = time.time()
        response = client.get('/api/initial-state')
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should be very fast (baseline is pre-computed)
        assert elapsed < 0.5

    def test_simulate_response_time(self, client):
        """Test that simulate endpoint completes in reasonable time."""
        import time

        request_data = {
            'adjusted_matches': [
                {
                    'id': 'match_0',
                    'team1': 'Cloud9 New York',
                    'team2': 'Boston Breach',
                    'team1_score': 3,
                    'team2_score': 0
                }
            ]
        }

        start = time.time()
        response = client.post(
            '/api/simulate',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        elapsed = time.time() - start

        assert response.status_code == 200

        # Should complete in reasonable time (1000 sims + network)
        assert elapsed < 3.0

    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.get('/api/health')

        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_probabilities_sum_to_one(self, client):
        """Test that probabilities for each team sum to ~1.0."""
        response = client.get('/api/initial-state')
        data = json.loads(response.data)

        for team_name, probs in data['probabilities'].items():
            # Sum all seed probabilities
            total = sum(probs.get(f'seed_{i}', 0) for i in range(1, 13))

            # Should sum to ~1.0
            assert 0.99 <= total <= 1.01, f"{team_name}: probs sum to {total}"

    def test_upcoming_matches_have_win_probabilities(self, client):
        """Test that upcoming matches include win probabilities."""
        response = client.get('/api/initial-state')
        data = json.loads(response.data)

        upcoming = data['upcoming_matches']

        # All upcoming matches should have win probability
        for match in upcoming:
            assert 'win_probability_team1' in match
            assert 0 <= match['win_probability_team1'] <= 1

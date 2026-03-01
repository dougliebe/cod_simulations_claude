/**
 * API Client for CoD Simulation Backend
 * Handles all communication with Flask API endpoints
 */

class SimulationAPI {
    static BASE_URL = 'http://localhost:5000/api';

    /**
     * Get initial state with current standings and baseline probabilities
     * @param {boolean} useEqualElo - If true, use equal Elo (1500) for all teams
     * @returns {Promise<Object>} Initial state data
     */
    static async getInitialState(useEqualElo = false) {
        try {
            const url = `${this.BASE_URL}/initial-state${useEqualElo ? '?use_equal_elo=true' : ''}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching initial state:', error);
            throw new Error('Failed to load initial data. Is the Flask server running?');
        }
    }

    /**
     * Run simulation with user-adjusted match results
     * @param {Array<Object>} adjustedMatches - Array of match objects with scores
     * @param {boolean} useEqualElo - If true, use equal Elo (1500) for all teams
     * @returns {Promise<Object>} Simulation results with probabilities
     */
    static async simulate(adjustedMatches, useEqualElo = false) {
        try {
            const response = await fetch(`${this.BASE_URL}/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    adjusted_matches: adjustedMatches,
                    use_equal_elo: useEqualElo
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error running simulation:', error);
            throw error;
        }
    }

    /**
     * Reset to baseline probabilities (no user adjustments)
     * @param {boolean} useEqualElo - If true, use equal Elo (1500) for all teams
     * @returns {Promise<Object>} Reset response with baseline probabilities
     */
    static async reset(useEqualElo = false) {
        try {
            const response = await fetch(`${this.BASE_URL}/reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ use_equal_elo: useEqualElo })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error resetting simulation:', error);
            throw new Error('Failed to reset simulation');
        }
    }

    /**
     * Force recomputation of baseline probabilities
     * @param {boolean} useEqualElo - If true, use equal Elo (1500) for all teams
     * @returns {Promise<Object>} Fresh baseline probabilities with new timing
     */
    static async recomputeBaseline(useEqualElo = false) {
        try {
            const response = await fetch(`${this.BASE_URL}/recompute-baseline`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ use_equal_elo: useEqualElo })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error recomputing baseline:', error);
            throw new Error('Failed to recompute baseline');
        }
    }

    /**
     * Get detailed information about a specific match
     * @param {string} matchId - Match identifier
     * @returns {Promise<Object>} Match details with win probabilities
     */
    static async getMatchDetails(matchId) {
        try {
            const response = await fetch(`${this.BASE_URL}/match-details/${matchId}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching match details:', error);
            throw error;
        }
    }

    /**
     * Health check endpoint
     * @returns {Promise<Object>} Health status
     */
    static async healthCheck() {
        try {
            const response = await fetch(`${this.BASE_URL}/health`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error checking health:', error);
            throw error;
        }
    }
}

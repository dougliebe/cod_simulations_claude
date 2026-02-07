/**
 * Probability Table Renderer
 * Handles rendering and updating the probability table with team data
 */

class ProbabilityTable {
    constructor() {
        this.tableBody = document.getElementById('probability-table-body');
    }

    /**
     * Format probability as percentage
     * @param {number} prob - Probability (0-1)
     * @returns {string} Formatted percentage
     */
    formatProbability(prob) {
        if (prob === undefined || prob === null) {
            return '0.0%';
        }
        return `${(prob * 100).toFixed(1)}%`;
    }

    /**
     * Get CSS class based on probability value for color coding
     * @param {number} prob - Probability (0-1)
     * @returns {string} CSS class name
     */
    getProbabilityClass(prob) {
        if (prob >= 0.70) return 'prob-high';
        if (prob >= 0.30) return 'prob-medium';
        if (prob >= 0.05) return 'prob-low';
        return 'prob-very-low';
    }

    /**
     * Get CSS class for team row based on current rank
     * @param {number} rank - Current rank (1-12)
     * @returns {string} CSS class name
     */
    getRankClass(rank) {
        if (rank <= 6) return 'winners-bracket'; // Top 6 - Bracket
        if (rank <= 10) return 'play-in';        // 7-10 - Play-ins
        return 'eliminated';                      // 11-12 - Eliminated
    }

    /**
     * Sort teams by current standing
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Probability data for each team
     * @returns {Array} Sorted teams
     */
    sortTeamsByStanding(teams, probabilities) {
        return teams.sort((a, b) => {
            // Sort by match record first
            const aMatchWinPct = a.match_wins / (a.match_wins + a.match_losses) || 0;
            const bMatchWinPct = b.match_wins / (b.match_wins + b.match_losses) || 0;

            if (aMatchWinPct !== bMatchWinPct) {
                return bMatchWinPct - aMatchWinPct;
            }

            // If tied on match record, sort by map differential
            const aMapDiff = a.map_wins - a.map_losses;
            const bMapDiff = b.map_wins - b.map_losses;

            return bMapDiff - aMapDiff;
        });
    }

    /**
     * Sort teams by bracket probability (top 6 %)
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Probability data for each team
     * @returns {Array} Sorted teams
     */
    sortTeamsByBracketProb(teams, probabilities) {
        return teams.sort((a, b) => {
            // Sort by bracket probability (make_bracket)
            const aProbBracket = probabilities[a.name]?.make_bracket || 0;
            const bProbBracket = probabilities[b.name]?.make_bracket || 0;

            if (aProbBracket !== bProbBracket) {
                return bProbBracket - aProbBracket;
            }

            // If tied on bracket prob, sort by play-in probability
            const aProbPlayIn = probabilities[a.name]?.make_play_ins || 0;
            const bProbPlayIn = probabilities[b.name]?.make_play_ins || 0;

            if (aProbPlayIn !== bProbPlayIn) {
                return bProbPlayIn - aProbPlayIn;
            }

            // If still tied, sort by current match record
            const aMatchWinPct = a.match_wins / (a.match_wins + a.match_losses) || 0;
            const bMatchWinPct = b.match_wins / (b.match_wins + b.match_losses) || 0;

            return bMatchWinPct - aMatchWinPct;
        });
    }

    /**
     * Render the full probability table
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Probability data for each team
     * @param {string} sortMode - Sort mode: 'standing' or 'bracket' (default: 'standing')
     */
    renderTable(teams, probabilities, sortMode = 'standing') {
        // Sort teams based on mode
        let sortedTeams;
        if (sortMode === 'bracket') {
            sortedTeams = this.sortTeamsByBracketProb([...teams], probabilities);
        } else {
            sortedTeams = this.sortTeamsByStanding([...teams], probabilities);
        }

        // Clear existing rows
        this.tableBody.innerHTML = '';

        // Render each team row
        sortedTeams.forEach((team, index) => {
            const rank = index + 1;
            const row = this.createTeamRow(team, rank, probabilities[team.name]);
            this.tableBody.appendChild(row);
        });
    }

    /**
     * Create a table row for a team
     * @param {Object} team - Team object
     * @param {number} rank - Current rank
     * @param {Object} probs - Probability data for this team
     * @returns {HTMLElement} Table row element
     */
    createTeamRow(team, rank, probs) {
        const row = document.createElement('tr');
        row.className = this.getRankClass(rank);

        // Rank
        const rankCell = document.createElement('td');
        rankCell.textContent = rank;
        rankCell.className = 'rank-cell';
        row.appendChild(rankCell);

        // Team name
        const nameCell = document.createElement('td');
        nameCell.textContent = team.name;
        nameCell.className = 'team-name-cell';
        row.appendChild(nameCell);

        // Match record
        const matchRecordCell = document.createElement('td');
        matchRecordCell.textContent = team.match_record || `${team.match_wins}-${team.match_losses}`;
        row.appendChild(matchRecordCell);

        // Map record
        const mapRecordCell = document.createElement('td');
        mapRecordCell.textContent = team.map_record || `${team.map_wins}-${team.map_losses}`;
        row.appendChild(mapRecordCell);

        // Play-in probability (top 10)
        const playInProb = probs.make_play_ins || 0;
        const playInCell = document.createElement('td');
        playInCell.textContent = this.formatProbability(playInProb);
        playInCell.className = this.getProbabilityClass(playInProb);
        row.appendChild(playInCell);

        // Bracket probability (top 6)
        const bracketProb = probs.make_bracket || 0;
        const bracketCell = document.createElement('td');
        bracketCell.textContent = this.formatProbability(bracketProb);
        bracketCell.className = this.getProbabilityClass(bracketProb);
        row.appendChild(bracketCell);

        // Individual seed probabilities (1-12)
        for (let seed = 1; seed <= 12; seed++) {
            const seedProb = probs[`seed_${seed}`] || 0;
            const seedCell = document.createElement('td');
            seedCell.textContent = this.formatProbability(seedProb);
            seedCell.className = this.getProbabilityClass(seedProb);
            row.appendChild(seedCell);
        }

        return row;
    }

    /**
     * Update table with new probabilities without full re-render
     * @param {Object} newProbabilities - Updated probability data
     */
    updateTable(newProbabilities) {
        const rows = this.tableBody.querySelectorAll('tr');

        rows.forEach((row) => {
            const teamName = row.querySelector('.team-name-cell').textContent;
            const probs = newProbabilities[teamName];

            if (!probs) return;

            // Update play-in probability (column 5)
            const playInCell = row.cells[4];
            const playInProb = probs.make_play_ins || 0;
            playInCell.textContent = this.formatProbability(playInProb);
            playInCell.className = this.getProbabilityClass(playInProb);

            // Update bracket probability (column 6)
            const bracketCell = row.cells[5];
            const bracketProb = probs.make_bracket || 0;
            bracketCell.textContent = this.formatProbability(bracketProb);
            bracketCell.className = this.getProbabilityClass(bracketProb);

            // Update seed probabilities (columns 7-18)
            for (let seed = 1; seed <= 12; seed++) {
                const seedProb = probs[`seed_${seed}`] || 0;
                const seedCell = row.cells[6 + seed - 1];
                seedCell.textContent = this.formatProbability(seedProb);
                seedCell.className = this.getProbabilityClass(seedProb);
            }
        });
    }

    /**
     * Update team records (match and map records) and probabilities
     * Re-renders the entire table sorted by bracket probability
     * @param {Array} teams - Array of team objects with updated records
     * @param {Object} probabilities - Updated probability data
     */
    updateTableWithTeams(teams, probabilities) {
        // Re-render entire table sorted by bracket probability
        this.renderTable(teams, probabilities, 'bracket');
    }

    /**
     * Reset table to baseline with teams data
     * Re-renders the entire table sorted by current standing
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Baseline probability data
     */
    resetTableWithTeams(teams, probabilities) {
        // Re-render entire table sorted by current standing
        this.renderTable(teams, probabilities, 'standing');
    }

    /**
     * Show or hide loading indicator
     * @param {boolean} show - Whether to show loading indicator
     */
    showLoading(show) {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (show) {
            loadingIndicator.classList.remove('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }

    /**
     * Display simulation info (time and iterations)
     * @param {number} simulationTime - Time in seconds
     * @param {number} iterations - Number of iterations
     */
    showSimulationInfo(simulationTime, iterations) {
        const simInfo = document.getElementById('simulation-info');
        const simTime = document.getElementById('sim-time');
        const simIterations = document.getElementById('sim-iterations');

        simTime.textContent = simulationTime.toFixed(3);
        simIterations.textContent = iterations;

        simInfo.classList.remove('hidden');

        // Hide after 5 seconds
        setTimeout(() => {
            simInfo.classList.add('hidden');
        }, 5000);
    }
}

/**
 * Game Boxes UI
 * Handles rendering and interaction with upcoming match boxes
 */

class GameBoxes {
    constructor() {
        this.container = document.getElementById('games-container');
        this.adjustedMatches = new Map(); // matchId -> {team1_score, team2_score}
    }

    /**
     * Render all game boxes for upcoming matches
     * @param {Array} upcomingMatches - Array of upcoming match objects
     */
    renderGameBoxes(upcomingMatches) {
        // Clear existing boxes
        this.container.innerHTML = '';

        // Render each match as a compact row
        upcomingMatches.forEach((match) => {
            const matchRow = this.createMatchRow(match);
            this.container.appendChild(matchRow);
        });
    }

    /**
     * Create a compact match row element with score buttons
     * @param {Object} match - Match object
     * @returns {HTMLElement} Match row element
     */
    createMatchRow(match) {
        const row = document.createElement('div');
        row.className = 'match-row';
        row.dataset.matchId = match.id;

        // Match date
        const dateDiv = document.createElement('div');
        dateDiv.className = 'match-date';
        if (match.start_date) {
            dateDiv.textContent = this.formatDate(match.start_date);
        }
        row.appendChild(dateDiv);

        // Team 1 info
        const team1Info = document.createElement('div');
        team1Info.className = 'team-info team1';

        const team1Name = document.createElement('span');
        team1Name.className = 'team-name';
        team1Name.textContent = match.team1;
        team1Info.appendChild(team1Name);

        if (match.win_probability_team1 !== undefined) {
            const team1Prob = document.createElement('span');
            team1Prob.className = 'win-prob';
            team1Prob.textContent = `(${(match.win_probability_team1 * 100).toFixed(0)}%)`;
            team1Info.appendChild(team1Prob);
        }

        row.appendChild(team1Info);

        // Score buttons container
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'score-buttons';

        const scores = ['3-0', '3-1', '3-2', '2-3', '1-3', '0-3'];
        scores.forEach(score => {
            const btn = document.createElement('button');
            btn.className = 'score-btn';
            btn.textContent = score;
            btn.dataset.score = score;

            btn.addEventListener('click', () => {
                this.handleScoreButtonClick(match.id, btn);
            });

            buttonsDiv.appendChild(btn);
        });

        row.appendChild(buttonsDiv);

        // Team 2 info
        const team2Info = document.createElement('div');
        team2Info.className = 'team-info team2';

        if (match.win_probability_team1 !== undefined) {
            const team2Prob = document.createElement('span');
            team2Prob.className = 'win-prob';
            team2Prob.textContent = `(${((1 - match.win_probability_team1) * 100).toFixed(0)}%)`;
            team2Info.appendChild(team2Prob);
        }

        const team2Name = document.createElement('span');
        team2Name.className = 'team-name';
        team2Name.textContent = match.team2;
        team2Info.appendChild(team2Name);

        row.appendChild(team2Info);

        return row;
    }

    /**
     * Handle score button click
     * @param {string} matchId - Match ID
     * @param {HTMLElement} buttonElement - Clicked button element
     */
    handleScoreButtonClick(matchId, buttonElement) {
        const row = document.querySelector(`[data-match-id="${matchId}"]`);
        const buttons = row.querySelectorAll('.score-btn');
        const clickedScore = buttonElement.dataset.score;

        // Check if button is already selected
        const isSelected = buttonElement.classList.contains('selected');

        if (isSelected) {
            // Deselect: remove from adjusted matches (return to simulated state)
            buttonElement.classList.remove('selected');
            this.adjustedMatches.delete(matchId);
            row.classList.remove('adjusted');
        } else {
            // Select: clear other buttons and select this one
            buttons.forEach(btn => btn.classList.remove('selected'));
            buttonElement.classList.add('selected');

            // Parse score (e.g., "3-1" -> team1_score: 3, team2_score: 1)
            const [team1Score, team2Score] = clickedScore.split('-').map(Number);

            this.adjustedMatches.set(matchId, {
                team1_score: team1Score,
                team2_score: team2Score
            });

            row.classList.add('adjusted');
        }
    }

    /**
     * Clear a specific match's scores
     * @param {string} matchId - Match ID
     */
    clearMatch(matchId) {
        const row = document.querySelector(`[data-match-id="${matchId}"]`);
        const buttons = row.querySelectorAll('.score-btn');

        buttons.forEach(btn => btn.classList.remove('selected'));
        this.adjustedMatches.delete(matchId);
        row.classList.remove('adjusted');
    }

    /**
     * Clear all match scores
     */
    clearAllMatches() {
        this.adjustedMatches.clear();

        const rows = this.container.querySelectorAll('.match-row');
        rows.forEach(row => {
            const buttons = row.querySelectorAll('.score-btn');
            buttons.forEach(btn => btn.classList.remove('selected'));
            row.classList.remove('adjusted');
        });
    }

    /**
     * Get all adjusted matches in API format
     * @param {Array} upcomingMatches - Original upcoming matches data
     * @returns {Array} Array of adjusted match objects
     */
    getAdjustedMatches(upcomingMatches) {
        const adjusted = [];

        this.adjustedMatches.forEach((scores, matchId) => {
            const match = upcomingMatches.find(m => m.id === matchId);
            if (match && scores.team1_score !== null && scores.team2_score !== null) {
                adjusted.push({
                    id: matchId,
                    team1: match.team1,
                    team2: match.team2,
                    team1_score: scores.team1_score,
                    team2_score: scores.team2_score
                });
            }
        });

        return adjusted;
    }

    /**
     * Format date string for display
     * @param {string} dateStr - Date string
     * @returns {string} Formatted date
     */
    formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateStr;
        }
    }
}

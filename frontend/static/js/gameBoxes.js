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

        // Render each match
        upcomingMatches.forEach((match) => {
            const gameBox = this.createGameBox(match);
            this.container.appendChild(gameBox);
        });
    }

    /**
     * Create a game box element for a match
     * @param {Object} match - Match object
     * @returns {HTMLElement} Game box element
     */
    createGameBox(match) {
        const box = document.createElement('div');
        box.className = 'game-box';
        box.dataset.matchId = match.id;

        // Match header with date
        const header = document.createElement('div');
        header.className = 'match-header';
        if (match.start_date) {
            const dateSpan = document.createElement('span');
            dateSpan.className = 'match-date';
            dateSpan.textContent = this.formatDate(match.start_date);
            header.appendChild(dateSpan);
        }
        box.appendChild(header);

        // Match teams container
        const teamsContainer = document.createElement('div');
        teamsContainer.className = 'match-teams';

        // Team 1
        const team1Div = this.createTeamDiv(match.team1, match.id, 1);
        teamsContainer.appendChild(team1Div);

        // VS divider
        const vsDiv = document.createElement('div');
        vsDiv.className = 'vs';
        vsDiv.textContent = 'vs';
        teamsContainer.appendChild(vsDiv);

        // Team 2
        const team2Div = this.createTeamDiv(match.team2, match.id, 2);
        teamsContainer.appendChild(team2Div);

        box.appendChild(teamsContainer);

        // Match footer with win probability and clear button
        const footer = document.createElement('div');
        footer.className = 'match-footer';

        if (match.win_probability_team1 !== undefined) {
            const winProbSpan = document.createElement('span');
            winProbSpan.className = 'win-prob';
            winProbSpan.textContent = `Win prob: ${(match.win_probability_team1 * 100).toFixed(0)}% - ${((1 - match.win_probability_team1) * 100).toFixed(0)}%`;
            footer.appendChild(winProbSpan);
        }

        const clearBtn = document.createElement('button');
        clearBtn.className = 'clear-btn';
        clearBtn.textContent = 'Clear';
        clearBtn.onclick = () => this.clearMatch(match.id);
        footer.appendChild(clearBtn);

        box.appendChild(footer);

        return box;
    }

    /**
     * Create a team div with name and score input
     * @param {string} teamName - Team name
     * @param {string} matchId - Match ID
     * @param {number} teamNumber - 1 or 2
     * @returns {HTMLElement} Team div element
     */
    createTeamDiv(teamName, matchId, teamNumber) {
        const teamDiv = document.createElement('div');
        teamDiv.className = `team team${teamNumber}`;

        const nameSpan = document.createElement('span');
        nameSpan.className = 'team-name';
        nameSpan.textContent = teamName;
        teamDiv.appendChild(nameSpan);

        const scoreInput = document.createElement('input');
        scoreInput.type = 'number';
        scoreInput.className = 'score-input';
        scoreInput.min = '0';
        scoreInput.max = '3';
        scoreInput.placeholder = '-';
        scoreInput.dataset.matchId = matchId;
        scoreInput.dataset.team = `team${teamNumber}`;

        // Add input event listener
        scoreInput.addEventListener('input', (e) => {
            this.handleScoreInput(matchId, e.target);
        });

        // Add blur event listener for validation
        scoreInput.addEventListener('blur', (e) => {
            this.validateMatch(matchId);
        });

        teamDiv.appendChild(scoreInput);

        return teamDiv;
    }

    /**
     * Handle score input change
     * @param {string} matchId - Match ID
     * @param {HTMLElement} inputElement - Input element
     */
    handleScoreInput(matchId, inputElement) {
        const box = document.querySelector(`[data-match-id="${matchId}"]`);
        const inputs = box.querySelectorAll('.score-input');
        const team1Input = inputs[0];
        const team2Input = inputs[1];

        const team1Score = team1Input.value === '' ? null : parseInt(team1Input.value);
        const team2Score = team2Input.value === '' ? null : parseInt(team2Input.value);

        // Update adjusted matches map
        if (team1Score !== null || team2Score !== null) {
            this.adjustedMatches.set(matchId, {
                team1_score: team1Score,
                team2_score: team2Score
            });

            // Highlight box as adjusted
            box.classList.add('adjusted');
        } else {
            this.adjustedMatches.delete(matchId);
            box.classList.remove('adjusted');
        }

        // Clear any previous error
        box.classList.remove('invalid');
    }

    /**
     * Validate a match's scores
     * @param {string} matchId - Match ID
     * @returns {boolean} True if valid
     */
    validateMatch(matchId) {
        const box = document.querySelector(`[data-match-id="${matchId}"]`);
        const inputs = box.querySelectorAll('.score-input');
        const team1Score = inputs[0].value === '' ? null : parseInt(inputs[0].value);
        const team2Score = inputs[1].value === '' ? null : parseInt(inputs[1].value);

        // If both are empty, it's valid (no adjustment)
        if (team1Score === null && team2Score === null) {
            box.classList.remove('invalid');
            return true;
        }

        // If only one is filled, it's invalid
        if (team1Score === null || team2Score === null) {
            box.classList.add('invalid');
            return false;
        }

        // Scores must be 0-3
        if (team1Score < 0 || team1Score > 3 || team2Score < 0 || team2Score > 3) {
            box.classList.add('invalid');
            return false;
        }

        // Valid best-of-5: one team must have exactly 3
        if (team1Score !== 3 && team2Score !== 3) {
            box.classList.add('invalid');
            return false;
        }

        // Both can't have 3
        if (team1Score === 3 && team2Score === 3) {
            box.classList.add('invalid');
            return false;
        }

        // Valid
        box.classList.remove('invalid');
        return true;
    }

    /**
     * Validate all matches
     * @returns {boolean} True if all valid
     */
    validateAllMatches() {
        let allValid = true;

        this.adjustedMatches.forEach((scores, matchId) => {
            if (!this.validateMatch(matchId)) {
                allValid = false;
            }
        });

        return allValid;
    }

    /**
     * Clear a specific match's scores
     * @param {string} matchId - Match ID
     */
    clearMatch(matchId) {
        const box = document.querySelector(`[data-match-id="${matchId}"]`);
        const inputs = box.querySelectorAll('.score-input');

        inputs.forEach(input => {
            input.value = '';
        });

        this.adjustedMatches.delete(matchId);
        box.classList.remove('adjusted');
        box.classList.remove('invalid');
    }

    /**
     * Clear all match scores
     */
    clearAllMatches() {
        this.adjustedMatches.clear();

        const boxes = this.container.querySelectorAll('.game-box');
        boxes.forEach(box => {
            const inputs = box.querySelectorAll('.score-input');
            inputs.forEach(input => {
                input.value = '';
            });
            box.classList.remove('adjusted');
            box.classList.remove('invalid');
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

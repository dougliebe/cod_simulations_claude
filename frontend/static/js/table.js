/**
 * Probability Table Renderer
 * Handles rendering and updating the probability table with team data
 */

// Team name to logo filename (abbreviation) mapping
const TEAM_LOGO_MAP = {
    'Boston Breach': 'BOS',
    'Carolina Royal Ravens': 'CAR',
    'Cloud9 New York': 'C9NY',
    'FaZe Vegas': 'LVF',
    'G2 Minnesota': 'MIN',
    'Los Angeles Thieves': 'LAT',
    'Miami Heretics': 'MIA',
    'OpTic Texas': 'TX',
    'Paris Gentle Mates': 'PAR',
    'Riyadh Falcons': 'RIY',
    'Toronto KOI': 'KOI',
    'Vancouver Surge': 'VAN'
};

class ProbabilityTable {
    constructor() {
        this.tableBody = document.getElementById('probability-table-body');
    }

    getLogoPath(teamName) {
        const abbr = TEAM_LOGO_MAP[teamName];
        if (!abbr) return null;
        return `/static/logos/${abbr}.png`;
    }

    /**
     * Format probability as percentage
     * @param {number} prob - Probability (0-1)
     * @returns {string} Formatted percentage
     */
    formatProbability(prob) {
        if (prob === undefined || prob === null) {
            return '0.0';
        }
        return (prob * 100).toFixed(1);
    }

    /**
     * Interpolate color from green (high) to purple (low) based on value 0-1
     * Lightened/pastel version for softer appearance
     * @param {number} value - Value 0-1 (1 = high/green, 0 = low/purple)
     * @returns {string} Hex color
     */
    interpolateColor(value) {
        const r = Math.round(26 + 49 * (1 - value));
        const g = Math.round(255 * value);
        const b = Math.round(26 + 120 * (1 - value));
        // Lighten by blending 60% original + 40% white
        const blend = 0.6;
        const rLight = Math.round(r * blend + 255 * (1 - blend));
        const gLight = Math.round(g * blend + 255 * (1 - blend));
        const bLight = Math.round(b * blend + 255 * (1 - blend));
        return `#${rLight.toString(16).padStart(2, '0')}${gLight.toString(16).padStart(2, '0')}${bLight.toString(16).padStart(2, '0')}`;
    }

    /**
     * Get black or white text color for readability on given background (WCAG relative luminance)
     * @param {string} hex - Hex color e.g. '#1AFF1A'
     * @returns {string} '#000000' or '#ffffff'
     */
    getContrastColor(hex) {
        const rgb = hex.replace(/^#/, '').match(/.{2}/g).map(x => parseInt(x, 16));
        const toLinear = (val) => {
            const srgb = val / 255;
            return srgb <= 0.04045 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4);
        };
        const L = 0.2126 * toLinear(rgb[0]) + 0.7152 * toLinear(rgb[1]) + 0.0722 * toLinear(rgb[2]);
        return L > 0.5 ? '#000000' : '#ffffff';
    }

    /**
     * Get cell style (background + text color) for probability value
     * @param {number} prob - Probability (0-1)
     * @returns {{ backgroundColor: string, color: string }}
     */
    getCellStyle(prob) {
        const bg = this.interpolateColor(prob);
        return { backgroundColor: bg, color: this.getContrastColor(bg) };
    }

    /**
     * Normalize value to 0-1 scale within column min/max (highest = 1, lowest = 0)
     * @param {number} value - Raw value
     * @param {number} colMin - Column minimum
     * @param {number} colMax - Column maximum
     * @returns {number} Normalized 0-1 (1 = highest in column)
     */
    normalizeForColumn(value, colMin, colMax) {
        if (colMax <= colMin || !Number.isFinite(colMin) || !Number.isFinite(colMax)) return 1;
        return (value - colMin) / (colMax - colMin);
    }

    /**
     * Compute min/max per column for play-in+bracket (combined), and seeds (separate) across all teams
     * @param {Object} probabilities - Keyed by team name
     * @param {Array} teamNames - Team names in table order
     * @returns {Object} { playInBracket: {min, max}, seed_1: {min, max}, ... }
     */
    computeColumnScales(probabilities, teamNames) {
        const scales = {
            playInBracket: { min: Infinity, max: -Infinity }
        };
        for (let seed = 1; seed <= 12; seed++) {
            scales[`seed_${seed}`] = { min: Infinity, max: -Infinity };
        }

        teamNames.forEach((name) => {
            const p = probabilities[name];
            if (!p) return;
            const playIn = p.make_play_ins || 0;
            const bracket = p.make_bracket || 0;
            scales.playInBracket.min = Math.min(scales.playInBracket.min, playIn, bracket);
            scales.playInBracket.max = Math.max(scales.playInBracket.max, playIn, bracket);
            for (let seed = 1; seed <= 12; seed++) {
                const v = p[`seed_${seed}`] || 0;
                scales[`seed_${seed}`].min = Math.min(scales[`seed_${seed}`].min, v);
                scales[`seed_${seed}`].max = Math.max(scales[`seed_${seed}`].max, v);
            }
        });

        return scales;
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
     * Calculate weighted average placement for a team
     * @param {Object} probs - Team's seed probabilities (seed_1, seed_2, ..., seed_12)
     * @returns {number} Weighted average placement (lower is better)
     */
    calculateWeightedAvgPlacement(probs) {
        let weightedSum = 0;
        for (let seed = 1; seed <= 12; seed++) {
            const prob = probs[`seed_${seed}`] || 0;
            weightedSum += seed * prob;
        }
        return weightedSum;
    }

    /**
     * Sort teams by weighted average placement
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Probability data for each team
     * @returns {Array} Sorted teams
     */
    sortTeamsByWeightedAvgPlacement(teams, probabilities) {
        return teams.sort((a, b) => {
            const aProbs = probabilities[a.name];
            const bProbs = probabilities[b.name];

            const aWeightedAvg = this.calculateWeightedAvgPlacement(aProbs);
            const bWeightedAvg = this.calculateWeightedAvgPlacement(bProbs);

            // Lower weighted average = better expected placement
            return aWeightedAvg - bWeightedAvg;
        });
    }

    /**
     * Render the full probability table
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Probability data for each team
     */
    renderTable(teams, probabilities) {
        // Sort teams by weighted average placement
        const sortedTeams = this.sortTeamsByWeightedAvgPlacement([...teams], probabilities);
        const teamNames = sortedTeams.map(t => t.name);

        // Compute per-column min/max so highest in each column gets same color (green)
        const scales = this.computeColumnScales(probabilities, teamNames);

        // Clear existing rows
        this.tableBody.innerHTML = '';

        // Render each team row, inserting cutoff separators after rows 6 and 10
        sortedTeams.forEach((team, index) => {
            const rank = index + 1;
            if (rank === 7 || rank === 11) {
                this.tableBody.appendChild(this.createCutoffSeparatorRow());
            }
            const row = this.createTeamRow(team, rank, probabilities[team.name], scales);
            this.tableBody.appendChild(row);
        });
    }

    /**
     * Create a full-width separator row for dashed cutoff lines (avoids breaks at cell boundaries)
     * @returns {HTMLElement} Table row element
     */
    createCutoffSeparatorRow() {
        const row = document.createElement('tr');
        row.className = 'cutoff-separator';
        const cell = document.createElement('td');
        cell.colSpan = 18;
        row.appendChild(cell);
        return row;
    }

    /**
     * Create a table row for a team
     * @param {Object} team - Team object
     * @param {number} rank - Current rank
     * @param {Object} probs - Probability data for this team
     * @param {Object} scales - Per-column min/max for color normalization
     * @returns {HTMLElement} Table row element
     */
    createTeamRow(team, rank, probs, scales) {
        const row = document.createElement('tr');
        row.className = this.getRankClass(rank);

        // Rank
        const rankCell = document.createElement('td');
        rankCell.textContent = rank;
        rankCell.className = 'rank-cell numeric-cell';
        row.appendChild(rankCell);

        // Team logo only (no name text)
        const nameCell = document.createElement('td');
        nameCell.className = 'team-name-cell';
        nameCell.dataset.teamName = team.name;
        const logoPath = this.getLogoPath(team.name);
        if (logoPath) {
            const img = document.createElement('img');
            img.src = logoPath;
            img.alt = team.name;
            img.className = 'team-logo';
            img.title = team.name;
            nameCell.appendChild(img);
        }
        row.appendChild(nameCell);

        // Match record
        const matchRecordCell = document.createElement('td');
        matchRecordCell.textContent = team.match_record || `${team.match_wins}-${team.match_losses}`;
        matchRecordCell.className = 'numeric-cell';
        row.appendChild(matchRecordCell);

        // Map record
        const mapRecordCell = document.createElement('td');
        mapRecordCell.textContent = team.map_record || `${team.map_wins}-${team.map_losses}`;
        mapRecordCell.className = 'numeric-cell';
        row.appendChild(mapRecordCell);

        // Play-in probability (top 10) - shared scale with bracket
        const playInProb = probs.make_play_ins || 0;
        const playInCell = document.createElement('td');
        playInCell.textContent = this.formatProbability(playInProb);
        playInCell.className = 'numeric-cell probability-cell';
        const playInNorm = this.normalizeForColumn(playInProb, scales.playInBracket.min, scales.playInBracket.max);
        const playInStyle = this.getCellStyle(playInNorm);
        playInCell.style.backgroundColor = playInStyle.backgroundColor;
        row.appendChild(playInCell);

        // Bracket probability (top 6) - shared scale with play-in
        const bracketProb = probs.make_bracket || 0;
        const bracketCell = document.createElement('td');
        bracketCell.textContent = this.formatProbability(bracketProb);
        bracketCell.className = 'numeric-cell probability-cell';
        const bracketNorm = this.normalizeForColumn(bracketProb, scales.playInBracket.min, scales.playInBracket.max);
        const bracketStyle = this.getCellStyle(bracketNorm);
        bracketCell.style.backgroundColor = bracketStyle.backgroundColor;
        row.appendChild(bracketCell);

        // Individual seed probabilities (1-12) - scaled per column
        for (let seed = 1; seed <= 12; seed++) {
            const seedProb = probs[`seed_${seed}`] || 0;
            const seedCell = document.createElement('td');
            seedCell.textContent = this.formatProbability(seedProb);
            seedCell.className = seed === 1 ? 'numeric-cell probability-cell seed-column-separator' : 'numeric-cell probability-cell';
            const s = scales[`seed_${seed}`];
            const seedNorm = this.normalizeForColumn(seedProb, s.min, s.max);
            const seedStyle = this.getCellStyle(seedNorm);
            seedCell.style.backgroundColor = seedStyle.backgroundColor;
            row.appendChild(seedCell);
        }

        return row;
    }

    /**
     * Update table with new probabilities without full re-render
     * @param {Object} newProbabilities - Updated probability data
     */
    updateTable(newProbabilities) {
        const rows = this.tableBody.querySelectorAll('tr:not(.cutoff-separator)');
        const teamNames = Array.from(rows).map(r => r.querySelector('.team-name-cell')?.dataset.teamName).filter(Boolean);

        // Compute per-column min/max so highest in each column gets same color (green)
        const scales = this.computeColumnScales(newProbabilities, teamNames);

        rows.forEach((row) => {
            const teamName = row.querySelector('.team-name-cell')?.dataset.teamName;
            if (!teamName) return;
            const probs = newProbabilities[teamName];
            if (!probs) return;

            // Update play-in probability (column 5) - shared scale with bracket
            const playInCell = row.cells[4];
            const playInProb = probs.make_play_ins || 0;
            playInCell.textContent = this.formatProbability(playInProb);
            const playInNorm = this.normalizeForColumn(playInProb, scales.playInBracket.min, scales.playInBracket.max);
            const playInStyle = this.getCellStyle(playInNorm);
            playInCell.style.backgroundColor = playInStyle.backgroundColor;

            // Update bracket probability (column 6) - shared scale with play-in
            const bracketCell = row.cells[5];
            const bracketProb = probs.make_bracket || 0;
            bracketCell.textContent = this.formatProbability(bracketProb);
            const bracketNorm = this.normalizeForColumn(bracketProb, scales.playInBracket.min, scales.playInBracket.max);
            const bracketStyle = this.getCellStyle(bracketNorm);
            bracketCell.style.backgroundColor = bracketStyle.backgroundColor;

            // Update seed probabilities (columns 7-18)
            for (let seed = 1; seed <= 12; seed++) {
                const seedProb = probs[`seed_${seed}`] || 0;
                const seedCell = row.cells[6 + seed - 1];
                seedCell.textContent = this.formatProbability(seedProb);
                const s = scales[`seed_${seed}`];
                const seedNorm = this.normalizeForColumn(seedProb, s.min, s.max);
                const seedStyle = this.getCellStyle(seedNorm);
                seedCell.style.backgroundColor = seedStyle.backgroundColor;
            }
        });
    }

    /**
     * Update team records (match and map records) and probabilities
     * Re-renders the entire table sorted by weighted average placement
     * @param {Array} teams - Array of team objects with updated records
     * @param {Object} probabilities - Updated probability data
     */
    updateTableWithTeams(teams, probabilities) {
        // Re-render entire table sorted by weighted average placement
        this.renderTable(teams, probabilities);
    }

    /**
     * Reset table to baseline with teams data
     * Re-renders the entire table sorted by weighted average placement
     * @param {Array} teams - Array of team objects
     * @param {Object} probabilities - Baseline probability data
     */
    resetTableWithTeams(teams, probabilities) {
        // Re-render entire table sorted by weighted average placement
        this.renderTable(teams, probabilities);
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
        simIterations.textContent = iterations.toLocaleString();

        simInfo.classList.remove('hidden');
    }
}

/**
 * Main Application Logic
 * Coordinates API calls, table rendering, and game box interactions
 */

class App {
    constructor() {
        this.state = {
            initialData: null,
            currentProbabilities: null,
            isSimulating: false,
            useEqualElo: false
        };

        this.table = new ProbabilityTable();
        this.gameBoxes = new GameBoxes();

        // Bottom buttons
        this.submitBtn = document.getElementById('submit-btn');
        this.resetBtn = document.getElementById('reset-btn');

        // Top buttons
        this.submitBtnTop = document.getElementById('submit-btn-top');
        this.resetBtnTop = document.getElementById('reset-btn-top');

        this.recomputeBaselineBtn = document.getElementById('recompute-baseline-btn');
        this.copyAsImageBtn = document.getElementById('copy-as-image-btn');
        this.errorMessage = document.getElementById('error-message');
        this.equalEloToggle = document.getElementById('equal-elo-toggle');
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            // Sync toggle with state
            this.equalEloToggle.checked = this.state.useEqualElo;

            // Show loading
            this.table.showLoading(true);

            // Fetch initial state from API
            const data = await SimulationAPI.getInitialState(this.state.useEqualElo);
            this.state.initialData = data;
            this.state.currentProbabilities = data.probabilities;

            // Render probability table
            this.table.renderTable(data.teams, data.probabilities);

            // Render game boxes
            this.gameBoxes.renderGameBoxes(data.upcoming_matches);

            // Show simulation info for initial load
            if (data.simulation_time !== undefined && data.num_simulations) {
                this.table.showSimulationInfo(data.simulation_time, data.num_simulations, {
                    median_bracket_cutoff: data.median_bracket_cutoff,
                    median_playin_cutoff: data.median_playin_cutoff
                });
            }

            // Sync state from response (e.g. use_equal_elo)
            this.state.useEqualElo = data.use_equal_elo ?? this.state.useEqualElo;
            this.equalEloToggle.checked = this.state.useEqualElo;

            // Attach event listeners
            this.attachEventListeners();

            // Hide loading
            this.table.showLoading(false);

            console.log('App initialized successfully');
        } catch (error) {
            this.showError(`Failed to initialize app: ${error.message}`);
            this.table.showLoading(false);
        }
    }

    /**
     * Attach event listeners to UI elements
     */
    attachEventListeners() {
        // Bottom submit button
        this.submitBtn.addEventListener('click', () => {
            this.handleSubmit();
        });

        // Bottom reset button
        this.resetBtn.addEventListener('click', () => {
            this.handleReset();
        });

        // Top submit button
        this.submitBtnTop.addEventListener('click', () => {
            this.handleSubmit();
        });

        // Top reset button
        this.resetBtnTop.addEventListener('click', () => {
            this.handleReset();
        });

        // Recompute baseline button
        this.recomputeBaselineBtn.addEventListener('click', () => {
            this.handleRecomputeBaseline();
        });

        // Copy as image button
        this.copyAsImageBtn.addEventListener('click', () => {
            this.handleCopyAsImage();
        });

        // Equal Elo toggle - refetch when changed
        this.equalEloToggle.addEventListener('change', () => {
            this.state.useEqualElo = this.equalEloToggle.checked;
            this.refreshForEloMode();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter to submit
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                this.handleSubmit();
            }
            // Escape to reset
            if (e.key === 'Escape') {
                this.handleReset();
            }
        });
    }

    /**
     * Refresh data when Elo mode changes (toggle between CSV and equal Elo)
     */
    async refreshForEloMode() {
        if (this.state.isSimulating) return;
        try {
            this.table.showLoading(true);
            const data = await SimulationAPI.getInitialState(this.state.useEqualElo);
            this.state.initialData = data;
            this.state.currentProbabilities = data.probabilities;
            this.table.renderTable(data.teams, data.probabilities);
            this.gameBoxes.renderGameBoxes(data.upcoming_matches);
            if (data.simulation_time !== undefined && data.num_simulations) {
                this.table.showSimulationInfo(data.simulation_time, data.num_simulations, {
                    median_bracket_cutoff: data.median_bracket_cutoff,
                    median_playin_cutoff: data.median_playin_cutoff
                });
            }
            this.state.useEqualElo = data.use_equal_elo ?? this.state.useEqualElo;
            this.equalEloToggle.checked = this.state.useEqualElo;
        } catch (error) {
            this.showError(`Failed to refresh: ${error.message}`);
        } finally {
            this.table.showLoading(false);
        }
    }

    /**
     * Handle submit button click
     */
    async handleSubmit() {
        // Prevent multiple simultaneous submissions
        if (this.state.isSimulating) {
            return;
        }

        try {
            // Get adjusted matches (buttons always produce valid scores)
            const adjustedMatches = this.gameBoxes.getAdjustedMatches(
                this.state.initialData.upcoming_matches
            );

            // If no adjustments, show message
            if (adjustedMatches.length === 0) {
                this.showError('No match scores selected. Click a score button and try again.');
                return;
            }

            // Clear any previous errors
            this.hideError();

            // Set simulating state
            this.state.isSimulating = true;

            // Disable and update both button sets
            this.submitBtn.disabled = true;
            this.submitBtn.textContent = 'Simulating...';
            this.submitBtnTop.disabled = true;
            this.submitBtnTop.textContent = 'Simulating...';

            this.table.showLoading(true);

            // Call API
            const result = await SimulationAPI.simulate(adjustedMatches, this.state.useEqualElo);

            // Update table with teams data and probabilities
            if (result.teams) {
                this.table.updateTableWithTeams(result.teams, result.probabilities);
            } else {
                // Fallback to old method if teams data not available
                this.table.updateTable(result.probabilities);
            }
            this.state.currentProbabilities = result.probabilities;

            // Show simulation info
            this.table.showSimulationInfo(result.simulation_time, result.iterations, {
                median_bracket_cutoff: result.median_bracket_cutoff,
                median_playin_cutoff: result.median_playin_cutoff
            });

            console.log(`Simulation completed in ${result.simulation_time}s`);
        } catch (error) {
            this.showError(`Simulation failed: ${error.message}`);
        } finally {
            // Reset state
            this.state.isSimulating = false;

            // Re-enable and restore text for both button sets
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = 'Simulate with Adjusted Scores';
            this.submitBtnTop.disabled = false;
            this.submitBtnTop.textContent = 'Simulate with Adjusted Scores';

            this.table.showLoading(false);
        }
    }

    /**
     * Handle reset button click
     */
    async handleReset() {
        if (this.state.isSimulating) {
            return;
        }

        try {
            // Clear all match inputs
            this.gameBoxes.clearAllMatches();

            // Clear any errors
            this.hideError();

            // Set simulating state
            this.state.isSimulating = true;

            // Disable both reset buttons
            this.resetBtn.disabled = true;
            this.resetBtnTop.disabled = true;

            this.table.showLoading(true);

            // Call reset API
            const result = await SimulationAPI.reset(this.state.useEqualElo);

            // Reset table to baseline sorted by current standing
            if (result.teams) {
                this.table.resetTableWithTeams(result.teams, result.probabilities);
            } else {
                // Fallback to old method if teams data not available
                this.table.updateTable(result.probabilities);
            }
            this.state.currentProbabilities = result.probabilities;

            if (result.simulation_time !== undefined && result.iterations) {
                this.table.showSimulationInfo(result.simulation_time, result.iterations, {
                    median_bracket_cutoff: result.median_bracket_cutoff,
                    median_playin_cutoff: result.median_playin_cutoff
                });
            }

            console.log('Reset to baseline probabilities');
        } catch (error) {
            this.showError(`Reset failed: ${error.message}`);
        } finally {
            // Reset state
            this.state.isSimulating = false;

            // Re-enable both reset buttons
            this.resetBtn.disabled = false;
            this.resetBtnTop.disabled = false;

            this.table.showLoading(false);
        }
    }

    /**
     * Handle recompute baseline button click
     */
    async handleRecomputeBaseline() {
        if (this.state.isSimulating) {
            return;
        }

        try {
            // Clear any errors
            this.hideError();

            // Set simulating state
            this.state.isSimulating = true;
            this.recomputeBaselineBtn.disabled = true;
            this.recomputeBaselineBtn.textContent = 'Computing...';
            this.table.showLoading(true);

            // Call recompute baseline API
            const result = await SimulationAPI.recomputeBaseline(this.state.useEqualElo);

            // Update table with fresh baseline
            if (result.teams) {
                this.table.renderTable(result.teams, result.probabilities, 'standing');
            } else {
                this.table.updateTable(result.probabilities);
            }
            this.state.currentProbabilities = result.probabilities;

            // Show simulation info with fresh timing
            this.table.showSimulationInfo(result.simulation_time, result.iterations, {
                median_bracket_cutoff: result.median_bracket_cutoff,
                median_playin_cutoff: result.median_playin_cutoff
            });

            console.log(`Baseline recomputed in ${result.simulation_time}s`);
        } catch (error) {
            this.showError(`Recompute baseline failed: ${error.message}`);
        } finally {
            // Reset state
            this.state.isSimulating = false;
            this.recomputeBaselineBtn.disabled = false;
            this.recomputeBaselineBtn.textContent = 'Recompute Baseline';
            this.table.showLoading(false);
        }
    }

    /**
     * Copy probability view (title + table + simulation info) as image to clipboard
     */
    async handleCopyAsImage() {
        const element = document.getElementById('copyable-probability-view');
        if (!element || typeof html2canvas === 'undefined') {
            this.showError('Copy as image requires html2canvas. Please refresh the page.');
            return;
        }

        const btn = this.copyAsImageBtn;
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Copying...';

        try {
            const canvas = await html2canvas(element, {
                scale: 2,
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff'
            });

            const blob = await new Promise((resolve) => {
                canvas.toBlob(resolve, 'image/png', 1.0);
            });

            await navigator.clipboard.write([
                new ClipboardItem({ 'image/png': blob })
            ]);

            btn.textContent = 'Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.disabled = false;
            }, 2000);
        } catch (error) {
            this.showError(`Copy failed: ${error.message}. Try a different browser or check clipboard permissions.`);
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.remove('hidden');

        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideError();
        }, 10000);
    }

    /**
     * Hide error message
     */
    hideError() {
        this.errorMessage.classList.add('hidden');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});

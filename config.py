"""Configuration settings for CoD simulation application."""

class Config:
    """Application configuration."""

    # Flask settings
    DEBUG = True
    SECRET_KEY = 'dev-secret-key-change-in-production'

    # Simulation parameters
    NUM_TEAMS = 12
    MATCHES_PER_TEAM = 11
    TOTAL_MATCHES = 66
    NUM_SIMULATIONS = 10000
    BEST_OF = 5  # Best-of-5 series
    PLAY_IN_TEAMS = 10  # Top 10 make play-ins
    BRACKET_TEAMS = 6  # Top 6 go directly to bracket

    # Elo settings
    ELO_K_FACTOR = 20.0
    DEFAULT_ELO = 1500.0

    # Performance settings
    SIMULATION_TIMEOUT = 5.0  # Max seconds for simulation
    ENABLE_PROFILING = False

    # Data paths
    DATA_DIR = 'data'
    MATCHES_CSV = 'data/upcoming_matches_2026_major2.csv'
    ELO_RATINGS_CSV = 'data/teams_elo.csv'

    # Tiebreaker configuration
    TIEBREAKER_SEED_RULES = {
        'tiebreaker_match_seeds': [1, 2, 3, 8],  # Seeds that use tiebreaker match
        'coin_flip_seeds': [4, 9, 10, 11],  # Seeds that use coin flip
        'choice_seeds': [5, 6, 7]  # Seeds where higher seed chooses opponent
    }

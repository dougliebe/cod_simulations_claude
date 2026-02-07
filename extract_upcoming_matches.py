import json
import pandas as pd
from datetime import datetime

def extract_upcoming_matches(json_file_path):
    """
    Extract upcoming match information from a nested JSON structure.
    
    Args:
        json_file_path: Path to the JSON file
        
    Returns:
        DataFrame with upcoming match information
    """
    # Load the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract all matches from the nested structure
    all_matches = []
    for item in data:
        if 'result' in item and 'data' in item['result'] and 'json' in item['result']['data']:
            matches = item['result']['data']['json']
            all_matches.extend(matches)
    
    # Filter for upcoming matches and extract required fields
    upcoming_matches = []
    for match in all_matches:
        # Skip non-dictionary items
        if not isinstance(match, dict):
            continue
            
        if match.get('status') == 'upcoming':
            match_info = {
                'datetime': match.get('datetime'),
                'team1': match.get('team1', {}).get('name') if match.get('team1') else None,
                'team2': match.get('team2', {}).get('name') if match.get('team2') else None,
                'team1_score': match.get('team_1_score'),
                'team2_score': match.get('team_2_score')
            }
            upcoming_matches.append(match_info)
    
    # Convert to DataFrame
    df = pd.DataFrame(upcoming_matches)
    
    # Convert datetime string to datetime object for better sorting
    if not df.empty and 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
    
    return df


if __name__ == "__main__":
    # Path to the JSON file
    json_file = r"D:\ANALYTICS\cod_simulations_claude\data\matches.json"
    
    # Extract upcoming matches
    upcoming_df = extract_upcoming_matches(json_file)
    
    # Display results
    print(f"Found {len(upcoming_df)} upcoming matches:\n")
    print(upcoming_df.to_string(index=False))
    
    # Optionally save to CSV
    output_csv = r"D:\ANALYTICS\cod_simulations_claude\data\upcoming_matches.csv"
    upcoming_df.to_csv(output_csv, index=False)
    print(f"\n✓ Results saved to: {output_csv}")

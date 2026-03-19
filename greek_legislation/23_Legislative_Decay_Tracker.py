import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
INPUT_FILE = "all_greek_laws/all_laws_metadata_full.csv"
CHUNK_SIZE = 25000  # Efficient for RAM

def analyze_decay_final(file_path):
    print(f"--- Starting Memory-Efficient Analysis (Blackmamba Edition) ---")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    # Updated columns based on your dmesg/terminal output
    date_col = 'publication_date'
    id_col = 'law' 
    relevant_cols = [id_col, date_col]

    partial_results = []
    print(f"Reading {file_path} in chunks of {CHUNK_SIZE}...")
    
    # Process in chunks to prevent OOM (Out of Memory)
    try:
        for i, chunk in enumerate(pd.read_csv(file_path, usecols=relevant_cols, chunksize=CHUNK_SIZE)):
            # Convert to datetime (errors='coerce' handles empty/bad strings)
            chunk[date_col] = pd.to_datetime(chunk[date_col], errors='coerce')
            chunk = chunk.dropna(subset=[date_col])
            
            # Keep only unique laws per chunk to keep the merge lean
            partial_results.append(chunk)
            print(f"   Processed chunk {i+1} ({len(chunk)} rows)...", end='\r')

        print("\nMerging data and calculating temporal gaps...")
        full_df = pd.concat(partial_results)
        
        # Sort by Law and Date to find the "Update" sequence
        full_df = full_df.sort_values(by=[id_col, date_col])
        
        # Calculate days between the original law and subsequent entries
        full_df['days_to_patch'] = full_df.groupby(id_col)[date_col].diff().dt.days
        
        # Filter for rows that represent a modification (gap > 0)
        decay_events = full_df[full_df['days_to_patch'] > 0].copy()

        if decay_events.empty:
            print("\n[INFO] No recurring law numbers found yet.")
            print("The dataset might still be in the 'downloading' phase for unique laws.")
            return

        # 4. Results
        median_val = decay_events['days_to_patch'].median()
        avg_val = decay_events['days_to_patch'].mean()
        
        print(f"\n[SUCCESS] ANALYSIS COMPLETE")
        print(f"Average time to first amendment: {avg_val:.1f} days")
        print(f"Median time to first amendment: {median_val:.1f} days")

        # 5. Save Visualization
        plt.figure(figsize=(10, 6))
        sns.histplot(decay_events['days_to_patch'], bins=40, color='darkblue', kde=True)
        plt.axvline(median_val, color='orange', linestyle='--', label=f'Median: {median_val} days')
        plt.title('Greek Legislative Stability: Days from Enactment to Modification')
        plt.xlabel('Days')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.savefig('legislative_decay_stable.png')
        print(f"[FILE] Plot saved as 'legislative_decay_stable.png'")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")

if __name__ == "__main__":
    analyze_decay_final(INPUT_FILE)
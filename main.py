import pandas as pd
import numpy as np
from datetime import datetime

from config import df_query
from data.ecm_data import get_ecm_data
from models.formulas import get_all_combinations
from analysis.combination_analysis import analyze_all_combinations, summarize_results, find_best_for_each_candidate
from utils.display import print_header

def main():
    print_header("FORENSIC ANALYSIS: SQL vs ECM DEVIATION")
    
    print("\nLoading ECM data...")
    df_ecm = get_ecm_data()
    print(f"   Loaded {len(df_ecm)} candidates")
    
    combinations = get_all_combinations()
    print(f"\nTesting {len(combinations)} combinations:")
    for combo in combinations:
        print(f"   - {combo['name']}")
    
    print_header("COMBINATION ANALYSIS RESULTS")
    results_df = analyze_all_combinations(df_ecm, combinations)
    
    if results_df.empty:
        print("ERROR: No results to analyze")
        return
    
    print_header("SUMMARY STATISTICS BY COMBINATION")
    summary = summarize_results(results_df)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(summary.to_string(index=False))
    
    print_header("OPTIMAL COMBINATION PER CANDIDATE PAIR")
    best_pairs = find_best_for_each_candidate(results_df)
    print(best_pairs.to_string(index=False))
    
    print_header("SOURCE-SPECIFIC ANALYSIS")
    
    for source in ['candidate', 'cei_max']:
        source_data = results_df[results_df['source'] == source]
        if not source_data.empty:
            print(f"\nSOURCE: {source}")
            source_summary = source_data.groupby(['T', 'formula_type']).agg({
                'difference': ['mean', 'median', 'min', 'max', 'count']
            }).round(6)
            print(source_summary)
    
    print_header("FINDINGS")
    
    best_combo = summary.iloc[0]
    print(f"\nOPTIMAL COMBINATION:")
    print(f"   {best_combo['Комбинация']}")
    print(f"   Mean difference: {best_combo['Средняя разница']:.6f}")
    print(f"   Pairs with error < 0.01: {best_combo['Кол-во < 0.01']} of {best_combo['Кол-во измерений']} ({best_combo['Процент < 0.01']})")
    
    problematic = best_pairs[best_pairs['разница'] > 0.01]
    if not problematic.empty:
        print(f"\nHIGH-DEVIATION PAIRS (difference > 0.01):")
        for _, row in problematic.iterrows():
            print(f"   {row['target']} → {row['candidate']}: {row['разница']:.6f}")
            print(f"     Optimal combination: {row['лучшая_комбинация']}")
    
    print("\nRECOMMENDATIONS:")
    print("   1. Compare error rates between candidate and cei_max sources")
    print("   2. Verify threshold consistency across candidates")
    print("   3. Confirm formula uniformity across system components")
    print("   4. Conduct targeted debugging for high-deviation pairs")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_df.to_csv(f'analysis_results_{timestamp}.csv', index=False)
    print(f"\nResults saved to: analysis_results_{timestamp}.csv")
    
    print("\nAnalysis complete.")

if __name__ == "__main__":
    main()
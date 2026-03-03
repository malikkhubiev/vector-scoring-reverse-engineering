import pandas as pd
import numpy as np
from config import df_query
from data.ecm_data import get_ecm_data, get_group_mapping
from utils.display import print_header

def get_candidate_id_by_key(candidate_key):
    """Получает внутренний ID кандидата по его обезличенному ключу."""
    query = "SELECT id FROM candidates WHERE external_id = :key LIMIT 1;"
    df = df_query(query, {"key": candidate_key})
    if df.empty:
        return None
    return df.iloc[0]['id']

def get_embedding_source_info(candidate_key):
    """
    Получает информацию о том, из какой таблицы берутся эмбеддинги.
    Возвращает: 'candidate' или 'candidate_embedding_info'
    """
    candidate_id = get_candidate_id_by_key(candidate_key)
    if not candidate_id:
        return 'unknown'
    
    query_cei = """
        SELECT COUNT(*) as emb_count
        FROM candidate_embedding_info
        WHERE candidate_id = :candidate_id
          AND embedding IS NOT NULL
    """
    df_cei = df_query(query_cei, {"candidate_id": candidate_id})
    
    if not df_cei.empty and df_cei.iloc[0]['emb_count'] > 0:
        return 'candidate_embedding_info'
    else:
        return 'candidate'

def test_candidate(candidate_key):
    """Тестирует одного кандидата"""
    
    print_header(f"FORENSIC ANALYSIS: CANDIDATE {candidate_key}")
    
    df_ecm = get_ecm_data()
    group_map = get_group_mapping()
    
    candidate_row = df_ecm[df_ecm['id'] == candidate_key]
    if candidate_row.empty:
        print(f"ERROR: Candidate {candidate_key} not found in dataset")
        return
    
    ecm_val = candidate_row.iloc[0]['ecm']
    sql_val = candidate_row.iloc[0]['sql']
    group = group_map.get(candidate_key, 'unknown')
    
    print(f"\nCANDIDATE DATA:")
    print(f"   ECM value: {ecm_val:.6f}")
    print(f"   SQL value: {sql_val:.6f}")
    print(f"   Raw difference: {abs(ecm_val - sql_val):.6f}")
    print(f"   Assigned group: {group} (T = {0.76 if group == 'A' else 0.748})")
    
    source = get_embedding_source_info(candidate_key)
    print(f"   Embedding source: {source}")
    
    thresholds = [0.76, 0.748]
    
    print(f"\nFORMULA ANALYSIS:")
    print("-" * 80)
    print(f"{'Formula':<30} {'T':<8} {'Predicted':<15} {'Difference':<15} {'Accuracy':<10}")
    print("-" * 80)
    
    for T in thresholds:
        if sql_val > T:
            pred_correct = (sql_val - T) / (1 - T)
            diff_correct = abs(ecm_val - pred_correct)
            acc_correct = (1 - diff_correct/ecm_val) * 100 if ecm_val > 0 else 0
            marker = "✓" if diff_correct < 0.005 else "⚠" if diff_correct < 0.01 else "✗"
            print(f"{marker} Classic: (x-T)/(1-T)  {T:<8.3f} {pred_correct:<15.6f} {diff_correct:<15.6f} {acc_correct:<10.2f}%")
        
        one_minus_T = 1 - T
        if sql_val > one_minus_T:
            pred_error = (sql_val - one_minus_T) / T
            diff_error = abs(ecm_val - pred_error)
            acc_error = (1 - diff_error/ecm_val) * 100 if ecm_val > 0 else 0
            marker = "✓" if diff_error < 0.005 else "⚠" if diff_error < 0.01 else "✗"
            print(f"{marker} Observed: (x-(1-T))/T  {T:<8.3f} {pred_error:<15.6f} {diff_error:<15.6f} {acc_error:<10.2f}%")
    
    print(f"\nTHRESHOLD BIFURCATION HYPOTHESIS:")
    print("-" * 80)
    
    expected_T = 0.76 if group == 'A' else 0.748
    one_minus_expected = 1 - expected_T
    
    pred_group = (sql_val - one_minus_expected) / expected_T
    diff_group = abs(ecm_val - pred_group)
    acc_group = (1 - diff_group/ecm_val) * 100 if ecm_val > 0 else 0
    
    print(f"   Expected T for group {group}: {expected_T}")
    print(f"   Prediction with group T: {pred_group:.6f}")
    print(f"   Difference: {diff_group:.6f}")
    print(f"   Accuracy: {acc_group:.2f}%")
    
    if diff_group < 0.005:
        print(f"   HYPOTHESIS CONFIRMED: Candidate belongs to group {group}")
    elif diff_group < 0.01:
        print(f"   HYPOTHESIS PARTIALLY CONFIRMED (within 1% margin)")
    else:
        print(f"   HYPOTHESIS REJECTED")

if __name__ == "__main__":
    print("\n" + "="*100)
    print("TESTING GROUP A CANDIDATE")
    print("="*100)
    test_candidate('ECM-00001')
    
    print("\n" + "="*100)
    print("TESTING GROUP B CANDIDATE")
    print("="*100)
    test_candidate('ECM-00003')
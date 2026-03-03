import pandas as pd

def analyze_source_correlation(df_best):
    """Анализирует корреляцию с источником эмбеддинга"""
    results = {}
    
    # Кандидаты с эмбеддингом в candidate
    candidate_emb_mask = df_best['has_candidate_emb'] == True
    candidate_with_emb = df_best[candidate_emb_mask]
    
    results['candidate_table'] = {
        'data': candidate_with_emb[['ID', 'Лучшая комбинация', 'Разница']] if not candidate_with_emb.empty else pd.DataFrame(),
        'mean_diff': candidate_with_emb['Разница'].mean() if not candidate_with_emb.empty else None
    }
    
    # Кандидаты с записями в CEI
    cei_mask = df_best['cei_emb_count'] > 0
    candidate_with_cei = df_best[cei_mask]
    
    results['cei_table'] = {
        'data': candidate_with_cei[['ID', 'Лучшая комбинация', 'Разница', 'cei_emb_count']] if not candidate_with_cei.empty else pd.DataFrame(),
        'mean_diff': candidate_with_cei['Разница'].mean() if not candidate_with_cei.empty else None
    }
    
    # Проблемные кандидаты
    problematic = df_best[df_best['Разница'] > 0.01]
    results['problematic'] = problematic[['ID', 'Разница', 'Лучшая комбинация', 'has_candidate_emb', 'cei_emb_count']] if not problematic.empty else pd.DataFrame()
    
    return results
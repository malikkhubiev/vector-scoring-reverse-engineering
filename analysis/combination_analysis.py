import pandas as pd
import numpy as np
from models.formulas import apply_formula
from analysis.similarity_calculator import calculate_similarities_for_target

def analyze_all_combinations(df_ecm, combinations):
    """Анализирует все комбинации для всех кандидатов"""
    
    # Для каждой комбинации будем собирать результаты
    all_results = []
    
    # Для каждого кандидата как target
    for idx, target_row in df_ecm.iterrows():
        target_key = target_row['ID']
        target_ecm = target_row['ECM']
        
        # Остальные кандидаты
        other_keys = df_ecm[df_ecm['ID'] != target_key]['ID'].tolist()
        
        print(f"\nАнализ для target: {target_key}")
        
        for combo in combinations:
            source = combo['source']
            T = combo['T']
            formula_type = combo['formula']
            
            # Вычисляем реальные схожести из БД для этого target
            similarities = calculate_similarities_for_target(
                target_key, 
                other_keys,
                method=source
            )
            
            if not similarities:
                continue
            
            # Для каждого кандидата считаем предсказание
            for other_key, sql_sim in similarities.items():
                # Находим ECM кандидата
                other_row = df_ecm[df_ecm['ID'] == other_key].iloc[0]
                ecm_val = other_row['ECM']
                
                # Применяем формулу
                pred = apply_formula(sql_sim, T, formula_type)
                
                if not np.isnan(pred):
                    diff = abs(ecm_val - pred)
                    
                    all_results.append({
                        'target': target_key,
                        'candidate': other_key,
                        'source': source,
                        'T': T,
                        'formula_type': formula_type,
                        'combo_name': combo['name'],
                        'sql_similarity': sql_sim,
                        'ecm_value': ecm_val,
                        'predicted': pred,
                        'difference': diff
                    })
    
    return pd.DataFrame(all_results)

def summarize_results(results_df):
    """Суммирует результаты по комбинациям"""
    if results_df.empty:
        return pd.DataFrame()
    
    summary = []
    
    for combo_name in results_df['combo_name'].unique():
        combo_data = results_df[results_df['combo_name'] == combo_name]
        diffs = combo_data['difference']
        
        summary.append({
            'Комбинация': combo_name,
            'Средняя разница': diffs.mean(),
            'Медианная разница': diffs.median(),
            'Мин разница': diffs.min(),
            'Макс разница': diffs.max(),
            'Кол-во измерений': len(diffs),
            'Кол-во < 0.005': len(diffs[diffs < 0.005]),
            'Кол-во < 0.01': len(diffs[diffs < 0.01]),
            'Кол-во < 0.02': len(diffs[diffs < 0.02]),
            'Процент < 0.01': f"{len(diffs[diffs < 0.01])/len(diffs)*100:.1f}%"
        })
    
    return pd.DataFrame(summary).sort_values('Средняя разница')

def find_best_for_each_candidate(results_df):
    """Находит лучшую комбинацию для каждой пары target-candidate"""
    if results_df.empty:
        return pd.DataFrame()
    
    best = []
    
    for (target, candidate), group in results_df.groupby(['target', 'candidate']):
        best_row = group.loc[group['difference'].idxmin()]
        best.append({
            'target': target,
            'candidate': candidate,
            'лучшая_комбинация': best_row['combo_name'],
            'разница': best_row['difference'],
            'sql_similarity': best_row['sql_similarity'],
            'ecm_value': best_row['ecm_value']
        })
    
    return pd.DataFrame(best)
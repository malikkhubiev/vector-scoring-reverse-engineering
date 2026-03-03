import numpy as np
import pandas as pd

def formula_correct(sql, T):
    """Правильная формула: (sql - T) / (1 - T)"""
    if pd.isna(sql) or sql <= T:
        return np.nan
    return (sql - T) / (1 - T)

def formula_error(sql, T):
    """Ошибочная формула: (sql - (1-T)) / T"""
    one_minus_T = 1 - T
    if pd.isna(sql) or sql <= one_minus_T:
        return np.nan
    return (sql - one_minus_T) / T

def get_all_combinations():
    """Возвращает все возможные комбинации для анализа"""
    thresholds = [0.76, 0.748]
    one_minus_thresholds = [1 - t for t in thresholds]
    sources = ['candidate', 'cei_max']
    
    combinations = []
    
    for source in sources:
        for T in thresholds:
            # Правильная формула
            combinations.append({
                'name': f'{source}, T={T}, правильная формула',
                'source': source,
                'T': T,
                'formula': 'correct',
                'desc': f'ECM = (SQL - {T}) / (1 - {T})'
            })
            
            # Ошибочная формула
            combinations.append({
                'name': f'{source}, T={T}, ошибочная формула',
                'source': source,
                'T': T,
                'formula': 'error',
                'desc': f'ECM = (SQL - {1-T}) / {T}'
            })
    
    return combinations

def apply_formula(sql, T, formula_type):
    """Применяет формулу к значению SQL"""
    if formula_type == 'correct':
        return formula_correct(sql, T)
    else:
        return formula_error(sql, T)
import pandas as pd
from config import df_query
import numpy as np

def get_candidate_ids(keys):
    """Получает ID кандидатов по их ключам"""
    if not keys:
        return {}
    
    placeholders = ','.join([f":key{i}" for i in range(len(keys))])
    params = {f"key{i}": key for i, key in enumerate(keys)}
    
    query = f"""
        SELECT key, id 
        FROM test.candidate 
        WHERE key IN ({placeholders})
    """
    
    df = df_query(query, params)
    if df.empty:
        return {}
    
    return dict(zip(df['key'], df['id']))

def get_candidate_embeddings(keys):
    """Получает эмбеддинги из таблицы candidate (метод 1)"""
    if not keys:
        return {}
    
    placeholders = ','.join([f":key{i}" for i in range(len(keys))])
    params = {f"key{i}": key for i, key in enumerate(keys)}
    
    query = f"""
        SELECT 
            key,
            embedding
        FROM test.candidate 
        WHERE key IN ({placeholders})
          AND embedding IS NOT NULL
    """
    
    df = df_query(query, params)
    if df.empty:
        return {}
    
    return dict(zip(df['key'], df['embedding']))

def get_cei_embeddings_with_max(candidate_ids):
    """Получает MAX схожесть из candidate_embedding_info (метод 2)"""
    if not candidate_ids:
        return {}, {}
    
    keys_by_id = {v: k for k, v in candidate_ids.items()}
    id_list = list(candidate_ids.values())
    
    if not id_list:
        return {}, {}
    
    placeholders = ','.join([f":id{i}" for i in range(len(id_list))])
    params = {f"id{i}": id_val for i, id_val in enumerate(id_list)}
    
    # Для каждого кандидата нужно будет вычислить схожесть отдельно
    # Здесь мы только получаем информацию о наличии эмбеддингов
    query = f"""
        SELECT 
            candidate_id,
            COUNT(*) as emb_count
        FROM candidate_embedding_info
        WHERE candidate_id IN ({placeholders})
          AND embedding IS NOT NULL
        GROUP BY candidate_id
    """
    
    df = df_query(query, params)
    if df.empty:
        return {}, {}
    
    result = {}
    for _, row in df.iterrows():
        candidate_id = row['candidate_id']
        key = keys_by_id.get(candidate_id)
        if key:
            result[key] = {
                'emb_count': row['emb_count']
            }
    
    return result, keys_by_id
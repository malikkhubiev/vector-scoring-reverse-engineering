import pandas as pd
import numpy as np
from config import df_query
from data.candidate_info import get_candidate_ids, get_candidate_embeddings

def format_vector_for_query(embedding):
    """Преобразует эмбеддинг в формат для SQL запроса"""
    import json
    import ast
    
    if embedding is None:
        return None
        
    if isinstance(embedding, str):
        try:
            embedding = json.loads(embedding)
        except:
            try:
                embedding = ast.literal_eval(embedding)
            except:
                return None
    elif isinstance(embedding, np.ndarray):
        embedding = embedding.tolist()
    
    if isinstance(embedding, list):
        return '[' + ','.join(str(x) for x in embedding) + ']'
    return None

def calculate_similarities_for_target(target_key, candidate_keys, method='candidate'):
    """
    Вычисляет схожесть между target_key и каждым кандидатом из списка
    
    method: 'candidate' - прямой поиск по таблице candidate
            'cei_max' - поиск по candidate_embedding_info с MAX
    """
    # Получаем ID всех кандидатов
    all_keys = [target_key] + candidate_keys
    key_to_id = get_candidate_ids(all_keys)
    
    if target_key not in key_to_id:
        print(f"Target {target_key} не найден")
        return {}
    
    target_id = key_to_id[target_key]
    
    if method == 'candidate':
        return calculate_similarities_candidate(target_key, candidate_keys, key_to_id)
    else:
        return calculate_similarities_cei_max(target_id, candidate_keys, key_to_id)

def calculate_similarities_candidate(target_key, candidate_keys, key_to_id):
    """Метод 1: прямой поиск по таблице candidate"""
    # Получаем эмбеддинг target
    query_target = """
        SELECT embedding 
        FROM test.candidate 
        WHERE key = :key
    """
    df_target = df_query(query_target, {"key": target_key})
    
    if df_target.empty or df_target.iloc[0]['embedding'] is None:
        return {}
    
    target_emb = df_target.iloc[0]['embedding']
    target_emb_str = format_vector_for_query(target_emb)
    
    if target_emb_str is None:
        return {}
    
    # Получаем схожесть со всеми кандидатами
    placeholders = ','.join([f":key{i}" for i in range(len(candidate_keys))])
    params = {f"key{i}": key for i, key in enumerate(candidate_keys)}
    
    query = f"""
        SELECT 
            key,
            1 - (embedding <=> '{target_emb_str}') as similarity
        FROM test.candidate 
        WHERE key IN ({placeholders})
          AND embedding IS NOT NULL
    """
    
    df = df_query(query, params)
    if df.empty:
        return {}
    
    return dict(zip(df['key'], df['similarity']))

def calculate_similarities_cei_max(target_id, candidate_keys, key_to_id):
    """Метод 2: поиск по candidate_embedding_info с MAX"""
    # Получаем эмбеддинг target из candidate (для сравнения)
    query_target = """
        SELECT embedding 
        FROM test.candidate 
        WHERE id = :id
    """
    df_target = df_query(query_target, {"id": target_id})
    
    if df_target.empty or df_target.iloc[0]['embedding'] is None:
        return {}
    
    target_emb = df_target.iloc[0]['embedding']
    target_emb_str = format_vector_for_query(target_emb)
    
    if target_emb_str is None:
        return {}
    
    # Получаем ID кандидатов
    candidate_ids = [key_to_id[key] for key in candidate_keys if key in key_to_id]
    
    if not candidate_ids:
        return {}
    
    placeholders = ','.join([f":id{i}" for i in range(len(candidate_ids))])
    params = {f"id{i}": id_val for i, id_val in enumerate(candidate_ids)}
    
    # Запрос с MAX и группировкой
    query = f"""
        SELECT 
            c.key,
            MAX(1 - (cei.embedding <=> '{target_emb_str}')) as max_similarity
        FROM candidate_embedding_info cei
        JOIN test.candidate c ON c.id = cei.candidate_id
        WHERE cei.candidate_id IN ({placeholders})
          AND cei.embedding IS NOT NULL
        GROUP BY c.key, c.id
    """
    
    df = df_query(query, params)
    if df.empty:
        return {}
    
    return dict(zip(df['key'], df['max_similarity']))
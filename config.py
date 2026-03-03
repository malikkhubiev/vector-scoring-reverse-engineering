import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Параметры подключения
DB_PARAMS = {
    'host': 'db-host',
    'port': 5432,
    'database': 'database',
    'user': 'username',
    'password': 'password'
}

# Создаем подключение
connection_string = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
engine = create_engine(connection_string)

def df_query(query, params=None):
    """Выполнение запроса с возвратом DataFrame"""
    try:
        with engine.connect() as conn:
            if params:
                return pd.read_sql(text(query), conn, params=params)
            else:
                return pd.read_sql(text(query), conn)
    except SQLAlchemyError as e:
        print(f"❌ Database query error: {e}")
        print(f"Query: {query}")
        if params:
            print(f"Parameters: {params}")
        return pd.DataFrame()
from database import Base, engine
from sqlalchemy import inspect
from sqlalchemy import Table, MetaData

metadata = MetaData()
users_table = Table('users', metadata, autoload_with=engine)
print(users_table.columns.keys())

inspector = inspect(engine)  # Используйте ваш объект engine
columns = inspector.get_columns('users')
print("Columns in 'users':", [column['name'] for column in columns])

# Создание всех таблиц
Base.metadata.create_all(engine)
print("Таблицы успешно созданы!")
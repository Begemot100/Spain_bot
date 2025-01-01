# Базовый образ Python
FROM python:3.11

# Устанавливаем рабочую директорию в контейнере
WORKDIR /handlers.py

# Копируем все файлы проекта в контейнер
COPY . /handlers.py

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем команду для запуска приложения (если у вас есть файл app.py или основной файл, который запускает Flask)
CMD ["python", "src/handlers.py"]
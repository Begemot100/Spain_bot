import psycopg2

try:
    conn = psycopg2.connect(
        dbname="railway",
        user="postgres",
        host="roundhouse.proxy.rlwy.net",
        port="42541"
    )
    print("Успешное подключение к базе данных!")
    conn.close()
except Exception as e:
    print("Ошибка подключения к базе данных:", e)

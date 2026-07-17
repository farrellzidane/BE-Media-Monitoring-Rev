import sqlite3

conn = sqlite3.connect(
    "data/articles.db"
)

cur = conn.cursor()

cur.execute(
    "SELECT COUNT(*) FROM articles"
)

print(
    cur.fetchone()[0]
)

conn.close()

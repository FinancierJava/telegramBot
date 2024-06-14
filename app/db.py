# db.py
import sqlite3

conn = sqlite3.connect('hangman.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS scores (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT,
    score INTEGER
)
''')
conn.commit()


async def save_score(player_id, player_name, points):
    cursor.execute('SELECT score FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()

    if row:
        current_score = row[0]
        new_score = current_score + points
        cursor.execute('UPDATE scores SET score = ? WHERE player_id = ?', (new_score, player_id))
    else:
        cursor.execute('INSERT INTO scores (player_id, player_name, score) VALUES (?, ?, ?)',
                       (player_id, player_name, points))

    conn.commit()


async def get_score(player_id):
    cursor.execute('SELECT score FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None


async def get_top_scores(limit=10):
    cursor.execute('SELECT player_name, score FROM scores ORDER BY score DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    return rows

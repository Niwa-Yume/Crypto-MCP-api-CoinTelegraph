#!/bin/bash

pip install -r requirements.txt

python -c "
import sqlite3
from pathlib import Path

# Créer la base de données articles si elle n'existe pas
if not Path('articles.db').exists():
    conn = sqlite3.connect('articles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            lien TEXT UNIQUE NOT NULL,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print('Base de données articles.db créée')

# Créer la base de données leaderboard si elle n'existe pas
if not Path('leaderboard.db').exists():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER NOT NULL,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print('Base de données leaderboard.db créée')
"

echo "Setup terminé !"

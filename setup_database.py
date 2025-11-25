import sqlite3

# créer le fichier articles.db
conn = sqlite3.connect("articles.db")
cursor = conn.cursor()

print("Base de données connectée/créée.")

# on fait la table

sql_creation_table = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT,
    lien TEXT UNIQUE,
    contenu_ia TEXT,
    date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

cursor.execute(sql_creation_table)
print("Table 'articles' vérifiée/créée.")

# on close tout
conn.commit()
conn.close()
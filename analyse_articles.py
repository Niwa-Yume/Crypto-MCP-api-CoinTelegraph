from dotenv import load_dotenv
import os
import json
import google.generativeai as genai
from collections import defaultdict
import time
import sqlite3

# --- CONFIG GEMINI (Inchangé) ---
load_dotenv()
GEMINI_API_KEY = os.getenv("API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("Clé GEMINI_API_KEY introuvable.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    "gemini-2.5-flash-lite",
    generation_config={"response_mime_type": "application/json"}
)

#co a la bdd
conn = sqlite3.connect("articles.db")
cursor = conn.cursor()

print("Connexion à la base de données réussie.")

#recup de la data
cursor.execute("SELECT contenu_ia FROM articles")

# fetchall() récupère TOUS les résultats de la requête d'un coup
rows = cursor.fetchall()

print(f"{len(rows)} articles trouvés dans la base de données.")

crypto_scores = defaultdict(int)
crypto_names = {}

for i, row in enumerate(rows):
    text_to_analyze = row[0]

    print(f"Traitement article {i + 1}/{len(rows)}...")

    prompt = f"""
    Tu es un expert crypto. Analyse ce texte et extrais les crypto-monnaies mentionnées.

    Règles :
    1. Ignore les termes génériques.
    2. Ignore les entreprises sauf token.
    3. Renvoie une liste vide si rien.

    Format JSON : {{ "coins": [{{"name": "Bitcoin", "symbol": "BTC"}}] }}

    Texte :
    "{text_to_analyze}"
    """

    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        found_coins = data.get("coins", [])

        if found_coins:
            print(f"   -> Trouvé : {', '.join([c['symbol'] for c in found_coins])}")
        else:
            print("   -> Rien.")

        # score d'itération
        for coin in found_coins:
            symbol = coin['symbol'].upper().strip()
            name = coin['name'].strip()
            if 2 <= len(symbol) <= 8:
                crypto_scores[symbol] += 1
                crypto_names[symbol] = name

        # temps de pause entre les requêtes en secondes
        time.sleep(4)

    except Exception as e:
        print(f"   ⚠️ Erreur : {e}")


conn.close()

# --- LEADERBOARD ---
leaderboard = []
for symbol, count in crypto_scores.items():
    leaderboard.append({
        "name": crypto_names.get(symbol, symbol),
        "symbol": symbol,
        "count": count,
    })

# Tri et classement
leaderboard.sort(key=lambda x: x['count'], reverse=True)
for rank, item in enumerate(leaderboard, 1):
    item['rank'] = rank


conn_lb = sqlite3.connect("leaderboard.db")
cursor_lb = conn_lb.cursor()

# Création de la table si elle n'existe pas déja
cursor_lb.execute("""
    CREATE TABLE IF NOT EXISTS classement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rank INTEGER,
        symbol TEXT,
        name TEXT,
        count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")


# insertion en vdd
for item in leaderboard:
    cursor_lb.execute(
        "INSERT INTO classement (rank, symbol, name, count) VALUES (?, ?, ?, ?)",
        (item['rank'], item['symbol'], item['name'], item['count'])
    )

conn_lb.commit()
conn_lb.close()

print("\n--- TOP 5 CRYPTOS ---")
print(json.dumps(leaderboard[:5], indent=2))
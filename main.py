
#recupération des articles
import feedparser
import json
import ssl
from bs4 import BeautifulSoup

# --- correction erreur SSL ---
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

rss_url = "https://cointelegraph.com/rss"
feed = feedparser.parse(rss_url)

articles = []

print(f"Récupération de {len(feed.entries)} articles...")

for entry in feed.entries[:50]:
    # 1. On récupère le contenu brut
    raw_summary = entry.summary

    # 2. On nettoie
    soup = BeautifulSoup(raw_summary, "html.parser")
    clean_summary = soup.get_text(separator=" ").strip()

    # 3. On construit le texte pour l'IA (Titre + Résumé propre)
    full_text = f"Titre: {entry.title}\nRésumé: {clean_summary}"

    articles.append({
        "text_for_ai": full_text,
        "original_link": entry.link
    })

# Exemple de résultat propre
print("-" * 40)
print("EXEMPLE DE TEXTE NETTOYÉ POUR L'IA :")
print(articles[0]['text_for_ai'])
print("-" * 40)

# Sauvegarde
with open("articles_clean.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)


# on va demander a l'ia de recup les articles_clean.json et des les parses pour
# extraire les crypto-monnaies mentionnées dans ce texte. Pour chaque
# crypto, donne-moi son nom complet et son symbole boursier (Ticker)
# standard (ex: BTC, ETH). Retourne un JSON avec un classement des crypto qui sont sorti le plus de fois et faire un leaderboard.
#python


from dotenv import load_dotenv
import os
import json
import google.generativeai as genai
from collections import defaultdict
import time
# --- CONFIG GEMINI ---
load_dotenv() #charge le .env
GEMINI_API_KEY = os.getenv("API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("Clé GEMINI_API_KEY introuvable dans le fichier `.env`")

genai.configure(api_key=GEMINI_API_KEY)

# On fait la sélection du modèle
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    # Cette option force Gemini à répondre DIRECTEMENT en JSON
    generation_config={"response_mime_type": "application/json"}
)

# --- 2. data ---
try:
    with open("articles_clean.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
except FileNotFoundError:
    articles = []

crypto_scores = defaultdict(int)
crypto_names = {}

# --- 3. BOUCLE D'ANALYSE ---
for i, article in enumerate(articles):
    print(f"Traitement article {i + 1}/{len(articles)}...")

    # Prompt adapté pour Gemini
    prompt = f"""
    Tu es un expert crypto. Analyse ce texte et extrais les crypto-monnaies mentionnées.

    Règles :
    1. Ignore les termes génériques (Crypto, DeFi, Blockchain).
    2. Ignore les entreprises (Binance, Coinbase) sauf si on parle de leur token.
    3. Si aucune crypto n'est trouvée, renvoie une liste vide.

    Format de réponse JSON attendu :
    {{
        "coins": [
            {{"name": "Bitcoin", "symbol": "BTC"}},
            {{"name": "Ethereum", "symbol": "ETH"}}
        ]
    }}

    Texte à analyser :
    "{article['text_for_ai']}"
    """

    try:
        # Appel API (input)
        response = model.generate_content(prompt)

        # Gemini output
        data = json.loads(response.text)

        found_coins = data.get("coins", [])

        if found_coins:
            print(f"   -> Trouvé : {', '.join([c['symbol'] for c in found_coins])}")
        else:
            print("   -> Rien.")

        # Comptage des scores
        for coin in found_coins:
            symbol = coin['symbol'].upper().strip()
            name = coin['name'].strip()

            # Filtre basique
            if 2 <= len(symbol) <= 8:
                crypto_scores[symbol] += 1
                crypto_names[symbol] = name

        # Petite pause pour être gentil avec l'API gratuite (optionnel)
        time.sleep(0.5)

    except Exception as e:
        print(f"   ⚠️ Erreur API : {e}")

# --- 4. LEADERBOARD & SAUVEGARDE ---
leaderboard = []

for symbol, count in crypto_scores.items():
    leaderboard.append({
        "name": crypto_names.get(symbol, symbol),
        "symbol": symbol,
        "count": count,
    })

# Tri par popularité
leaderboard.sort(key=lambda x: x['count'], reverse=True)

# Ajout du rang
for rank, item in enumerate(leaderboard, 1):
    item['rank'] = rank

print(json.dumps(leaderboard[:5], indent=2))

with open("crypto_leaderboard.json", "w", encoding="utf-8") as f:
    json.dump(leaderboard, f, ensure_ascii=False, indent=2)

print("Leaderboard généré :", leaderboard[:10])



import feedparser
import ssl
from bs4 import BeautifulSoup
import sqlite3

# --- soucsi ssl ---
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# On se connecte au fichier bdd
conn = sqlite3.connect("articles.db")
cursor = conn.cursor()

rss_url = "https://cointelegraph.com/rss"
feed = feedparser.parse(rss_url)

print(f"Récupération de {len(feed.entries)} articles...")

count_new = 0  # nb de nouveau articles

for entry in feed.entries[:50]:
    raw_summary = entry.summary
    soup = BeautifulSoup(raw_summary, "html.parser")
    clean_summary = soup.get_text(separator=" ").strip()
    full_text = f"Titre: {entry.title}\nRésumé: {clean_summary}"

    try:
        # Les '?' sont des paniers vides que Python va remplir avec tes variables.
        sql = "INSERT INTO articles (titre, lien, contenu_ia) VALUES (?, ?, ?)"

        cursor.execute(sql, (entry.title, entry.link, full_text))

        print(f"[OK] Ajouté : {entry.title[:50]}...")
        count_new += 1

    except sqlite3.IntegrityError:
        # si l'article existe déjà, SQLite crie "Erreur ! et on ignore la lige".
        print(f"[DOUBLON] Ignoré : {entry.title[:30]}...")


# Très important : Si tu ne fais pas commit, rien n'est sauvegardé !
conn.commit()
conn.close()

print("-" * 40)
print(f"Terminé ! {count_new} nouveaux articles ajoutés dans articles.db")
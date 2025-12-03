from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
import feedparser
import ssl
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration des chemins
SCRIPT_DIR = Path(__file__).parent
ARTICLES_DB_PATH = SCRIPT_DIR / "articles.db"
LEADERBOARD_DB_PATH = SCRIPT_DIR / "leaderboard.db"

# Correction SSL
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# Création de l'API
app = FastAPI(
    title="Crypto Leaderboard API",
    description="API pour consulter le classement des cryptomonnaies basé sur les articles",
    version="1.0.0"
)

# CORS pour permettre les requêtes depuis n'importe quelle origine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic
class CryptoLeaderboard(BaseModel):
    rank: int
    name: str
    symbol: str
    count: int
    created_at: Optional[str] = None

class Article(BaseModel):
    id: int
    titre: str
    lien: str
    date_ajout: str

class StatsResponse(BaseModel):
    total_articles: int
    total_cryptos: int
    last_update: Optional[str]

# Routes API

@app.get("/")
def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Bienvenue sur l'API Crypto Leaderboard",
        "version": "1.0.0",
        "endpoints": {
            "/leaderboard": "Obtenir le classement des cryptos",
            "/leaderboard/{symbol}": "Obtenir les détails d'une crypto",
            "/articles": "Liste des articles",
            "/stats": "Statistiques globales",
            "/health": "Status de l'API"
        }
    }

@app.get("/health")
def health_check():
    """Vérifier que l'API fonctionne"""
    try:
        # Vérifier la connexion aux bases de données
        conn_articles = sqlite3.connect(str(ARTICLES_DB_PATH))
        conn_articles.close()

        conn_leaderboard = sqlite3.connect(str(LEADERBOARD_DB_PATH))
        conn_leaderboard.close()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "databases": {
                "articles": "connected",
                "leaderboard": "connected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/leaderboard", response_model=List[CryptoLeaderboard])
def get_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="Nombre de résultats à retourner"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination")
):
    """
    Récupérer le classement des cryptomonnaies

    - **limit**: Nombre de résultats (max 100)
    - **offset**: Position de départ pour la pagination
    """
    try:
        if not LEADERBOARD_DB_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Base de données introuvable à : {LEADERBOARD_DB_PATH}"
            )

        conn = sqlite3.connect(str(LEADERBOARD_DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rank, name, symbol, count, created_at 
            FROM classement 
            ORDER BY rank 
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        results = [
            {
                "rank": row[0],
                "name": row[1],
                "symbol": row[2],
                "count": row[3],
                "created_at": row[4] if len(row) > 4 else None
            }
            for row in rows
        ]

        return results

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.get("/leaderboard/{symbol}", response_model=CryptoLeaderboard)
def get_crypto_by_symbol(symbol: str):
    """
    Récupérer les informations d'une cryptomonnaie spécifique

    - **symbol**: Le symbole de la crypto (ex: BTC, ETH)
    """
    try:
        conn = sqlite3.connect(str(LEADERBOARD_DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rank, name, symbol, count, created_at 
            FROM classement 
            WHERE UPPER(symbol) = UPPER(?)
            ORDER BY created_at DESC
            LIMIT 1
        """, (symbol,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Cryptomonnaie '{symbol}' non trouvée dans le classement"
            )

        return {
            "rank": row[0],
            "name": row[1],
            "symbol": row[2],
            "count": row[3],
            "created_at": row[4] if len(row) > 4 else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/articles", response_model=List[Article])
def get_articles(
    limit: int = Query(20, ge=1, le=100, description="Nombre d'articles à retourner"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination")
):
    """
    Récupérer la liste des articles

    - **limit**: Nombre d'articles (max 100)
    - **offset**: Position de départ pour la pagination
    """
    try:
        if not ARTICLES_DB_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="Base de données des articles introuvable"
            )

        conn = sqlite3.connect(str(ARTICLES_DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, titre, lien, date_ajout 
            FROM articles 
            ORDER BY date_ajout DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "titre": row[1],
                "lien": row[2],
                "date_ajout": row[3]
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Récupérer les statistiques globales
    """
    try:
        stats = {}

        # Compter les articles
        if ARTICLES_DB_PATH.exists():
            conn_articles = sqlite3.connect(str(ARTICLES_DB_PATH))
            cursor_articles = conn_articles.cursor()
            cursor_articles.execute("SELECT COUNT(*) FROM articles")
            stats["total_articles"] = cursor_articles.fetchone()[0]

            cursor_articles.execute("SELECT MAX(date_ajout) FROM articles")
            last_update = cursor_articles.fetchone()[0]
            stats["last_update"] = last_update
            conn_articles.close()
        else:
            stats["total_articles"] = 0
            stats["last_update"] = None

        # Compter les cryptos
        if LEADERBOARD_DB_PATH.exists():
            conn_leaderboard = sqlite3.connect(str(LEADERBOARD_DB_PATH))
            cursor_leaderboard = conn_leaderboard.cursor()
            cursor_leaderboard.execute("SELECT COUNT(DISTINCT symbol) FROM classement")
            stats["total_cryptos"] = cursor_leaderboard.fetchone()[0]
            conn_leaderboard.close()
        else:
            stats["total_cryptos"] = 0

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/refresh-articles")
def refresh_articles():
    """
    Récupérer de nouveaux articles depuis le flux RSS
    """
    try:
        rss_url = "https://cointelegraph.com/rss"
        feed = feedparser.parse(rss_url)

        conn = sqlite3.connect(str(ARTICLES_DB_PATH))
        cursor = conn.cursor()

        # Créer la table si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                lien TEXT UNIQUE NOT NULL,
                contenu_ia TEXT,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        count_new = 0
        count_existing = 0

        for entry in feed.entries[:50]:
            raw_summary = entry.summary
            soup = BeautifulSoup(raw_summary, "html.parser")
            clean_summary = soup.get_text(separator=" ").strip()
            full_text = f"Titre: {entry.title}\nRésumé: {clean_summary}"

            try:
                cursor.execute(
                    "INSERT INTO articles (titre, lien, contenu_ia) VALUES (?, ?, ?)",
                    (entry.title, entry.link, full_text)
                )
                count_new += 1
            except sqlite3.IntegrityError:
                count_existing += 1

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Récupération terminée",
            "total_fetched": len(feed.entries[:50]),
            "new_articles": count_new,
            "existing_articles": count_existing
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


from fastmcp import FastMCP
import sqlite3

# on créer le serv
mcp = FastMCP("CryptoLeaderboard")


@mcp.tool()    #définit la fonction comme publique en java
def lire_classement_crypto(limit: int = 5) -> str:
    try:
        conn = sqlite3.connect("leaderboard.db") #ouvre la db leaderboard
        cursor = conn.cursor() # sert a exectuer les commandes sql fournit de base

        cursor.execute("SELECT rank, name, symbol, count FROM classement ORDER BY rank LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "Aucune donnée trouvée."

        resultat = "Voici le classement actuel :\n"
        for row in rows:
            resultat += f"#{row[0]} {row[1]} ({row[2]}) - Mentionné {row[3]} fois\n"

        return resultat

    except Exception as e:
        return f"Erreur lors de la lecture de la DB : {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="http", port=8000) #lance le serveur
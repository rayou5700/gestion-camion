import sqlite3
import os

DB_NAME = "donnees.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trajets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            plaque TEXT,
            chauffeur TEXT,
            km_depart REAL,
            km_arrivee REAL,
            km_parcourus REAL,
            nb_pleins INTEGER,
            litres_ajoutes REAL,
            prix_litre REAL,
            colis_transportes INTEGER,
            colis_livres_client INTEGER,
            colis_livres_relais INTEGER,
            niveau_carburant_fin REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicules (
            plaque TEXT PRIMARY KEY,
            capacite_reservoir REAL,
            conso_moyenne REAL DEFAULT 30.0
        )
    """)
    conn.commit()
    conn.close()

def ajouter_trajet(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO trajets 
        (date, plaque, chauffeur, km_depart, km_arrivee, km_parcourus, 
         nb_pleins, litres_ajoutes, prix_litre, colis_transportes, 
         colis_livres_client, colis_livres_relais, niveau_carburant_fin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["date"], data["plaque"], data.get("chauffeur", ""),
        data["km_depart"], data["km_arrivee"], data["km_parcourus"],
        data["nb_pleins"], data["litres_ajoutes"], data.get("prix_litre", 0),
        data["colis_transportes"], data.get("colis_livres_client", 0),
        data.get("colis_livres_relais", 0), data["niveau_carburant_fin"]
    ))
    conn.commit()
    conn.close()

def get_trajets(plaque=None, mois=None, annee=None, limite=500):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = "SELECT * FROM trajets WHERE 1=1"
    params = []

    if plaque:
        query += " AND plaque=?"
        params.append(plaque)
    if mois and mois != "Tous":
        query += " AND strftime('%m', date) = ?"
        params.append(f"{int(mois):02d}")
    if annee and annee != "Toutes":
        query += " AND strftime('%Y', date) = ?"
        params.append(str(annee))

    query += " ORDER BY date DESC LIMIT ?"
    params.append(limite)

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_toutes_plaques():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT plaque FROM trajets ORDER BY plaque")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def get_toutes_annees():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT strftime('%Y', date) FROM trajets ORDER BY date DESC")
    rows = [r[0] for r in c.fetchall() if r[0]]
    conn.close()
    return rows

def get_vehicule(plaque):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM vehicules WHERE plaque=?", (plaque,))
    row = c.fetchone()
    conn.close()
    return row

def save_vehicule(plaque, capacite, conso):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicules (plaque, capacite_reservoir, conso_moyenne)
        VALUES (?, ?, ?)
        ON CONFLICT(plaque) DO UPDATE SET
            capacite_reservoir=excluded.capacite_reservoir,
            conso_moyenne=excluded.conso_moyenne
    """, (plaque, capacite, conso))
    conn.commit()
    conn.close()

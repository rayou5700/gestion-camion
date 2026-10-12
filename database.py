import sqlite3
import os

DB_NAME = "donnees.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trajets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, plaque TEXT, km_depart REAL, km_arrivee REAL,
            km_parcourus REAL, nb_pleins INTEGER, litres_ajoutes REAL,
            colis_transportes INTEGER, colis_livres INTEGER,
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
        (date, plaque, km_depart, km_arrivee, km_parcourus, nb_pleins, 
         litres_ajoutes, colis_transportes, colis_livres, niveau_carburant_fin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data["date"], data["plaque"], data["km_depart"], data["km_arrivee"],
          data["km_parcourus"], data["nb_pleins"], data["litres_ajoutes"],
          data["colis_transportes"], data["colis_livres"], data["niveau_carburant_fin"]))
    conn.commit()
    conn.close()

def get_trajets(plaque=None, limite=50):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if plaque:
        c.execute("SELECT * FROM trajets WHERE plaque=? ORDER BY date DESC LIMIT ?", (plaque, limite))
    else:
        c.execute("SELECT * FROM trajets ORDER BY date DESC LIMIT ?", (limite,))
    rows = c.fetchall()
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

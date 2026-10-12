import sqlite3
import os

DB_NAME = "donnees.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Table trajets (avec photo et heures)
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
            colis_non_livres INTEGER DEFAULT 0,
            niveau_carburant_fin REAL,
            photo_depart TEXT,
            photo_arrivee TEXT,
            heure_debut TEXT,
            heure_fin TEXT,
            valide INTEGER DEFAULT 0
        )
    """)

    # Table vehicules
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicules (
            plaque TEXT PRIMARY KEY,
            capacite_reservoir REAL,
            conso_moyenne REAL DEFAULT 30.0
        )
    """)

    # Table utilisateurs
    c.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            nom_complet TEXT
        )
    """)

    # Table conges
    c.execute("""
        CREATE TABLE IF NOT EXISTS conges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chauffeur TEXT,
            date_debut TEXT,
            date_fin TEXT,
            motif TEXT
        )
    """)

    # Table planning
    c.execute("""
        CREATE TABLE IF NOT EXISTS planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            chauffeur TEXT,
            plaque TEXT,
            description TEXT
        )
    """)

            # Créer admin serhane s'il n'existe pas
    c.execute("SELECT COUNT(*) FROM utilisateurs WHERE username='serhane'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO utilisateurs VALUES (?, ?, ?, ?)",
                  ("serhane", "stef57340", "admin", "Serhane"))

    conn.commit()
    conn.close()

# ============ TRAJETS ============
def ajouter_trajet(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO trajets 
        (date, plaque, chauffeur, km_depart, km_arrivee, km_parcourus, 
         nb_pleins, litres_ajoutes, prix_litre, colis_transportes, 
         colis_livres_client, colis_livres_relais, colis_non_livres,
         niveau_carburant_fin, photo_depart, photo_arrivee, 
         heure_debut, heure_fin, valide)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["date"], data["plaque"], data.get("chauffeur", ""),
        data["km_depart"], data["km_arrivee"], data["km_parcourus"],
        data["nb_pleins"], data["litres_ajoutes"], data.get("prix_litre", 0),
        data["colis_transportes"], data.get("colis_livres_client", 0),
        data.get("colis_livres_relais", 0), data.get("colis_non_livres", 0),
        data["niveau_carburant_fin"], data.get("photo_depart", ""),
        data.get("photo_arrivee", ""), data.get("heure_debut", ""),
        data.get("heure_fin", ""), data.get("valide", 0)
    ))
    conn.commit()
    conn.close()

def valider_trajet(trajet_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE trajets SET valide=1 WHERE id=?", (trajet_id,))
    conn.commit()
    conn.close()

def get_trajets(plaque=None, mois=None, annee=None, chauffeur=None, limite=500):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = "SELECT * FROM trajets WHERE 1=1"
    params = []

    if plaque:
        query += " AND plaque=?"
        params.append(plaque)
    if chauffeur:
        query += " AND chauffeur=?"
        params.append(chauffeur)
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

def get_trajet_by_id(trajet_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM trajets WHERE id=?", (trajet_id,))
    row = c.fetchone()
    conn.close()
    return row

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

def get_tous_chauffeurs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT chauffeur FROM trajets WHERE chauffeur != '' ORDER BY chauffeur")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

# ============ VEHICULES ============
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

# ============ UTILISATEURS ============
def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM utilisateurs WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def get_tous_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM utilisateurs ORDER BY role DESC, username")
    rows = c.fetchall()
    conn.close()
    return rows

def creer_user(username, password, role, nom_complet):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO utilisateurs VALUES (?, ?, ?, ?)
    """, (username, password, role, nom_complet))
    conn.commit()
    conn.close()

def supprimer_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM utilisateurs WHERE username=?", (username,))
    conn.commit()
    conn.close()

# ============ CONGES ============
def ajouter_conge(chauffeur, date_debut, date_fin, motif):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO conges (chauffeur, date_debut, date_fin, motif)
        VALUES (?, ?, ?, ?)
    """, (chauffeur, date_debut, date_fin, motif))
    conn.commit()
    conn.close()

def get_conges(chauffeur=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if chauffeur:
        c.execute("SELECT * FROM conges WHERE chauffeur=? ORDER BY date_debut DESC", (chauffeur,))
    else:
        c.execute("SELECT * FROM conges ORDER BY date_debut DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def supprimer_conge(conge_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM conges WHERE id=?", (conge_id,))
    conn.commit()
    conn.close()

# ============ PLANNING ============
def ajouter_planning(date, chauffeur, plaque, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO planning (date, chauffeur, plaque, description)
        VALUES (?, ?, ?, ?)
    """, (date, chauffeur, plaque, description))
    conn.commit()
    conn.close()

def get_planning(semaine_debut=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if semaine_debut:
        c.execute("""
            SELECT * FROM planning 
            WHERE date >= ? AND date < date(?, '+7 days')
            ORDER BY date
        """, (semaine_debut, semaine_debut))
    else:
        c.execute("SELECT * FROM planning ORDER BY date DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    return rows

def supprimer_planning(planning_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM planning WHERE id=?", (planning_id,))
    conn.commit()
    conn.close()

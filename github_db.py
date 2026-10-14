import os
import base64
import requests
import streamlit as st

GITHUB_USER = "rayou5700"
GITHUB_REPO = "gestion-camion"
DB_FILE = "donnees.db"

def get_github_token():
    try:
        return st.secrets["GITHUB_TOKEN"]
    except:
        return os.environ.get("GITHUB_TOKEN", "")

def telecharger_db():
    """Télécharge la base depuis GitHub avec retry."""
    token = get_github_token()
    if not token:
        print("⚠️ Pas de token GitHub")
        return False

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {token}"}

    # 3 tentatives
    for tentative in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                contenu = base64.b64decode(data["content"])
                with open(DB_FILE, "wb") as f:
                    f.write(contenu)
                print(f"✅ Base téléchargée ({len(contenu)} octets)")
                return True
            elif r.status_code == 404:
                print("ℹ️ Base pas encore sur GitHub")
                return False
            else:
                print(f"⚠️ Tentative {tentative+1}/3 : HTTP {r.status_code}")
        except Exception as e:
            print(f"⚠️ Tentative {tentative+1}/3 : {e}")
    
    print("❌ Échec du téléchargement après 3 tentatives")
    return False

def upload_db(commit_message="Mise à jour base"):
    """Envoie la base locale vers GitHub."""
    token = get_github_token()
    if not token:
        return False

    if not os.path.exists(DB_FILE):
        return False

    with open(DB_FILE, "rb") as f:
        contenu = f.read()

    contenu_b64 = base64.b64encode(contenu).decode()
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {token}"}

    for tentative in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            sha = r.json().get("sha") if r.status_code == 200 else None

            data = {"message": commit_message, "content": contenu_b64}
            if sha:
                data["sha"] = sha

            r = requests.put(url, headers=headers, json=data, timeout=10)
            if r.status_code in (200, 201):
                print("✅ Base sauvegardée")
                return True
            else:
                print(f"⚠️ Tentative {tentative+1}/3 upload : HTTP {r.status_code}")
        except Exception as e:
            print(f"⚠️ Tentative {tentative+1}/3 : {e}")
    
    print("❌ Échec de l'upload")
    return False

def init_sync():
    """Télécharge la base au démarrage - FORCE l'écrasement."""
    # Supprimer la base locale si elle existe
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print("🗑️ Ancienne base supprimée")
        except:
            pass
    
    # Télécharger la nouvelle
    return telecharger_db()

def upload_force():
    return upload_db("Sauvegarde manuelle")

import streamlit as st
from datetime import datetime
import pandas as pd
from database import (init_db, ajouter_trajet, get_trajets, get_vehicule,
                      save_vehicule, get_toutes_plaques, get_toutes_annees)
from calculs import (calculer_km, estimer_carburant_restant,
                     calculer_moyennes, calculer_cout_gasoil, get_col)

st.set_page_config(
    page_title="Gestion Camion",
    page_icon="🚛",
    layout="wide"
)

init_db()

st.title("🚛 Gestion Trajets & Carburant")
st.markdown("Enregistre tes trajets, pleins et colis. Les calculs se font automatiquement.")

# ================= SIDEBAR : FILTRES =================
st.sidebar.header("🔍 Filtres")
plaques_dispo = get_toutes_plaques()
annees_dispo = get_toutes_annees()

plaque_filtre = st.sidebar.selectbox("Plaque", ["Toutes"] + plaques_dispo)
mois_filtre = st.sidebar.selectbox(
    "Mois",
    ["Tous", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
)
annee_filtre = st.sidebar.selectbox("Année", ["Toutes"] + annees_dispo)

# ================= ONGLETS =================
onglet1, onglet2, onglet3 = st.tabs([
    "📝 Nouveau trajet",
    "📊 Statistiques",
    "⚙️ Config véhicule"
])

# ---------- ONGLET 1 : Nouveau trajet ----------
with onglet1:
    st.subheader("📝 Enregistrer un trajet")
    st.markdown("Remplis les informations puis clique sur **Enregistrer**.")

    with st.form("form_trajet", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚛 Informations véhicule")
            plaque = st.text_input("Plaque d'immatriculation *", placeholder="AB-123-CD")
            chauffeur = st.text_input("Nom du chauffeur", placeholder="Ex: Jean")
            km_depart = st.number_input("Km au départ", min_value=0.0, value=0.0, step=1.0)
            km_arrivee = st.number_input("Km à l'arrivée", min_value=0.0, value=0.0, step=1.0)
            niveau_debut = st.number_input("Niveau carburant au départ (L)", min_value=0.0, value=0.0, step=1.0)

        with col2:
            st.markdown("### ⛽ Carburant")
            nb_pleins = st.number_input("Nombre de pleins effectués", min_value=0, value=0, step=1)
            litres_ajoutes = st.number_input("Litres ajoutés au total", min_value=0.0, value=0.0, step=1.0)
            prix_litre = st.number_input("Prix du litre (€)", min_value=0.0, value=1.70, step=0.01, format="%.2f")

            st.markdown("### 📦 Colis")
            colis_transp = st.number_input("Colis transportés", min_value=0, value=0, step=1)
            colis_client = st.number_input("Colis livrés au client", min_value=0, value=0, step=1)
            colis_relais = st.number_input("Colis livrés en relais", min_value=0, value=0, step=1)

        soumettre = st.form_submit_button("💾 Enregistrer le trajet", type="primary")

    if soumettre:
        try:
            if not plaque:
                st.error("❌ Renseigne la plaque d'immatriculation.")
            else:
                km = calculer_km(km_depart, km_arrivee)

                veh = get_vehicule(plaque)
                if not veh:
                    save_vehicule(plaque, 400, 30.0)
                    veh = get_vehicule(plaque)
                conso_moyenne = veh[2]

                carburant_restant = estimer_carburant_restant(
                    niveau_debut, litres_ajoutes, km, conso_moyenne
                )
                cout_gasoil = calculer_cout_gasoil(litres_ajoutes, prix_litre)

                data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "plaque": plaque,
                    "chauffeur": chauffeur,
                    "km_depart": km_depart,
                    "km_arrivee": km_arrivee,
                    "km_parcourus": km,
                    "nb_pleins": int(nb_pleins),
                    "litres_ajoutes": litres_ajoutes,
                    "prix_litre": prix_litre,
                    "colis_transportes": int(colis_transp),
                    "colis_livres_client": int(colis_client),
                    "colis_livres_relais": int(colis_relais),
                    "niveau_carburant_fin": round(carburant_restant, 2)
                }
                ajouter_trajet(data)

                st.success("✅ Trajet enregistré avec succès !")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📏 Km parcourus", f"{km:.1f} km")
                c2.metric("⛽ Carburant restant", f"{carburant_restant:.1f} L")
                c3.metric("💰 Coût gasoil", f"{cout_gasoil:.2f} €")
                c4.metric("📦 Colis livrés", f"{int(colis_client) + int(colis_relais)}/{int(colis_transp)}")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# ---------- ONGLET 2 : Statistiques ----------
with onglet2:
    st.subheader("📊 Statistiques & Historique")

    plaque_stats = plaque_filtre if plaque_filtre != "Toutes" else None
    mois_stats = mois_filtre if mois_filtre != "Tous" else None
    annee_stats = annee_filtre if annee_filtre != "Toutes" else None

    trajets = get_trajets(plaque_stats, mois_stats, annee_stats)

    if not trajets:
        st.info("Aucun trajet trouvé avec ces filtres.")
    else:
        moyennes = calculer_moyennes(trajets)
        carburant_restant = get_col(trajets[0], 13, 0)

        st.markdown("### 🎯 Résumé global")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⛽ Conso moyenne", f"{moyennes['conso']} L/100km")
        c2.metric("🛢️ Carburant restant", f"{carburant_restant:.1f} L")
        c3.metric("📅 Trajets", len(trajets))
        c4.metric("📏 Km total", f"{moyennes['total_km']:.0f} km")

        st.markdown("### 📦 Colis")
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("📦 Transp./jour", moyennes['colis_transp'])
        c6.metric("🏠 Livrés client/jour", moyennes['colis_client'])
        c7.metric("🏪 Livrés relais/jour", moyennes['colis_relais'])
        c8.metric("🎯 Taux livraison", f"{moyennes['taux_livraison']} %")

        st.markdown("### 💰 Coût du gasoil")
        c9, c10, c11 = st.columns(3)
        c9.metric("💶 Coût total", f"{moyennes['cout_total']:.2f} €")
        c10.metric("📆 Coût moyen/jour", f"{moyennes['cout_moyen_jour']:.2f} €")
        c11.metric("🛢️ Litres totaux", f"{moyennes['total_litres']:.1f} L")

        st.markdown("### 📋 Historique détaillé")
        df = pd.DataFrame(trajets, columns=[
            "ID", "Date", "Plaque", "Chauffeur", "Km départ", "Km arrivée",
            "Km parcourus", "Nb pleins", "Litres ajoutés", "Prix/L (€)",
            "Colis transp.", "Livrés client", "Livrés relais", "Carburant fin (L)"
        ])
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Télécharger l'historique en CSV",
            csv,
            f"trajets_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

# ---------- ONGLET 3 : Config véhicule ----------
with onglet3:
    st.subheader("⚙️ Configuration du véhicule")
    st.markdown("Configure la capacité du réservoir et la conso moyenne de référence.")

    plaque_cfg = st.text_input("Plaque", key="plaque_cfg")
    capacite_cfg = st.number_input("Capacité réservoir (L)", min_value=0.0, value=400.0, step=10.0)
    conso_cfg = st.number_input("Conso moyenne référence (L/100km)", min_value=0.0, value=30.0, step=1.0)

    if st.button("Enregistrer la configuration"):
        if not plaque_cfg:
            st.error("❌ Renseigne une plaque.")
        else:
            save_vehicule(plaque_cfg, capacite_cfg, conso_cfg)
            st.success(f"✅ Véhicule {plaque_cfg} configuré : réservoir {capacite_cfg}L, conso {conso_cfg} L/100km.")

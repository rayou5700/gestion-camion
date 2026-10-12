import streamlit as st
from datetime import datetime
import pandas as pd
from database import init_db, ajouter_trajet, get_trajets, get_vehicule, save_vehicule
from calculs import calculer_km, estimer_carburant_restant, calculer_moyennes

st.set_page_config(
    page_title="Gestion Camion",
    page_icon="🚛",
    layout="wide"
)

init_db()

st.title("🚛 Gestion Trajets & Carburant")
st.markdown("Enregistre tes trajets, pleins et colis. Le logiciel calcule automatiquement ta consommation.")

onglet1, onglet2, onglet3 = st.tabs(["📝 Nouveau trajet", "📊 Statistiques", "⚙️ Config véhicule"])

# ---------- ONGLET 1 : Nouveau trajet ----------
with onglet1:
    st.subheader("Enregistrer un trajet")

    col1, col2 = st.columns(2)
    with col1:
        plaque = st.text_input("Plaque d'immatriculation", placeholder="AB-123-CD")
        km_depart = st.number_input("Km au départ", min_value=0.0, value=0.0, step=1.0)
        nb_pleins = st.number_input("Nombre de pleins effectués", min_value=0, value=0, step=1)
        colis_transp = st.number_input("Colis transportés", min_value=0, value=0, step=1)
    with col2:
        niveau_debut = st.number_input("Niveau carburant au départ (L)", min_value=0.0, value=0.0, step=1.0)
        km_arrivee = st.number_input("Km à l'arrivée", min_value=0.0, value=0.0, step=1.0)
        litres_ajoutes = st.number_input("Litres ajoutés au total", min_value=0.0, value=0.0, step=1.0)
        colis_livres = st.number_input("Colis livrés", min_value=0, value=0, step=1)

    if st.button("💾 Enregistrer le trajet", type="primary"):
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

                data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "plaque": plaque,
                    "km_depart": km_depart,
                    "km_arrivee": km_arrivee,
                    "km_parcourus": km,
                    "nb_pleins": int(nb_pleins),
                    "litres_ajoutes": litres_ajoutes,
                    "colis_transportes": int(colis_transp),
                    "colis_livres": int(colis_livres),
                    "niveau_carburant_fin": round(carburant_restant, 2)
                }
                ajouter_trajet(data)

                st.success("✅ Trajet enregistré !")
                st.markdown(f"""
                - 🚛 **Plaque** : {plaque}
                - 📏 **Km parcourus** : {km:.1f} km
                - ⛽ **Carburant restant estimé** : {carburant_restant:.1f} L
                - 📦 **Colis livrés** : {int(colis_livres)}/{int(colis_transp)}
                """)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# ---------- ONGLET 2 : Statistiques ----------
with onglet2:
    st.subheader("📊 Statistiques")

    plaque_stats = st.text_input("Plaque à consulter", key="plaque_stats")

    if st.button("Afficher les statistiques"):
        if not plaque_stats:
            st.warning("Renseigne une plaque.")
        else:
            trajets = get_trajets(plaque_stats)
            if not trajets:
                st.info(f"Aucun trajet pour {plaque_stats}.")
            else:
                moyennes = calculer_moyennes(trajets)
                carburant_restant = trajets[0][10]

                col1, col2, col3 = st.columns(3)
                col1.metric("⛽ Conso moyenne", f"{moyennes['conso']} L/100km")
                col2.metric("🛢️ Carburant restant", f"{carburant_restant:.1f} L")
                col3.metric("📅 Trajets enregistrés", len(trajets))

                col4, col5, col6 = st.columns(3)
                col4.metric("📦 Colis transp./jour", moyennes['colis_transp'])
                col5.metric("✅ Colis livrés/jour", moyennes['colis_livres'])
                col6.metric("🎯 Taux livraison", f"{moyennes['taux_livraison']} %")

                st.subheader("Historique des trajets")
                df = pd.DataFrame(trajets, columns=[
                    "ID", "Date", "Plaque", "Km départ", "Km arrivée", "Km parcourus",
                    "Nb pleins", "Litres ajoutés", "Colis transp.", "Colis livrés", "Carburant fin (L)"
                ])
                st.dataframe(df, use_container_width=True)

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Télécharger en CSV",
                    csv,
                    f"trajets_{plaque_stats}.csv",
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

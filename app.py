import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import base64
from PIL import Image
from io import BytesIO
from database import (init_db, ajouter_trajet, get_trajets, get_vehicule,
                      save_vehicule, get_toutes_plaques, get_toutes_annees,
                      get_tous_chauffeurs, get_user, get_tous_users, creer_user,
                      supprimer_user, ajouter_conge, get_conges, supprimer_conge,
                      ajouter_planning, get_planning, supprimer_planning,
                      valider_trajet, get_trajet_by_id, get_photos_trajet,
                      get_groupes, get_users_par_groupe)
from calculs import (calculer_km, estimer_carburant_restant,
                     calculer_moyennes, calculer_cout_gasoil, get_col,
                     calculer_heures_travail)
from auth import login, logout, is_admin
from github_db import init_sync, upload_db

st.set_page_config(
    page_title="Gestion Camion",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============ CSS POUR MOBILE ============
st.markdown("""
<style>
.stButton > button {
    width: 100%;
    height: 55px;
    font-size: 18px;
    font-weight: bold;
    border-radius: 10px;
}
.stTextInput input, .stNumberInput input, .stDateInput input {
    height: 50px;
    font-size: 16px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    font-size: 14px;
    font-weight: 600;
    padding: 0 10px;
}
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
h1 { font-size: 1.8rem !important; }
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

# ============ SYNCHRO GITHUB ============
import os
sync_reussi = init_sync()

if not sync_reussi and not os.path.exists("donnees.db"):
    st.error("⚠️ Impossible de charger la base. Réessaie dans 30 secondes.")
    st.stop()

init_db()

# ============ CONNEXION OBLIGATOIRE ============
user = login()
if not user:
    st.stop()

username, role, nom_complet, groupe_user = user

# ============ FONCTIONS UTILITAIRES PHOTOS ============
def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        return ""

def base64_to_image(b64_string):
    if not b64_string:
        return None
    try:
        return base64.b64decode(b64_string)
    except:
        return None

# ============ HEADER ============
col_titre, col_user = st.columns([4, 1])
with col_titre:
    st.title("🚛 Gestion Trajets & Carburant")
with col_user:
    st.markdown(f"**👤 {nom_complet}**")
    role_badge = "👑 Admin" if role == "admin" else "🚚 Salarié"
    groupe_badge = f" | 🏢 {groupe_user}" if groupe_user else ""
    st.caption(f"Rôle : {role_badge}{groupe_badge}")
    logout()

st.markdown("---")

# ============ ALERTES GLOBALES ============
def afficher_alertes():
    alertes = []
    plaques = get_toutes_plaques()
    for p in plaques:
        trajets = get_trajets(plaque=p, limite=1)
        if trajets:
            carburant = get_col(trajets[0], 14, 0)
            if carburant < 50:
                alertes.append(f"⚠️ **{p}** : carburant bas (**{carburant:.1f} L**)")

    if alertes:
        with st.expander("🔔 Alertes", expanded=True):
            for a in alertes:
                st.warning(a)

afficher_alertes()

# ============ SIDEBAR FILTRES ============
st.sidebar.header("🔍 Filtres")
plaques_dispo = get_toutes_plaques()
annees_dispo = get_toutes_annees()
chauffeurs_dispo = get_tous_chauffeurs()
groupes_dispo = get_groupes()

plaque_filtre = st.sidebar.selectbox("Plaque", ["Toutes"] + plaques_dispo)
mois_filtre = st.sidebar.selectbox(
    "Mois", ["Tous", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
)
annee_filtre = st.sidebar.selectbox("Année", ["Toutes"] + annees_dispo)

if role == "admin":
    groupe_filtre = st.sidebar.selectbox("Groupe", ["Tous"] + groupes_dispo if groupes_dispo else ["Tous"])
    chauffeur_filtre = st.sidebar.selectbox(
        "Chauffeur", ["Tous"] + chauffeurs_dispo
    )
else:
    groupe_filtre = groupe_user
    chauffeur_filtre = nom_complet

# ============ CONSTRUCTION DES ONGLETS SELON RÔLE ============
if role == "admin":
    onglets = st.tabs([
        "📝 Nouveau trajet", "📊 Statistiques", "📈 Graphiques",
        "🔔 Alertes", "📅 Calendrier", "📆 Planning", "🏖️ Congés",
        "👥 Utilisateurs", "🏢 Groupes", "⚙️ Config véhicule"
    ])
    (tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10) = onglets
else:
    onglets = st.tabs([
        "📝 Ma journée", "📊 Mes stats", "📅 Mon calendrier", "🏖️ Mes congés"
    ])
    (tab1, tab2, tab5, tab7) = onglets
    tab3 = tab4 = tab6 = tab8 = tab9 = tab10 = None

# ================= ONGLET 1 : NOUVEAU TRAJET =================
with tab1:
    st.subheader("📝 Enregistrer un trajet")

    if "photo_depart" not in st.session_state:
        st.session_state.photo_depart = None
        st.session_state.photo_arrivee = None

    with st.form("form_trajet", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚛 Informations véhicule")
            plaque = st.text_input("Plaque d'immatriculation *", placeholder="AB-123-CD")
            chauffeur = st.text_input(
                "Nom du chauffeur",
                value=nom_complet if role == "salarie" else "",
                disabled=(role == "salarie")
            )
            heure_debut = st.text_input("Heure de début (HH:MM)", value="08:00")

            st.markdown("### 📸 Photo km DÉPART (obligatoire)")
            st.caption("Prends en photo ton compteur km")
            photo_depart = st.camera_input(
                "Photo du compteur km au départ",
                key="upload_depart"
            )
            if photo_depart:
                st.session_state.photo_depart = photo_depart
                st.success("✅ Photo départ prise")

            km_depart = st.number_input(
                "Km au départ (à recopier de la photo) *",
                min_value=0.0, value=0.0, step=1.0
            )
            niveau_debut = st.number_input(
                "Niveau carburant au départ (L)",
                min_value=0.0, value=0.0, step=1.0
            )

        with col2:
            st.markdown("### ⛽ Carburant")
            nb_pleins = st.number_input("Nombre de pleins", min_value=0, value=0, step=1)
            litres_ajoutes = st.number_input("Litres ajoutés", min_value=0.0, value=0.0, step=1.0)
            prix_litre = st.number_input("Prix du litre (€)", min_value=0.0, value=1.70, step=0.01, format="%.2f")

            st.markdown("### 📦 Colis")
            colis_transp = st.number_input("Colis transportés", min_value=0, value=0, step=1)
            colis_client = st.number_input("Livrés client", min_value=0, value=0, step=1)
            colis_relais = st.number_input("Livrés relais", min_value=0, value=0, step=1)
            colis_non_livres = st.number_input("Non livrés", min_value=0, value=0, step=1)

            st.markdown("### 🕐 Fin de journée")
            heure_fin = st.text_input("Heure de fin (HH:MM)", value="18:00")

            st.markdown("### 📸 Photo km ARRIVÉE (obligatoire)")
            st.caption("Prends en photo ton compteur km à l'arrivée")
            photo_arrivee = st.camera_input(
                "Photo du compteur km à l'arrivée",
                key="upload_arrivee"
            )
            if photo_arrivee:
                st.session_state.photo_arrivee = photo_arrivee
                st.success("✅ Photo arrivée prise")

            km_arrivee = st.number_input(
                "Km à l'arrivée (à recopier de la photo) *",
                min_value=0.0, value=0.0, step=1.0
            )

        soumettre = st.form_submit_button("💾 Enregistrer et valider la journée", type="primary")

    if soumettre:
        try:
            erreurs = []
            if not plaque:
                erreurs.append("Plaque manquante")
            if not st.session_state.photo_depart:
                erreurs.append("Photo km DÉPART obligatoire")
            if not st.session_state.photo_arrivee:
                erreurs.append("Photo km ARRIVÉE obligatoire")
            if km_depart == 0 or km_arrivee == 0:
                erreurs.append("Km départ et arrivée obligatoires")
            if km_arrivee <= km_depart:
                erreurs.append("Km arrivée doit être > km départ")

            if erreurs:
                st.error("❌ Impossible de valider :")
                for e in erreurs:
                    st.write(f"- {e}")
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
                heures = calculer_heures_travail(heure_debut, heure_fin)

                photo_depart_b64 = image_to_base64(st.session_state.photo_depart)
                photo_arrivee_b64 = image_to_base64(st.session_state.photo_arrivee)

                data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "plaque": plaque, "chauffeur": chauffeur,
                    "km_depart": km_depart, "km_arrivee": km_arrivee,
                    "km_parcourus": km, "nb_pleins": int(nb_pleins),
                    "litres_ajoutes": litres_ajoutes, "prix_litre": prix_litre,
                    "colis_transportes": int(colis_transp),
                    "colis_livres_client": int(colis_client),
                    "colis_livres_relais": int(colis_relais),
                    "colis_non_livres": int(colis_non_livres),
                    "niveau_carburant_fin": round(carburant_restant, 2),
                    "photo_depart": photo_depart_b64,
                    "photo_arrivee": photo_arrivee_b64,
                    "heure_debut": heure_debut, "heure_fin": heure_fin,
                    "valide": 1
                }
                ajouter_trajet(data)
                upload_db(f"Nouveau trajet {plaque}")

                st.session_state.photo_depart = None
                st.session_state.photo_arrivee = None

                st.success("✅ Journée validée !")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📏 Km", f"{km:.1f} km")
                c2.metric("⛽ Carburant", f"{carburant_restant:.1f} L")
                c3.metric("💰 Coût", f"{cout_gasoil:.2f} €")
                c4.metric("🕐 Heures", f"{heures:.1f} h")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# ================= ONGLET 2 : STATISTIQUES =================
if tab2:
    with tab2:
        st.subheader("📊 Statistiques")

        plaque_stats = plaque_filtre if plaque_filtre != "Toutes" else None
        mois_stats = mois_filtre if mois_filtre != "Tous" else None
        annee_stats = annee_filtre if annee_filtre != "Toutes" else None

        trajets = get_trajets(plaque_stats, mois_stats, annee_stats)

        # Filtrage par rôle / groupe
        if role == "salarie":
            trajets = [t for t in trajets if get_col(t, 3) == nom_complet]
        elif role == "admin" and groupe_filtre != "Tous" and groupe_filtre:
            # Filtrer par groupe
            users_groupe = get_users_par_groupe(groupe_filtre)
            noms_groupe = [u[3] for u in users_groupe]
            trajets = [t for t in trajets if get_col(t, 3) in noms_groupe]

        trajets = [t for t in trajets if len(t) >= 20]

        if not trajets:
            st.info("Aucun trajet trouvé.")
        else:
            m = calculer_moyennes(trajets)
            carburant_restant = get_col(trajets[0], 14, 0)

            st.markdown("### 🎯 Résumé")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("⛽ Conso moyenne", f"{m['conso']} L/100km")
            c2.metric("🛢️ Carburant restant", f"{carburant_restant:.1f} L")
            c3.metric("📅 Trajets", len(trajets))
            c4.metric("📏 Km total", f"{m['total_km']:.0f} km")

            st.markdown("### 📦 Colis")
            c5, c6, c7, c8, c9 = st.columns(5)
            c5.metric("📦 Transp./jour", m['colis_transp'])
            c6.metric("🏠 Client/jour", m['colis_client'])
            c7.metric("🏪 Relais/jour", m['colis_relais'])
            c8.metric("❌ Non livrés/jour", m['colis_non_livres'])
            c9.metric("🎯 Taux", f"{m['taux_livraison']} %")

            st.markdown("### 💰 Coût & Heures")
            c10, c11, c12, c13 = st.columns(4)
            c10.metric("💶 Coût total", f"{m['cout_total']:.2f} €")
            c11.metric("📆 Moyen/jour", f"{m['cout_moyen_jour']:.2f} €")
            c12.metric("🛢️ Litres totaux", f"{m['total_litres']:.1f} L")
            c13.metric("🕐 Heures totales", f"{m['total_heures']:.1f} h")

            if role == "admin":
                st.markdown("### 📸 Photos des trajets récents")
                st.caption("Clique sur un trajet pour voir les photos km départ/arrivée")

                for t in trajets[:10]:
                    trajet_id = get_col(t, 0)
                    date_t = get_col(t, 1)
                    plaque_t = get_col(t, 2)
                    chauffeur_t = get_col(t, 3)

                    with st.expander(f"📸 {date_t} - {plaque_t} - {chauffeur_t}"):
                        photos = get_photos_trajet(trajet_id)
                        col_p1, col_p2 = st.columns(2)

                        with col_p1:
                            st.markdown("**📷 Km DÉPART**")
                            if photos[0]:
                                img_bytes = base64_to_image(photos[0])
                                if img_bytes:
                                    st.image(img_bytes, use_container_width=True)
                                else:
                                    st.info("Photo indisponible")
                            else:
                                st.info("Aucune photo")

                        with col_p2:
                            st.markdown("**📷 Km ARRIVÉE**")
                            if photos[1]:
                                img_bytes = base64_to_image(photos[1])
                                if img_bytes:
                                    st.image(img_bytes, use_container_width=True)
                                else:
                                    st.info("Photo indisponible")
                            else:
                                st.info("Aucune photo")

            st.markdown("### 📋 Historique")
            df = pd.DataFrame(trajets, columns=[
                "ID", "Date", "Plaque", "Chauffeur", "Km départ", "Km arrivée",
                "Km parcourus", "Nb pleins", "Litres", "Prix/L",
                "Colis transp.", "Client", "Relais", "Non livrés",
                "Carburant (L)", "Photo départ", "Photo arrivée",
                "H début", "H fin", "Validé"
            ])
            df_display = df.drop(columns=["Photo départ", "Photo arrivée"])
            st.dataframe(df_display, use_container_width=True)

            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger CSV", csv,
                             f"trajets_{datetime.now().strftime('%Y%m%d')}.csv",
                             "text/csv")

# ================= ONGLET 3 : GRAPHIQUES =================
if tab3:
    with tab3:
        st.subheader("📈 Graphiques")

        plaque_stats = plaque_filtre if plaque_filtre != "Toutes" else None
        trajets = get_trajets(plaque_stats, limite=200)
        trajets = [t for t in trajets if len(t) >= 20]

        if not trajets:
            st.info("Aucune donnée pour les graphiques.")
        else:
            df = pd.DataFrame(trajets, columns=[
                "ID", "Date", "Plaque", "Chauffeur", "Km départ", "Km arrivée",
                "Km parcourus", "Nb pleins", "Litres", "Prix/L",
                "Colis transp.", "Client", "Relais", "Non livrés",
                "Carburant", "Photo départ", "Photo arrivée",
                "H début", "H fin", "Validé"
            ])
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date")

            df["Conso"] = (df["Litres"] / df["Km parcourus"] * 100).round(2)
            df_conso = df[df["Conso"] > 0]

            if not df_conso.empty:
                st.markdown("### ⛽ Courbe de consommation (L/100km)")
                fig = px.line(df_conso, x="Date", y="Conso",
                             markers=True, title="Évolution de la consommation")
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📦 Répartition des colis")
            total_client = df["Client"].sum()
            total_relais = df["Relais"].sum()
            total_non_livres = df["Non livrés"].sum()

            fig2 = px.pie(
                values=[total_client, total_relais, total_non_livres],
                names=["Livrés client", "Livrés relais", "Non livrés"],
                title="Répartition des colis",
                color_discrete_sequence=["#4CAF50", "#2196F3", "#F44336"]
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### 📏 Km parcourus par jour")
            fig3 = px.bar(df, x="Date", y="Km parcourus", title="Km par jour")
            st.plotly_chart(fig3, use_container_width=True)

            df["Cout"] = df["Litres"] * df["Prix/L"]
            fig4 = px.bar(df[df["Cout"] > 0], x="Date", y="Cout",
                         title="Coût gasoil par jour (€)")
            st.plotly_chart(fig4, use_container_width=True)

# ================= ONGLET 4 : ALERTES =================
if tab4:
    with tab4:
        st.subheader("🔔 Alertes & Surveillance")

        st.markdown("### ⛽ Carburant bas (< 50 L)")
        plaques = get_toutes_plaques()
        if not plaques:
            st.info("Aucun véhicule enregistré.")
        else:
            for p in plaques:
                trajets = get_trajets(plaque=p, limite=1)
                if trajets:
                    carburant = get_col(trajets[0], 14, 0)
                    if carburant < 50:
                        st.error(f"🚨 **{p}** : seulement **{carburant:.1f} L** restants !")
                    elif carburant < 100:
                        st.warning(f"⚠️ **{p}** : **{carburant:.1f} L** restants")
                    else:
                        st.success(f"✅ **{p}** : {carburant:.1f} L")

        st.markdown("### 📦 Colis non livrés")
        trajets_recents = get_trajets(limite=20)
        trajets_recents = [t for t in trajets_recents if len(t) >= 20]
        for t in trajets_recents:
            non_livres = get_col(t, 13, 0)
            if non_livres > 0:
                date = get_col(t, 1)
                plaque = get_col(t, 2)
                st.warning(f"📦 **{date}** - {plaque} : **{non_livres}** colis non livrés")

        st.markdown("### 📊 Consommation anormale")
        trajets_all = get_trajets(limite=100)
        trajets_all = [t for t in trajets_all if len(t) >= 20]
        if len(trajets_all) > 5:
            m = calculer_moyennes(trajets_all)
            conso_moy = m['conso']
            for t in trajets_all[:10]:
                km = get_col(t, 6, 0)
                litres = get_col(t, 8, 0)
                if km > 0 and litres > 0:
                    conso = (litres / km) * 100
                    if conso > conso_moy * 1.3:
                        st.error(f"🚨 **{get_col(t, 1)}** : conso anormale **{conso:.1f} L/100km** (moyenne {conso_moy})")

# ================= ONGLET 5 : CALENDRIER =================
if tab5:
    with tab5:
        st.subheader("📅 Calendrier des trajets")

        trajets = get_trajets(limite=200)
        trajets = [t for t in trajets if len(t) >= 20]
        if role == "salarie":
            trajets = [t for t in trajets if get_col(t, 3) == nom_complet]

        if not trajets:
            st.info("Aucun trajet.")
        else:
            df = pd.DataFrame(trajets, columns=[
                "ID", "Date", "Plaque", "Chauffeur", "Km départ", "Km arrivée",
                "Km parcourus", "Nb pleins", "Litres", "Prix/L",
                "Colis transp.", "Client", "Relais", "Non livrés",
                "Carburant", "Photo départ", "Photo arrivée",
                "H début", "H fin", "Validé"
            ])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Jour"] = df["Date"].dt.date

            resume = df.groupby("Jour").agg({
                "Km parcourus": "sum",
                "Client": "sum",
                "Relais": "sum",
                "Non livrés": "sum"
            }).reset_index()
            resume.columns = ["Jour", "Km", "Livrés client", "Livrés relais", "Non livrés"]

            st.dataframe(resume, use_container_width=True)

            fig = px.bar(resume, x="Jour", y="Km", title="Km par jour")
            st.plotly_chart(fig, use_container_width=True)

# ================= ONGLET 6 : PLANNING =================
if tab6:
    with tab6:
        st.subheader("📆 Planning hebdomadaire")

        with st.form("form_planning"):
            col1, col2, col3 = st.columns(3)
            with col1:
                date_plan = st.date_input("Date")
            with col2:
                chauffeur_plan = st.selectbox("Chauffeur",
                    get_tous_chauffeurs() if get_tous_chauffeurs() else ["Jean Dupont"])
            with col3:
                plaque_plan = st.selectbox("Camion",
                    get_toutes_plaques() if get_toutes_plaques() else ["AB-123-CD"])
            description = st.text_input("Description de la tournée")
            submit = st.form_submit_button("➕ Ajouter au planning")

        if submit:
            ajouter_planning(str(date_plan), chauffeur_plan, plaque_plan, description)
            upload_db("Nouveau planning")
            st.success("✅ Ajouté au planning")
            st.rerun()

        st.markdown("### 📋 Planning des 7 prochains jours")
        aujourd_hui = datetime.now().date()
        planning = get_planning(str(aujourd_hui))

        if not planning:
            st.info("Rien de prévu cette semaine.")
        else:
            for p in planning:
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**{p[1]}** - 👤 {p[2]} - 🚛 {p[3]}")
                        st.caption(f"📝 {p[4]}")
                    with col2:
                        if st.button("🗑️", key=f"del_plan_{p[0]}"):
                            supprimer_planning(p[0])
                            upload_db("Suppression planning")
                            st.rerun()

# ================= ONGLET 7 : CONGÉS =================
if tab7:
    with tab7:
        st.subheader("🏖️ Gestion des congés")

        if role == "admin":
            with st.form("form_conge"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    chauffeur_conge = st.selectbox("Chauffeur",
                        get_tous_chauffeurs() if get_tous_chauffeurs() else ["Jean Dupont"])
                with col2:
                    debut = st.date_input("Date de début")
                with col3:
                    fin = st.date_input("Date de fin")
                motif = st.text_input("Motif (optionnel)")
                submit = st.form_submit_button("➕ Ajouter congé")

            if submit:
                ajouter_conge(chauffeur_conge, str(debut), str(fin), motif)
                upload_db("Nouveau congé")
                st.success("✅ Congé ajouté")
                st.rerun()

            conges = get_conges()
        else:
            conges = get_conges(nom_complet)

        st.markdown("### 📋 Liste des congés")
        if not conges:
            st.info("Aucun congé enregistré.")
        else:
            for c in conges:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{c[1]}** : du **{c[2]}** au **{c[3]}**")
                    if c[4]:
                        st.caption(f"Motif : {c[4]}")
                with col2:
                    if role == "admin" and st.button("🗑️", key=f"del_conge_{c[0]}"):
                        supprimer_conge(c[0])
                        upload_db("Suppression congé")
                        st.rerun()

# ================= ONGLET 8 : UTILISATEURS (admin only) =================
if tab8:
    with tab8:
        st.subheader("👥 Gestion des utilisateurs")

        groupes_existants = get_groupes()
        groupes_options = ["(Aucun)"] + groupes_existants + ["+ Nouveau groupe..."]

        with st.form("form_user"):
            col1, col2 = st.columns(2)
            with col1:
                new_user = st.text_input("Nom d'utilisateur")
                new_nom = st.text_input("Nom complet")
            with col2:
                new_pass = st.text_input("Mot de passe", type="password")
                new_role = st.selectbox("Rôle", ["salarie", "admin"])

            groupe_choisi = st.selectbox("Groupe / Société", groupes_options)

            nouveau_groupe = ""
            if groupe_choisi == "+ Nouveau groupe...":
                nouveau_groupe = st.text_input("Nom du nouveau groupe (ex: DPD, GLS...)")

            submit = st.form_submit_button("➕ Créer / Modifier")

        if submit:
            if new_user and new_pass and new_nom:
                if groupe_choisi == "+ Nouveau groupe...":
                    groupe_final = nouveau_groupe.strip()
                elif groupe_choisi == "(Aucun)":
                    groupe_final = ""
                else:
                    groupe_final = groupe_choisi

                creer_user(new_user, new_pass, new_role, new_nom, groupe_final)
                upload_db(f"Création utilisateur {new_user}")
                st.success(f"✅ Utilisateur {new_user} enregistré (Groupe : {groupe_final or 'Aucun'})")
                st.rerun()
            else:
                st.error("Tous les champs sont obligatoires")

               st.markdown("### 👥 Utilisateurs existants")

        groupes_filtre = get_groupes()
        filtre_groupe = st.selectbox(
            "Filtrer par groupe",
            ["Tous"] + groupes_filtre + ["(Sans groupe)"]
        )

        users = get_tous_users()
        if filtre_groupe == "(Sans groupe)":
            users = [u for u in users if (len(u) <= 4 or not u[4])]
        elif filtre_groupe != "Tous":
            users = [u for u in users if len(u) > 4 and u[4] == filtre_groupe]

        # Initialiser le mode édition
        if "edit_user" not in st.session_state:
            st.session_state.edit_user = None

        for u in users:
            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                role_badge = "👑 Admin" if u[2] == "admin" else "🚚 Salarié"
                groupe_badge = f" - 🏢 **{u[4]}**" if len(u) > 4 and u[4] else " - 🏢 *(aucun)*"
                st.markdown(f"**{u[3]}** (`{u[0]}`) - {role_badge}{groupe_badge}")
            with col2:
                if u[0] != "serhane":
                    if st.button("✏️", key=f"edit_btn_{u[0]}", help="Modifier cet utilisateur"):
                        st.session_state.edit_user = u[0]
                        st.rerun()
            with col3:
                if u[0] != "serhane" and st.button("🗑️", key=f"del_user_{u[0]}", help="Supprimer"):
                    supprimer_user(u[0])
                    upload_db("Suppression utilisateur")
                    st.rerun()

        # ===== FORMULAIRE DE MODIFICATION =====
        if st.session_state.edit_user:
            user_to_edit = get_user(st.session_state.edit_user)
            
            if user_to_edit:
                st.markdown("---")
                st.markdown(f"### ✏️ Modifier l'utilisateur **{user_to_edit[3]}**")
                
                groupes_existants = get_groupes()
                groupes_options = ["(Aucun)"] + groupes_existants + ["+ Nouveau groupe..."]
                
                # Pré-sélectionner le groupe actuel
                groupe_actuel = user_to_edit[4] if len(user_to_edit) > 4 and user_to_edit[4] else "(Aucun)"
                if groupe_actuel not in groupes_options:
                    groupe_actuel = "(Aucun)"
                index_groupe = groupes_options.index(groupe_actuel)
                
                with st.form("form_edit_user"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_user = st.text_input("Nom d'utilisateur", value=user_to_edit[0], disabled=True)
                        edit_nom = st.text_input("Nom complet", value=user_to_edit[3])
                    with col2:
                        edit_pass = st.text_input("Nouveau mot de passe (laisser vide = inchangé)", type="password")
                        edit_role = st.selectbox("Rôle", ["salarie", "admin"], 
                                                  index=0 if user_to_edit[2] == "salarie" else 1)
                    
                    edit_groupe = st.selectbox("Groupe / Société", groupes_options, index=index_groupe)
                    
                    edit_nouveau_groupe = ""
                    if edit_groupe == "+ Nouveau groupe...":
                        edit_nouveau_groupe = st.text_input("Nom du nouveau groupe")
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_edit = st.form_submit_button("💾 Enregistrer les modifications", type="primary")
                    with col_cancel:
                        cancel_edit = st.form_submit_button("❌ Annuler")
                
                if save_edit:
                    # Déterminer le groupe final
                    if edit_groupe == "+ Nouveau groupe...":
                        groupe_final = edit_nouveau_groupe.strip()
                    elif edit_groupe == "(Aucun)":
                        groupe_final = ""
                    else:
                        groupe_final = edit_groupe
                    
                    # Mot de passe : garder l'ancien si vide
                    password_final = edit_pass if edit_pass else user_to_edit[1]
                    
                    creer_user(edit_user, password_final, edit_role, edit_nom, groupe_final)
                    upload_db(f"Modification utilisateur {edit_user}")
                    st.success(f"✅ Utilisateur **{edit_nom}** modifié ! (Groupe : {groupe_final or 'Aucun'})")
                    st.session_state.edit_user = None
                    st.rerun()
                
                if cancel_edit:
                    st.session_state.edit_user = None
                    st.rerun()

# ================= ONGLET 9 : GROUPES =================
if tab9:
    with tab9:
        st.subheader("🏢 Gestion des groupes / sociétés")
        st.caption("Organise tes salariés par société (DPD, GLS, etc.)")

        groupes = get_groupes()

        if not groupes:
            st.info("Aucun groupe créé. Va dans 👥 Utilisateurs pour assigner des groupes.")
        else:
            st.markdown(f"### 📊 Vue d'ensemble - {len(groupes)} groupe(s)")

            for g in groupes:
                users_g = get_users_par_groupe(g)
                nb_users = len(users_g)

                with st.expander(f"🏢 **{g}** - {nb_users} salarié(s)", expanded=False):
                    if not users_g:
                        st.info("Aucun utilisateur dans ce groupe.")
                    else:
                        for u in users_g:
                            role_badge = "👑 Admin" if u[2] == "admin" else "🚚 Salarié"
                            st.markdown(f"- **{u[3]}** (`{u[0]}`) - {role_badge}")

                        st.markdown("---")
                        st.markdown(f"**📊 Statistiques du groupe {g}**")

                        noms_chauffeurs = [u[3] for u in users_g]
                        trajets_groupe = []
                        for t in get_trajets(limite=500):
                            if len(t) >= 20 and get_col(t, 3) in noms_chauffeurs:
                                trajets_groupe.append(t)

                        if trajets_groupe:
                            m = calculer_moyennes(trajets_groupe)
                            c1, c2, c3 = st.columns(3)
                            c1.metric("📅 Trajets", len(trajets_groupe))
                            c2.metric("📏 Km total", f"{m['total_km']:.0f} km")
                            c3.metric("💰 Coût total", f"{m['cout_total']:.2f} €")

                            c4, c5, c6 = st.columns(3)
                            c4.metric("📦 Colis livrés/jour", m['colis_client'] + m['colis_relais'])
                            c5.metric("⛽ Conso moyenne", f"{m['conso']} L/100km")
                            c6.metric("🕐 Heures totales", f"{m['total_heures']:.1f} h")
                        else:
                            st.info("Aucun trajet enregistré pour ce groupe.")

# ================= ONGLET 10 : CONFIG =================
if tab10:
    with tab10:
        st.subheader("⚙️ Configuration véhicule")
        plaque_cfg = st.text_input("Plaque", key="plaque_cfg")
        capacite_cfg = st.number_input("Capacité réservoir (L)", min_value=0.0, value=400.0, step=10.0)
        conso_cfg = st.number_input("Conso référence (L/100km)", min_value=0.0, value=30.0, step=1.0)
        if st.button("Enregistrer la configuration"):
            if plaque_cfg:
                save_vehicule(plaque_cfg, capacite_cfg, conso_cfg)
                upload_db(f"Config véhicule {plaque_cfg}")
                st.success(f"✅ {plaque_cfg} configuré")
            else:
                st.error("Renseigne une plaque")

        st.markdown("---")
        st.markdown("### 💾 Sauvegarde manuelle")
        st.caption("Force la sauvegarde de la base sur GitHub")
        if st.button("🔄 Sauvegarder maintenant sur GitHub"):
            if upload_db("Sauvegarde manuelle"):
                st.success("✅ Base sauvegardée sur GitHub !")
            else:
                st.error("❌ Échec de la sauvegarde. Vérifie le token.")

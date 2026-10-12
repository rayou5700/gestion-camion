import streamlit as st
from database import get_user

def login():
    """Affiche l'écran de connexion. Retourne (username, role, nom)."""
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        return st.session_state.user

    st.markdown("""
        <div style='text-align:center; padding: 40px;'>
            <h1>🚛 Gestion Camion</h1>
            <p>Connecte-toi pour accéder</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("🔐 Se connecter", use_container_width=True)

        if submit:
            user = get_user(username)
            if user and user[1] == password:
                st.session_state.user = (user[0], user[2], user[3])
                st.rerun()
            else:
                st.error("❌ Identifiants incorrects")

        st.markdown("---")
        st.caption("💡 Contacte ton administrateur pour obtenir un compte")

    return None

def logout():
    """Déconnexion."""
    if st.button("🚪 Se déconnecter"):
        st.session_state.user = None
        st.rerun()

def is_admin():
    """Vérifie si l'utilisateur connecté est admin."""
    if "user" not in st.session_state or not st.session_state.user:
        return False
    return st.session_state.user[1] == "admin"

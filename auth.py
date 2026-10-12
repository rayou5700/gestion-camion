import streamlit as st
import extra_streamlit_components as stx
from database import get_user

# Gestionnaire de cookies
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

def login():
    """Affiche l'écran de connexion. Retourne (username, role, nom)."""
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        return st.session_state.user

    cookie_manager = get_cookie_manager()

    # Récupérer les identifiants sauvegardés dans les cookies
    saved_user = cookie_manager.get("camion_user") or ""
    saved_pass = cookie_manager.get("camion_pass") or ""
    remember_checked = bool(saved_user)

    st.markdown("""
        <div style='text-align:center; padding: 40px;'>
            <h1>🚛 Gestion Camion</h1>
            <p>Connecte-toi pour accéder</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", value=saved_user)
            password = st.text_input("Mot de passe", value=saved_pass, type="password")
            remember = st.checkbox("💾 Se souvenir de moi", value=remember_checked)
            submit = st.form_submit_button("🔐 Se connecter", use_container_width=True)

        if submit:
            user = get_user(username)
            if user and user[1] == password:
                # Sauvegarder dans les cookies si demandé
                if remember:
                    cookie_manager.set("camion_user", username, expires_at=None)
                    cookie_manager.set("camion_pass", password, expires_at=None)
                else:
                    # Effacer les cookies
                    try:
                        cookie_manager.delete("camion_user")
                        cookie_manager.delete("camion_pass")
                    except:
                        pass

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

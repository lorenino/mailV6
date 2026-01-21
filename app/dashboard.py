import streamlit as st
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from db_utils import get_all_clients_df

# Page Configuration
st.set_page_config(
    page_title="Suivi Campagne Email",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a "Pro" look
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    """Loads data from the database."""
    try:
        df = get_all_clients_df()
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement de la base de données: {e}")
        return pd.DataFrame()

import subprocess
import os
import json
import sys

# ... (imports remain the same)

# ... (page config and css remain the same)

# Path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
STATUS_FILE = os.path.join(DATA_DIR, 'status.json')
STOP_FLAG_FILE = os.path.join(DATA_DIR, 'stop.flag')

def get_mailer_status():
    """Reads the status.json file."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def main():
    # Auto-refresh every 3 seconds when campaign is running (non-blocking)
    st_autorefresh(interval=3000, limit=None, key="data_refresh")
    
    st.title("🚀 Dashboard de Suivi - Campagne Email")
    
    # --- Initialize Session State for transitions ---
    if 'launching' not in st.session_state:
        st.session_state.launching = False
    if 'stopping' not in st.session_state:
        st.session_state.stopping = False
    if 'launch_time' not in st.session_state:
        st.session_state.launch_time = 0
    if 'stop_time' not in st.session_state:
        st.session_state.stop_time = 0
    
    # --- Control Panel ---
    st.sidebar.header("🎛️ Panneau de Contrôle")
    
    status_data = get_mailer_status()
    is_running = status_data.get('running', False) if status_data else False
    
    # Auto-clear transition states after timeout (10 seconds) or when state changes
    current_time = time.time()
    if st.session_state.launching and (is_running or current_time - st.session_state.launch_time > 10):
        st.session_state.launching = False
    if st.session_state.stopping and (not is_running or current_time - st.session_state.stop_time > 10):
        st.session_state.stopping = False
    
    # Check if in a transitional state
    is_transitioning = st.session_state.launching or st.session_state.stopping
    
    if is_transitioning:
        # Show transitional state with disabled buttons
        if st.session_state.launching:
            st.sidebar.warning("⏳ **Démarrage en cours...**")
            st.sidebar.info("Le processus d'envoi est en train de s'initialiser. Veuillez patienter.")
            with st.sidebar:
                st.spinner("Initialisation du mailer...")
        else:  # stopping
            st.sidebar.warning("⏳ **Arrêt en cours...**")
            st.sidebar.info("Le signal d'arrêt a été envoyé. Le processus s'arrêtera après l'email en cours.")
        
        # Disabled button placeholder
        st.sidebar.button("⏳ Veuillez patienter...", disabled=True, type="secondary")
        
    elif is_running:
        mode = status_data.get('mode', '') if status_data else ''
        mode_emoji = "🧪" if mode == "TEST" else "📤"
        st.sidebar.success(f"{mode_emoji} **Campagne en cours ({mode})**")
        st.sidebar.markdown("---")
        
        # Show detailed stats
        if status_data:
            # Stats row
            col1, col2, col3 = st.sidebar.columns(3)
            with col1:
                st.metric("✅ Envoyés", status_data.get('sent', 0))
            with col2:
                st.metric("⏳ Restants", status_data.get('remaining', 0))
            with col3:
                failed = status_data.get('failed', 0)
                st.metric("❌ Échecs", failed, delta_color="inverse" if failed > 0 else "off")
            
            # Current activity
            msg = status_data.get('message', '')
            st.sidebar.markdown(f"**📨 {msg}**")
            
            if 'progress' in status_data:
                st.sidebar.progress(status_data['progress'] / 100)
                st.sidebar.caption(f"Progression: {status_data['progress']}%")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🛑 STOPPER LA CAMPAGNE", type="primary", use_container_width=True):
            with open(STOP_FLAG_FILE, 'w') as f:
                f.write('STOP')
            st.session_state.stopping = True
            st.session_state.stop_time = time.time()
            st.rerun()
    else:
        st.sidebar.info("🔴 **Campagne à l'arrêt**")
        st.sidebar.markdown("---")
        
        # Test Mode Toggle
        is_dry_run = st.sidebar.checkbox(
            "🧪 Mode Test (Dry Run)", 
            value=True, 
            help="Si coché, aucun email ne sera réellement envoyé. Utile pour tester le processus."
        )
        
        # Show mode explanation
        if is_dry_run:
            st.sidebar.caption("✅ Mode sécurisé: les emails seront simulés")
        else:
            st.sidebar.warning("⚠️ Mode réel: les emails seront vraiment envoyés!")
        
        st.sidebar.markdown("---")

        # Quick Test Button
        if st.sidebar.button("📧 Envoyer Test (lfaloci)", help="Envoie un email de test unique à lfaloci@datacorp-lyon.fr"):
            with st.sidebar:
                with st.spinner("Envoi du test..."):
                    test_script = os.path.join(SCRIPT_DIR, "send_test.py")
                    # Run synchronously to show result
                    result = subprocess.run(
                        [sys.executable, test_script], 
                        capture_output=True, 
                        text=True, 
                        cwd=SCRIPT_DIR
                    )
                    
                    if result.returncode == 0 and "✅ Test email sent successfully!" in result.stdout:
                        st.success("Test envoyé avec succès !")
                    else:
                        st.error("Échec de l'envoi")
                        # Show last few lines of output for debugging
                        output = result.stdout + "\n" + result.stderr
                        st.caption("Logs:")
                        st.code(output[-500:])

        st.sidebar.markdown("---")
        
        if st.sidebar.button("▶️ LANCER LA CAMPAGNE", type="primary", use_container_width=True):
            # Set transitional state BEFORE launching
            st.session_state.launching = True
            st.session_state.launch_time = time.time()
            
            # Launch mailer.py in a separate process
            mailer_path = os.path.join(SCRIPT_DIR, "mailer.py")
            cmd = [sys.executable, mailer_path]
            if not is_dry_run:
                cmd.append("--real")
            
            kwargs = {'cwd': SCRIPT_DIR}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(cmd, **kwargs)
            st.rerun()

    # Show last update timestamp at bottom of sidebar
    if status_data and not is_transitioning:
        st.sidebar.markdown("---")
        st.sidebar.caption(f"🕐 Dernière MAJ: {time.strftime('%H:%M:%S', time.localtime(status_data.get('timestamp', 0)))}")

    st.markdown("---")

    # Load Data
    df = load_data()

    if not df.empty:
        # Calculate Metrics
        total_clients = len(df)
        
        # Normalize status for comparison (handle potential casing issues)
        if 'Envoyé ?' in df.columns:
            sent_clients = len(df[df['Envoyé ?'].str.upper() == 'OUI'])
        else:
            sent_clients = 0
            st.warning("Colonne 'Envoyé ?' introuvable.")

        remaining_clients = total_clients - sent_clients
        progress = sent_clients / total_clients if total_clients > 0 else 0

        # KPI Columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Total Clients", value=total_clients)
        
        with col2:
            st.metric(label="Emails Envoyés", value=sent_clients, delta=f"{progress*100:.1f}%")
        
        with col3:
            st.metric(label="Restants", value=remaining_clients, delta_color="inverse")
            
        with col4:
            status_text = "✅ Terminé" if remaining_clients == 0 else "⏳ En cours"
            st.metric(label="Statut", value=status_text)

        # Progress Bar
        st.markdown("### Progression Globale")
        st.progress(progress)
        
        # Data Table Section
        st.markdown("---")
        st.subheader("📋 Détails des Clients")
        
        # Filters
        filter_status = st.selectbox(
            "Filtrer par statut d'envoi",
            ["Tous", "Envoyés (OUI)", "Non Envoyés (NON/Autre)"]
        )

        df_display = df.copy()
        if filter_status == "Envoyés (OUI)":
            df_display = df_display[df_display['Envoyé ?'].str.upper() == 'OUI']
        elif filter_status == "Non Envoyés (NON/Autre)":
            df_display = df_display[df_display['Envoyé ?'].str.upper() != 'OUI']

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Email 1": st.column_config.TextColumn("Email")
            }
        )
        
        # Manual refresh button (auto-refresh is already handled by st_autorefresh)
        if st.button('🔄 Actualiser les données'):
            st.rerun()

    else:
        st.info("Aucune donnée trouvée dans la base de données.")

if __name__ == "__main__":
    main()

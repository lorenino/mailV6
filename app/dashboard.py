import streamlit as st
import pandas as pd
import time
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
    st.title("🚀 Dashboard de Suivi - Campagne Email")
    
    # --- Control Panel ---
    st.sidebar.header("🎛️ Panneau de Contrôle")
    
    status_data = get_mailer_status()
    is_running = status_data.get('running', False) if status_data else False
    
    if is_running:
        st.sidebar.success("🟢 Campagne en cours")
        if st.sidebar.button("🛑 STOPPER LA CAMPAGNE", type="primary"):
            with open(STOP_FLAG_FILE, 'w') as f:
                f.write('STOP')
            st.sidebar.warning("Signal d'arrêt envoyé...")
            time.sleep(1)
            st.rerun()
    else:
        st.sidebar.info("🔴 Campagne à l'arrêt")
        
        # Test Mode Toggle
        is_dry_run = st.sidebar.checkbox("Mode Test (Dry Run)", value=True, help="Si coché, aucun email ne sera réellement envoyé.")
        
        if st.sidebar.button("▶️ LANCER LA CAMPAGNE"):
            # Launch mailer.py in a separate process using the same interpreter
            # mailer.py is in the same directory as this script
            mailer_path = os.path.join(SCRIPT_DIR, "mailer.py")
            cmd = [sys.executable, mailer_path]
            if not is_dry_run:
                cmd.append("--real")
            
            # creationflags is Windows specific, cwd ensures correct working directory
            kwargs = {'cwd': SCRIPT_DIR}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(cmd, **kwargs)
            
            mode_msg = "TEST (Dry Run)" if is_dry_run else "RÉEL"
            st.sidebar.success(f"Démarrage initié en mode {mode_msg}...")
            time.sleep(2)
            st.rerun()

    if status_data:
        st.sidebar.markdown(f"**Status:** {status_data.get('message', '')}")
        if 'progress' in status_data:
            st.sidebar.progress(status_data['progress'] / 100)
        st.sidebar.text(f"Dernière MAJ: {time.strftime('%H:%M:%S', time.localtime(status_data.get('timestamp', 0)))}")

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
        
        # Auto-refresh logic
        if is_running:
            time.sleep(2) # Refresh every 2s if running
            st.rerun()
        elif st.button('🔄 Actualiser les données'):
            st.rerun()

    else:
        st.info("Aucune donnée trouvée dans la base de données.")

if __name__ == "__main__":
    main()

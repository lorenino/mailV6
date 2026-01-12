"""
Script d'import de mail.xlsx vers clients.db
Réinitialise la base de données avec les nouveaux emails.
"""
import pandas as pd
import sqlite3
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
EXCEL_FILE = os.path.join(SCRIPT_DIR, '..', 'mail.xlsx')
DB_FILE = os.path.join(DATA_DIR, 'clients.db')

def import_excel_to_db(excel_path=EXCEL_FILE, reset=True):
    """
    Importe les emails depuis le fichier Excel vers clients.db
    
    Args:
        excel_path: Chemin vers le fichier Excel
        reset: Si True, supprime les anciens contacts et repart à zéro
    """
    print(f"📂 Lecture de {excel_path}...")
    
    # Lire le fichier Excel
    df = pd.read_excel(excel_path)
    
    # Identifier la colonne email (première colonne ou colonne contenant '@')
    email_col = None
    for col in df.columns:
        # Vérifie si la colonne contient des emails
        sample = df[col].dropna().head(10).astype(str)
        if sample.str.contains('@').any():
            email_col = col
            break
    
    if email_col is None:
        print("❌ Erreur: Aucune colonne email trouvée!")
        return False
    
    print(f"✅ Colonne email détectée: '{email_col}'")
    
    # Nettoyer les emails
    emails = df[email_col].dropna().astype(str).str.strip().str.lower()
    emails = emails[emails.str.contains('@', na=False)]  # Garder uniquement les emails valides
    emails = emails.drop_duplicates()  # Supprimer les doublons
    
    print(f"📧 {len(emails)} emails valides trouvés (après dédoublonnage)")
    
    # Connexion à la base de données
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if reset:
        print("🗑️  Réinitialisation de la base de données...")
        cursor.execute("DROP TABLE IF EXISTS clients")
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            Provenance TEXT,
            Civilité TEXT,
            Nom TEXT,
            Prénom TEXT,
            "Société - Nom" TEXT,
            "Email 1" TEXT,
            "Envoyé ?" TEXT
        )
    ''')
    
    # Insérer les emails
    inserted = 0
    for email in emails:
        try:
            cursor.execute('''
                INSERT INTO clients (Provenance, Civilité, Nom, Prénom, "Société - Nom", "Email 1", "Envoyé ?")
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Import Excel', '', '', '', '', email, 'NON'))
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # Email déjà existant
    
    conn.commit()
    conn.close()
    
    print(f"✅ {inserted} emails importés dans clients.db")
    print(f"📍 Base de données: {DB_FILE}")
    return True


if __name__ == "__main__":
    # Option: passer le chemin du fichier en argument
    excel_path = sys.argv[1] if len(sys.argv) > 1 else EXCEL_FILE
    
    # Option: --append pour ajouter sans réinitialiser
    reset = "--append" not in sys.argv
    
    if not os.path.exists(excel_path):
        print(f"❌ Fichier non trouvé: {excel_path}")
        sys.exit(1)
    
    success = import_excel_to_db(excel_path, reset)
    sys.exit(0 if success else 1)

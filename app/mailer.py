import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import random
import json
import os
import sys
from db_utils import get_unsent_clients, mark_as_sent

# Configuration Files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
STOP_FLAG_FILE = os.path.join(DATA_DIR, 'stop.flag')
STATUS_FILE = os.path.join(DATA_DIR, 'status.json')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        update_status("Erreur: Config introuvable", running=False)
        return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_template(template_file):
    if not os.path.exists(template_file):
        update_status(f"Erreur: Template {template_file} introuvable", running=False)
        return None
    with open(template_file, 'r', encoding='utf-8') as f:
        return f.read()

def update_status(message, running=True, progress=None):
    """Writes the current status to a JSON file."""
    status = {
        "running": running,
        "message": message,
        "timestamp": time.time()
    }
    if progress:
        status["progress"] = progress
        
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f)

def check_stop_flag():
    """Checks if the stop flag file exists."""
    if os.path.exists(STOP_FLAG_FILE):
        try:
            os.remove(STOP_FLAG_FILE)
        except:
            pass
        return True
    return False

def send_email(smtp_config, to_email, subject, html_content, debug=False):
    msg = MIMEMultipart()
    msg['From'] = smtp_config['from_email']
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        if debug:
            server.set_debuglevel(1)
        server.login(smtp_config['user'], smtp_config['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False

def main(dry_run=False):
    # Clear any existing stop flag on startup
    if os.path.exists(STOP_FLAG_FILE):
        os.remove(STOP_FLAG_FILE)

    update_status("Démarrage de la campagne...", running=True)
    
    config = load_config()
    if not config:
        return

    camp_conf = config['campaign']
    smtp_conf = config['smtp']
    
    # Prepend ../data/ to template file path if it's just a filename
    template_path = camp_conf['template_file']
    if not os.path.isabs(template_path) and not template_path.startswith('../'):
         template_path = os.path.join('../data', template_path)

    template = load_template(template_path)
    if not template:
        return

    clients = get_unsent_clients()
    total_to_send = len(clients)
    
    if total_to_send == 0:
        update_status("Aucun email à envoyer.", running=False)
        return

    update_status(f"Prêt à envoyer {total_to_send} emails.", running=True)
    
    count = 0
    for i, client in enumerate(clients):
        if check_stop_flag():
            update_status("Campagne stoppée par l'utilisateur.", running=False)
            print("Stop flag detected. Exiting.")
            return

        email = client['Email 1']
        client_id = client['id']
        
        # Update status with current action
        progress_pct = int((i / total_to_send) * 100)
        update_status(f"Envoi en cours à {email}...", running=True, progress=progress_pct)
        
        # Personalization
        personalized_html = template # Add replacement logic here if needed

        if not dry_run:
            success = send_email(smtp_conf, email, camp_conf['subject'], personalized_html)
            if success:
                mark_as_sent(client_id)
                count += 1
                
                # Random delay
                delay = random.randint(camp_conf['min_delay_seconds'], camp_conf['max_delay_seconds'])
                for d in range(delay, 0, -1):
                    if check_stop_flag():
                        update_status("Campagne stoppée pendant le délai.", running=False)
                        return
                    update_status(f"Pause: reprise dans {d}s (Envoyé à {email})", running=True, progress=progress_pct)
                    time.sleep(1)
            else:
                print(f"Failed to send to {email}")
        else:
            print(f"[DRY RUN] Would send to {email}")
            count += 1
            time.sleep(1)

    update_status("Campagne terminée avec succès !", running=False, progress=100)

if __name__ == "__main__":
    # Check for command line argument to disable dry_run
    dry_run = "--real" not in sys.argv
    main(dry_run=dry_run)

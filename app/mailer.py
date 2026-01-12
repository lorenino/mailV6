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
    """Load config from environment variables (priority) or config.json (fallback)."""
    # Try to load base config from file
    base_config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            base_config = json.load(f)
    
    # Override with environment variables if set
    config = {
        "smtp": {
            "host": os.environ.get("SMTP_HOST", base_config.get("smtp", {}).get("host", "")),
            "port": int(os.environ.get("SMTP_PORT", base_config.get("smtp", {}).get("port", 25))),
            "user": os.environ.get("SMTP_USER", base_config.get("smtp", {}).get("user", "")),
            "password": os.environ.get("SMTP_PASSWORD", base_config.get("smtp", {}).get("password", "")),
            "from_email": os.environ.get("SMTP_FROM_EMAIL", base_config.get("smtp", {}).get("from_email", ""))
        },
        "campaign": {
            "daily_limit": int(os.environ.get("CAMPAIGN_DAILY_LIMIT", base_config.get("campaign", {}).get("daily_limit", 500))),
            "min_delay_seconds": int(os.environ.get("CAMPAIGN_MIN_DELAY", base_config.get("campaign", {}).get("min_delay_seconds", 30))),
            "max_delay_seconds": int(os.environ.get("CAMPAIGN_MAX_DELAY", base_config.get("campaign", {}).get("max_delay_seconds", 300))),
            "template_file": base_config.get("campaign", {}).get("template_file", "email_template.html"),
            "subject": os.environ.get("CAMPAIGN_SUBJECT", base_config.get("campaign", {}).get("subject", ""))
        }
    }
    
    # Validate required fields
    if not config["smtp"]["host"] or not config["smtp"]["from_email"]:
        update_status("Erreur: Config SMTP incomplète", running=False)
        return None
    
    return config

def load_template(template_file):
    if not os.path.exists(template_file):
        update_status(f"Erreur: Template {template_file} introuvable", running=False)
        return None
    with open(template_file, 'r', encoding='utf-8') as f:
        return f.read()

def update_status(message, running=True, progress=None, sent=0, remaining=0, failed=0, mode=""):
    """Writes the current status to a JSON file with detailed info."""
    status = {
        "running": running,
        "message": message,
        "timestamp": time.time(),
        "sent": sent,
        "remaining": remaining,
        "failed": failed,
        "mode": mode
    }
    if progress is not None:
        status["progress"] = progress
    
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f)
    except Exception as e:
        print(f"[ERROR] Failed to write status file: {e}")

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
    mode_str = "TEST" if dry_run else "RÉEL"
    
    # Clear any existing stop flag on startup
    if os.path.exists(STOP_FLAG_FILE):
        os.remove(STOP_FLAG_FILE)

    update_status(f"Démarrage en mode {mode_str}...", running=True, mode=mode_str)
    
    try:
        config = load_config()
        if not config:
            return

        camp_conf = config['campaign']
        smtp_conf = config['smtp']
        daily_limit = camp_conf.get('daily_limit', 500)
        
        # Prepend ../data/ to template file path if it's just a filename
        template_path = camp_conf['template_file']
        if not os.path.isabs(template_path) and not template_path.startswith('../'):
             template_path = os.path.join('../data', template_path)

        template = load_template(template_path)
        if not template:
            return

        clients = get_unsent_clients()
        total_to_send = min(len(clients), daily_limit)  # Respect daily limit
        remaining = len(clients)
        
        if total_to_send == 0:
            update_status("Aucun email à envoyer.", running=False, sent=0, remaining=0, mode=mode_str)
            return

        update_status(
            f"Prêt: {total_to_send} emails à envoyer (limite: {daily_limit}/jour)", 
            running=True, remaining=total_to_send, mode=mode_str
        )
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        for i, client in enumerate(clients[:total_to_send]):  # Apply daily limit
            if check_stop_flag():
                update_status(
                    f"Stoppé: {sent_count} envoyés, {failed_count} échecs", 
                    running=False, sent=sent_count, remaining=total_to_send-i, failed=failed_count, mode=mode_str
                )
                print("Stop flag detected. Exiting.")
                return

            email = client.get('Email 1', '')
            client_id = client.get('id')
            client_name = client.get('Nom', 'N/A')
            
            if not email:
                print(f"[SKIP] Client {client_id} has no email")
                failed_count += 1
                continue
            
            # Update status with current action
            progress_pct = int(((i + 1) / total_to_send) * 100)
            current_remaining = total_to_send - i - 1
            
            update_status(
                f"Envoi {i+1}/{total_to_send}: {email}", 
                running=True, progress=progress_pct, sent=sent_count, remaining=current_remaining, failed=failed_count, mode=mode_str
            )
            
            # Personalization
            personalized_html = template  # Add replacement logic here if needed

            if not dry_run:
                success = send_email(smtp_conf, email, camp_conf['subject'], personalized_html)
                if success:
                    try:
                        mark_as_sent(client_id)
                        sent_count += 1
                    except Exception as db_error:
                        print(f"[DB ERROR] Failed to mark {email} as sent: {db_error}")
                        failed_count += 1
                        failed_emails.append(email)
                        continue
                    
                    # Random delay
                    delay = random.randint(camp_conf['min_delay_seconds'], camp_conf['max_delay_seconds'])
                    for d in range(delay, 0, -1):
                        if check_stop_flag():
                            update_status(
                                f"Stoppé pendant pause: {sent_count} envoyés", 
                                running=False, sent=sent_count, remaining=current_remaining, failed=failed_count, mode=mode_str
                            )
                            return
                        update_status(
                            f"Pause {d}s - Dernier: {email}", 
                            running=True, progress=progress_pct, sent=sent_count, remaining=current_remaining, failed=failed_count, mode=mode_str
                        )
                        time.sleep(1)
                else:
                    failed_count += 1
                    failed_emails.append(email)
                    print(f"[FAILED] {email}")
            else:
                print(f"[DRY RUN] {email}")
                sent_count += 1
                time.sleep(0.5)  # Shorter delay in test mode

        # Final status
        status_msg = f"Terminé! {sent_count} envoyés"
        if failed_count > 0:
            status_msg += f", {failed_count} échecs"
        update_status(status_msg, running=False, progress=100, sent=sent_count, remaining=0, failed=failed_count, mode=mode_str)
        
        if failed_emails:
            print(f"[REPORT] Failed emails: {failed_emails}")
            
    except Exception as e:
        error_msg = f"Erreur critique: {str(e)[:100]}"
        print(f"[CRITICAL] {e}")
        update_status(error_msg, running=False, failed=1, mode=mode_str)
        raise

if __name__ == "__main__":
    # Check for command line argument to disable dry_run
    dry_run = "--real" not in sys.argv
    main(dry_run=dry_run)

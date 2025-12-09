from mailer import load_config, load_template, send_email, DATA_DIR
import os

TEST_EMAIL = "lfaloci@datacorp-lyon.fr"

def send_test():
    print(f"Preparing to send TEST email to {TEST_EMAIL}...")
    
    # 1. Load Config
    config = load_config()
    if not config:
        print("Failed to load config.")
        return

    smtp_conf = config['smtp']
    camp_conf = config['campaign']

    # 2. Load Template (fix path like mailer.py)
    template_path = camp_conf['template_file']
    if not os.path.isabs(template_path) and not template_path.startswith('../'):
        template_path = os.path.join(DATA_DIR, template_path)
    
    template = load_template(template_path)
    if not template:
        print("Failed to load template.")
        return

    # 3. Send Email
    print("Sending...")
    success = send_email(smtp_conf, TEST_EMAIL, f"[TEST] {camp_conf['subject']}", template, debug=True)
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email.")

if __name__ == "__main__":
    send_test()

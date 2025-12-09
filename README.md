# Automate Mailing

Outil d'envoi d'emails automatisés.

## 📂 Fichiers du Projet

- **`mailer.py`** : Script d'envoi (lit `clients.db` et envoie les mails).
- **`send_test.py`** : Script de test (envoi unique).
- **`config.json`** : Configuration (SMTP, délais, sujet).
- **`clients.db`** : Base de données clients.
- **`email_template.html`** : Modèle du mail.

## 🚀 Utilisation

### 1. Tester
Ouvrez un terminal et lancez :
```bash
python send_test.py
```
Cela envoie un mail de test à l'adresse configurée dans le script.

### 2. Dashboard de Suivi (Nouveau 📊)
Pour voir l'avancement en temps réel (barre de progression, stats) :
```bash
python -m streamlit run dashboard.py
```
Cela ouvrira une page web avec le tableau de bord.

### 3. Envoyer la Campagne
1. Éditez `mailer.py` et changez la dernière ligne : `main(dry_run=False)`.
2. Lancez :
```bash
python mailer.py
```

## ⚙️ Configuration (`config.json`)
- **`daily_limit`** : Nombre max d'emails par jour.
- **`min_delay_seconds`** / **`max_delay_seconds`** : Pause aléatoire entre chaque mail.

## 🌐 Déploiement sur VPS (Linux/Windows)

Voici la procédure rapide pour installer et lancer le dashboard sur un serveur.

### 1. Installation
Copiez les fichiers sur le serveur, puis lancez :
```bash
pip install -r requirements.txt
```

### 2. Lancement (Mode Persistant)
Pour que le dashboard continue de tourner même après avoir fermé la console (Linux) :
```bash
nohup python -m streamlit run dashboard.py --server.port 8501 &
```
*Note : Sur Windows Server, lancez simplement la commande via PowerShell ou créez une tâche planifiée.*

### 3. Accès
Accédez à votre dashboard via : `http://VOTRE_IP_VPS:8501`
*(Assurez-vous d'avoir ouvert le port 8501 dans le pare-feu)*

## 🐳 Déploiement Docker (Portainer / Alpine)

Le projet est prêt pour être déployé via Docker (image Alpine légère).

### Via Portainer (Stack)
1.  Créez une nouvelle **Stack**.
2.  Copiez le contenu du fichier `docker-compose.yml`.
3.  Assurez-vous que le dossier `data/` existe sur le serveur ou laissez Docker le créer (mais pensez à y mettre votre `clients.db` et `config.json`).
    *Conseil : Il est préférable de cloner le repo Git dans Portainer pour avoir tous les fichiers.*

### Via CLI
```bash
# Construire et lancer
docker-compose up -d --build
```

Les données (`clients.db`, `config.json`) sont persistées dans le dossier `./data` de l'hôte.

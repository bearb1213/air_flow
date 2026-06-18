#!/bin/bash
# ============================================================
#  INSTALLATION APACHE AIRFLOW 2.8.0 — Projet Traiteur
#  Exécuter ce script une seule fois depuis le dossier projet
# ============================================================

set -e  # Arrêter si une commande échoue

echo "======================================"
echo " 1. Création du venv Python"
echo "======================================"
python3 -m venv venv
source venv/bin/activate

echo "======================================"
echo " 2. Mise à jour pip"
echo "======================================"
pip install --upgrade pip

echo "======================================"
echo " 3. Installation Apache Airflow 2.8.0"
echo "======================================"
# Contrainte officielle pour Python 3.10 (compatible 3.8-3.11)
pip install apache-airflow==2.8.0 --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.0/constraints-3.10.txt"

echo "======================================"
echo " 4. Installation des dépendances ETL"
echo "======================================"
pip install apache-airflow-providers-postgres==5.7.1 pandas==2.1.4 openpyxl==3.1.2 psycopg2-binary==2.9.9 sqlalchemy==1.4.51

echo "======================================"
echo " 5. Configuration AIRFLOW_HOME"
echo "======================================"
export AIRFLOW_HOME=~/airflow
echo "export AIRFLOW_HOME=~/airflow" >> ~/.bashrc
echo "export AIRFLOW_HOME=~/airflow" >> ~/.zshrc 2>/dev/null || true

echo "======================================"
echo " 6. Initialisation de la base Airflow"x   
echo "======================================"
airflow db init

echo "======================================"
echo " 7. Création de l'utilisateur admin"
echo "======================================"
airflow users create --username admin --firstname Admin --lastname Traiteur --role Admin --email admin@traiteur.mg --password admin123

echo "======================================"
echo " 8. Copie du DAG dans ~/airflow/dags/"
echo "======================================"
mkdir -p ~/airflow/dags
cp dags/dag_traiteur_etl.py ~/airflow/dags/

echo ""
echo "======================================"
echo "  INSTALLATION TERMINÉE !"
echo "======================================"
echo ""
echo "  Pour démarrer Airflow :"
echo ""
echo "  Terminal 1 (webserver) :"
echo "    source venv/bin/activate"
echo "    airflow webserver --port 8080"
echo ""
echo "  Terminal 2 (scheduler) :"
echo "    source venv/bin/activate"
echo "    airflow scheduler"
echo ""
echo "  Interface web : http://localhost:8080"
echo "  Login : admin / admin123"
echo ""
echo "  N'oubliez pas de configurer la Connection PostgreSQL"
echo "  dans l'UI : Admin > Connections > postgres_traiteur_dwh"
echo "======================================"

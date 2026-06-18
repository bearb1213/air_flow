"""
============================================================
 DAG ETL — Projet Traiteur
 Cours : DataWarehouse
 
 Pipeline :
   1. check_sources      → vérifie que les fichiers Excel/CSV existent
   2. extract_postgres   → lit les tables PostgreSQL (Django)
   3. extract_fichiers   → lit Excel + CSV
   4. transform          → nettoie, calcule, agrège
   5. load_dimensions    → charge les 5 tables dim_*
   6. load_faits         → charge la table fait_traiteur
   7. rapport_final      → affiche un résumé dans les logs

 Planification : tous les lundis à 6h du matin
 Base source  : PostgreSQL "traiteur"  (votre appli Django)
 Base cible   : PostgreSQL "traiteur_dwh" (Data Warehouse)
============================================================
"""

# ── Imports standard Airflow ──────────────────────────────────────────────────
from airflow import DAG
# from airflow.operators.python import PythonOperator
# from airflow.sensors.filesystem import FileSensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.filesystem import FileSensor
from datetime import datetime, timedelta
import logging

# ── Imports Python pour l'ETL ────────────────────────────────────────────────
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ── Logger ───────────────────────────────────────────────────────────────────
log = logging.getLogger(__name__)

# ============================================================
#  CONFIGURATION — à adapter à votre environnement
# ============================================================

# Chemin vers vos fichiers de données
# Mettez ici le chemin absolu vers le dossier contenant vos xlsx/csv
DOSSIER_DONNEES = os.path.join(os.path.dirname(__file__), '..', 'data')

FICHIER_TRAITEUR = os.path.join(DOSSIER_DONNEES, 'traiteur.xlsx')
FICHIER_MENU     = os.path.join(DOSSIER_DONNEES, 'menu_traiteur.xlsx')
FICHIER_EQUIPE   = os.path.join(DOSSIER_DONNEES, 'equipe.csv')
FICHIER_MATERIEL = os.path.join(DOSSIER_DONNEES, 'materiel_traiteur.csv')

# Connexion base source (votre appli Django)
DB_SOURCE = {
    'host':     'localhost',
    'port':     5432,
    'dbname':   'traiteur',
    'user':     'postgres',
    'password': 'tsila',      # même mot de passe que dans settings.py
}

# Connexion base cible (Data Warehouse)
DB_DWH = {
    'host':     'localhost',
    'port':     5432,
    'dbname':   'traiteur_dwh',
    'user':     'postgres',
    'password': 'tsila',
}

# ============================================================
#  PARAMÈTRES PAR DÉFAUT DU DAG
# ============================================================

default_args = {
    'owner':            'etudiant',
    'depends_on_past':  False,
    'start_date':       datetime(2024, 1, 1),
    'retries':          1,
    'retry_delay':      timedelta(minutes=5),
    'email_on_failure': False,   # mettre True + configurer SMTP si vous voulez
}

# ============================================================
#  ÉTAPE 1 — VÉRIFICATION DES SOURCES
# ============================================================

def verifier_sources(**context):
    """
    Vérifie que tous les fichiers Excel et CSV sont bien présents
    avant de lancer l'extraction.
    Arrête le DAG avec une erreur claire si un fichier manque.
    """
    fichiers = {
        'traiteur.xlsx':        FICHIER_TRAITEUR,
        'menu_traiteur.xlsx':   FICHIER_MENU,
        'equipe.csv':           FICHIER_EQUIPE,
        'materiel_traiteur.csv': FICHIER_MATERIEL,
    }

    manquants = []
    for nom, chemin in fichiers.items():
        if os.path.exists(chemin):
            taille = os.path.getsize(chemin)
            log.info(f"  [OK] {nom} trouvé ({taille} octets)")
        else:
            log.error(f"  [MANQUANT] {nom} introuvable : {chemin}")
            manquants.append(nom)

    if manquants:
        raise FileNotFoundError(
            f"Fichiers manquants : {', '.join(manquants)}\n"
            f"Vérifiez le dossier : {DOSSIER_DONNEES}"
        )

    log.info("Tous les fichiers sources sont présents. On peut continuer.")

# ============================================================
#  ÉTAPE 2 — EXTRACTION POSTGRESQL (base Django)
# ============================================================

def extraire_postgres(**context):
    """
    Lit les tables de la base Django (source opérationnelle) :
    - clients
    - employes
    - materiels
    - plats
    - materiel_types / plat_types

    Stocke les DataFrames dans XCom pour la prochaine tâche.
    """
    log.info("Connexion à la base PostgreSQL source : traiteur")
    conn = psycopg2.connect(**DB_SOURCE)

    # -- Lire les tables une par une
    tables = {
        'clients':        "SELECT * FROM clients",
        'employes':       "SELECT * FROM employes",
        'materiels':      "SELECT * FROM materiels",
        'plats':          "SELECT * FROM plats",
        'plat_types':     "SELECT * FROM plat_types",
        'materiel_types': "SELECT * FROM materiel_types",
    }

    donnees_pg = {}
    for nom_table, requete in tables.items():
        df = pd.read_sql_query(requete, conn)
        log.info(f"  Table '{nom_table}' : {len(df)} lignes extraites")
        donnees_pg[nom_table] = df.to_json(orient='records', date_format='iso')

    conn.close()
    log.info("Extraction PostgreSQL terminée.")

    # XCom : passer les données à la tâche transform
    context['ti'].xcom_push(key='donnees_pg', value=donnees_pg)

# ============================================================
#  ÉTAPE 3 — EXTRACTION FICHIERS (Excel + CSV)
# ============================================================

def extraire_fichiers(**context):
    """
    Lit les fichiers Excel et CSV fournis :
    - traiteur.xlsx     → événements (code, client, nb_pax, date, lieu, statut)
    - menu_traiteur.xlsx → plats par événement
    - equipe.csv        → employés par événement (salaire, heures)
    - materiel_traiteur.csv → matériels par événement

    Stocke les DataFrames en XCom.
    """
    log.info("Lecture des fichiers Excel et CSV...")

    # -- Excel : traiteur.xlsx
    df_traiteur = pd.read_excel(FICHIER_TRAITEUR, sheet_name='Donnees')
    log.info(f"  traiteur.xlsx : {len(df_traiteur)} lignes, colonnes : {list(df_traiteur.columns)}")

    # -- Excel : menu_traiteur.xlsx
    df_menu = pd.read_excel(FICHIER_MENU, sheet_name='Donnees')
    log.info(f"  menu_traiteur.xlsx : {len(df_menu)} lignes")

    # -- CSV : equipe.csv (séparateur ;)
    df_equipe = pd.read_csv(FICHIER_EQUIPE, sep=';')
    log.info(f"  equipe.csv : {len(df_equipe)} lignes")

    # -- CSV : materiel_traiteur.csv (séparateur ;)
    df_materiel = pd.read_csv(FICHIER_MATERIEL, sep=';')
    log.info(f"  materiel_traiteur.csv : {len(df_materiel)} lignes")

    donnees_fichiers = {
        'traiteur':  df_traiteur.to_json(orient='records', date_format='iso'),
        'menu':      df_menu.to_json(orient='records', date_format='iso'),
        'equipe':    df_equipe.to_json(orient='records'),
        'materiel':  df_materiel.to_json(orient='records'),
    }

    log.info("Extraction fichiers terminée.")
    context['ti'].xcom_push(key='donnees_fichiers', value=donnees_fichiers)

# ============================================================
#  ÉTAPE 4 — TRANSFORMATION
# ============================================================

def transformer(**context):
    """
    Transformations appliquées :

    1. Nettoyage
       - Garder seulement les traiteurs 'confirme'
       - Normaliser les valeurs (minuscules, strip espaces)
       - Convertir les dates en format standard

    2. Calculs par événement
       - total_salaires  = somme(salaire × heure_travail) des employés
       - total_materiels = somme(prix) des matériels
       - cout_preparation = somme(cout_preparation × nb_pax) des plats
       - revenus_plats   = somme(prix × nb_pax) des plats
       - marge_brute     = revenus_plats - (cout_preparation + total_salaires + total_materiels)

    3. Préparation des dimensions
       - dim_client, dim_lieu, dim_date, dim_plat, dim_statut

    Stocke les résultats en XCom pour la tâche load.
    """
    ti = context['ti']

    # ── Récupérer les données depuis XCom ─────────────────────
    donnees_pg       = ti.xcom_pull(key='donnees_pg',       task_ids='extraire_postgres')
    donnees_fichiers = ti.xcom_pull(key='donnees_fichiers', task_ids='extraire_fichiers')

    # Reconstruire les DataFrames
    df_clients  = pd.read_json(donnees_pg['clients'])
    df_employes = pd.read_json(donnees_pg['employes'])
    df_plats_pg = pd.read_json(donnees_pg['plats'])

    df_traiteur = pd.read_json(donnees_fichiers['traiteur'])
    df_menu     = pd.read_json(donnees_fichiers['menu'])
    df_equipe   = pd.read_json(donnees_fichiers['equipe'])
    df_materiel = pd.read_json(donnees_fichiers['materiel'])

    log.info(f"Données chargées — traiteurs : {len(df_traiteur)}, menu : {len(df_menu)}")

    # ── 1. NETTOYAGE ──────────────────────────────────────────

    # Normaliser la colonne statut (enlever espaces, mettre en minuscules)
    df_traiteur['status'] = df_traiteur['status'].str.strip().str.lower()

    # Conserver uniquement les événements confirmés
    nb_avant = len(df_traiteur)
    df_traiteur = df_traiteur[df_traiteur['status'] == 'confirme'].copy()
    log.info(f"Nettoyage statut : {nb_avant} → {len(df_traiteur)} traiteurs confirmés conservés")

    # Convertir la colonne date en datetime
    df_traiteur['date'] = pd.to_datetime(df_traiteur['date'])

    # Nettoyer le lieu (enlever espaces en début/fin)
    df_traiteur['lieu'] = df_traiteur['lieu'].str.strip()

    # ── 2. CALCULS PAR ÉVÉNEMENT ──────────────────────────────

    # -- Coût total des employés par traiteur
    #    salaire (journalier) × heure_travail → on utilise le salaire brut direct
    cout_equipe = (
        df_equipe
        .groupby('traiteur_code')['salaire']
        .sum()
        .reset_index()
        .rename(columns={'salaire': 'total_salaires'})
    )

    # -- Nombre d'employés par traiteur
    nb_employes = (
        df_equipe
        .groupby('traiteur_code')['emp_code']
        .count()
        .reset_index()
        .rename(columns={'emp_code': 'nb_employes'})
    )

    # -- Coût total des matériels par traiteur
    cout_mat = (
        df_materiel
        .groupby('traiteur_code')['prix']
        .sum()
        .reset_index()
        .rename(columns={'prix': 'total_materiels'})
    )

    # -- Nombre de matériels par traiteur
    nb_mat = (
        df_materiel
        .groupby('traiteur_code')['materiel_code']
        .count()
        .reset_index()
        .rename(columns={'materiel_code': 'nb_materiels'})
    )

    # -- Calculs sur les menus (par traiteur, multiplié par nb_pax)
    #    On joint le nb_pax depuis df_traiteur
    df_menu_pax = df_menu.merge(
        df_traiteur[['code_traiteur', 'nb_pax']],
        left_on='code_traiteur',
        right_on='code_traiteur',
        how='left'
    )
    df_menu_pax['cout_prep_total']  = df_menu_pax['cout_preparation'] * df_menu_pax['nb_pax']
    df_menu_pax['revenu_plat_total'] = df_menu_pax['prix']            * df_menu_pax['nb_pax']

    cout_plats = (
        df_menu_pax
        .groupby('code_traiteur')
        .agg(
            cout_preparation=('cout_prep_total',  'sum'),
            revenus_plats   =('revenu_plat_total', 'sum'),
            nb_plats        =('plat_code',         'count'),
        )
        .reset_index()
    )

    # ── 3. ASSEMBLAGE TABLE DE FAITS ──────────────────────────

    df_faits = df_traiteur.copy()

    # Jointures pour ajouter tous les calculs
    df_faits = df_faits.merge(cout_equipe, on='traiteur_code' if 'traiteur_code' in df_faits.columns else 'code_traiteur', how='left')

    # Renommer la colonne code_traiteur pour faciliter les jointures
    if 'code_traiteur' in df_faits.columns:
        df_faits = df_faits.rename(columns={'code_traiteur': 'traiteur_code'})

    df_faits = df_faits.merge(cout_equipe,   on='traiteur_code', how='left')
    df_faits = df_faits.merge(nb_employes,   on='traiteur_code', how='left')
    df_faits = df_faits.merge(cout_mat,      on='traiteur_code', how='left')
    df_faits = df_faits.merge(nb_mat,        on='traiteur_code', how='left')
    df_faits = df_faits.merge(cout_plats,    on='traiteur_code', how='left')

    # Remplacer les NaN par 0 (traiteurs sans employés / matériels)
    for col in ['total_salaires', 'total_materiels', 'cout_preparation',
                'revenus_plats', 'nb_employes', 'nb_materiels', 'nb_plats']:
        df_faits[col] = df_faits[col].fillna(0)

    # Calcul de la marge brute
    df_faits['marge_brute'] = (
        df_faits['revenus_plats']
        - df_faits['cout_preparation']
        - df_faits['total_salaires']
        - df_faits['total_materiels']
    )

    log.info(f"Table de faits construite : {len(df_faits)} lignes")
    log.info(f"  Revenus totaux  : {df_faits['revenus_plats'].sum():,.0f} Ar")
    log.info(f"  Coûts totaux    : {(df_faits['cout_preparation'] + df_faits['total_salaires'] + df_faits['total_materiels']).sum():,.0f} Ar")
    log.info(f"  Marge brute     : {df_faits['marge_brute'].sum():,.0f} Ar")

    # ── 4. PRÉPARER LES DIMENSIONS ────────────────────────────

    # Dimension Client
    dim_client = df_clients[['client_code', 'nom', 'prenom', 'email', 'telephone']].drop_duplicates()

    # Dimension Lieu
    dim_lieu = pd.DataFrame({'lieu_label': df_traiteur['lieu'].unique()})

    # Dimension Date
    dates_uniques = df_traiteur['date'].dt.date.unique()
    dim_date = pd.DataFrame({'date_complete': dates_uniques})
    dim_date['date_complete'] = pd.to_datetime(dim_date['date_complete'])
    dim_date['annee']       = dim_date['date_complete'].dt.year
    dim_date['mois']        = dim_date['date_complete'].dt.month
    dim_date['nom_mois']    = dim_date['date_complete'].dt.strftime('%B')
    dim_date['trimestre']   = dim_date['date_complete'].dt.quarter
    dim_date['jour_semaine'] = dim_date['date_complete'].dt.strftime('%A')

    # Dimension Statut
    dim_statut = pd.DataFrame({'statut_label': ['confirme', 'annule', 'en attente']})

    # Dimension Plat
    dim_plat = df_menu[['plat_code', 'label', 'type_plat', 'cout_preparation', 'prix']].drop_duplicates('plat_code')
    dim_plat = dim_plat.rename(columns={'prix': 'prix_unitaire'})

    log.info("Dimensions préparées.")

    # ── Passer tout en XCom ───────────────────────────────────
    donnees_transformees = {
        'faits':      df_faits.to_json(orient='records', date_format='iso'),
        'dim_client': dim_client.to_json(orient='records'),
        'dim_lieu':   dim_lieu.to_json(orient='records'),
        'dim_date':   dim_date.to_json(orient='records', date_format='iso'),
        'dim_statut': dim_statut.to_json(orient='records'),
        'dim_plat':   dim_plat.to_json(orient='records'),
    }
    ti.xcom_push(key='donnees_transformees', value=donnees_transformees)
    log.info("Transformation terminée. Données prêtes pour le chargement.")

# ============================================================
#  ÉTAPE 5 — CHARGEMENT DES DIMENSIONS
# ============================================================

def charger_dimensions(**context):
    """
    Charge les 5 tables de dimensions dans le Data Warehouse.
    Stratégie : INSERT … ON CONFLICT DO NOTHING (idempotent)
    → si on relance le DAG, pas de doublons.
    """
    ti = context['ti']
    donnees = ti.xcom_pull(key='donnees_transformees', task_ids='transformer')

    conn = psycopg2.connect(**DB_DWH)
    cur  = conn.cursor()

    # ── dim_client ────────────────────────────────────────────
    df_client = pd.read_json(donnees['dim_client'])
    if not df_client.empty:
        rows = [tuple(r) for r in df_client[['client_code','nom','prenom','email','telephone']].values]
        execute_values(cur, """
            INSERT INTO dim_client (client_code, nom, prenom, email, telephone)
            VALUES %s
            ON CONFLICT (client_code) DO NOTHING
        """, rows)
        log.info(f"dim_client : {len(rows)} lignes insérées/ignorées")

    # ── dim_lieu ──────────────────────────────────────────────
    df_lieu = pd.read_json(donnees['dim_lieu'])
    if not df_lieu.empty:
        rows = [(r,) for r in df_lieu['lieu_label'].values]
        execute_values(cur, """
            INSERT INTO dim_lieu (lieu_label)
            VALUES %s
            ON CONFLICT (lieu_label) DO NOTHING
        """, rows)
        log.info(f"dim_lieu : {len(rows)} lignes insérées/ignorées")

    # ── dim_date ──────────────────────────────────────────────
    df_date = pd.read_json(donnees['dim_date'])
    if not df_date.empty:
        df_date['date_complete'] = pd.to_datetime(df_date['date_complete']).dt.date
        rows = [tuple(r) for r in df_date[['date_complete','annee','mois','nom_mois','trimestre','jour_semaine']].values]
        execute_values(cur, """
            INSERT INTO dim_date (date_complete, annee, mois, nom_mois, trimestre, jour_semaine)
            VALUES %s
            ON CONFLICT (date_complete) DO NOTHING
        """, rows)
        log.info(f"dim_date : {len(rows)} lignes insérées/ignorées")

    # ── dim_statut ────────────────────────────────────────────
    df_statut = pd.read_json(donnees['dim_statut'])
    if not df_statut.empty:
        rows = [(r,) for r in df_statut['statut_label'].values]
        execute_values(cur, """
            INSERT INTO dim_statut (statut_label)
            VALUES %s
            ON CONFLICT (statut_label) DO NOTHING
        """, rows)
        log.info(f"dim_statut : {len(rows)} lignes insérées/ignorées")

    # ── dim_plat ──────────────────────────────────────────────
    df_plat = pd.read_json(donnees['dim_plat'])
    if not df_plat.empty:
        rows = [tuple(r) for r in df_plat[['plat_code','label','type_plat','prix_unitaire','cout_preparation']].values]
        execute_values(cur, """
            INSERT INTO dim_plat (plat_code, label, type_plat, prix_unitaire, cout_preparation)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, rows)
        log.info(f"dim_plat : {len(rows)} lignes insérées/ignorées")

    conn.commit()
    cur.close()
    conn.close()
    log.info("Chargement des dimensions terminé.")

# ============================================================
#  ÉTAPE 6 — CHARGEMENT DE LA TABLE DE FAITS
# ============================================================

def charger_faits(**context):
    """
    Charge la table fait_traiteur dans le Data Warehouse.

    Pour chaque événement on :
      1. Résout les surrogate keys (SK) en faisant un SELECT sur chaque dim
      2. Insère la ligne de fait avec ces SKs
      3. Utilise ON CONFLICT (traiteur_code) DO UPDATE pour l'idempotence
    """
    ti = context['ti']
    donnees = ti.xcom_pull(key='donnees_transformees', task_ids='transformer')

    df_faits = pd.read_json(donnees['faits'])
    df_faits['date'] = pd.to_datetime(df_faits['date']).dt.date

    conn = psycopg2.connect(**DB_DWH)
    cur  = conn.cursor()

    # Charger les SKs des dimensions en mémoire pour jointure rapide
    cur.execute("SELECT client_sk, client_code FROM dim_client")
    map_client = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT lieu_sk, lieu_label FROM dim_lieu")
    map_lieu = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT date_sk, date_complete FROM dim_date")
    map_date = {str(row[1]): row[0] for row in cur.fetchall()}

    cur.execute("SELECT statut_sk, statut_label FROM dim_statut")
    map_statut = {row[1]: row[0] for row in cur.fetchall()}

    nb_inseres = 0
    nb_erreurs = 0

    for _, row in df_faits.iterrows():
        try:
            client_sk = map_client.get(row['code_client'])
            lieu_sk   = map_lieu.get(str(row['lieu']).strip())
            date_sk   = map_date.get(str(row['date']))
            statut_sk = map_statut.get('confirme')   # on ne charge que les confirmés

            if None in (client_sk, lieu_sk, date_sk, statut_sk):
                log.warning(
                    f"SK manquant pour {row['traiteur_code']} : "
                    f"client={client_sk}, lieu={lieu_sk}, date={date_sk}, statut={statut_sk}"
                )
                nb_erreurs += 1
                continue

            cur.execute("""
                INSERT INTO fait_traiteur (
                    client_sk, lieu_sk, date_sk, statut_sk, traiteur_code,
                    nb_pax, nb_employes, nb_plats, nb_materiels,
                    total_salaires, total_materiels, cout_preparation,
                    revenus_plats, marge_brute
                )
                VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s,%s)
                ON CONFLICT (traiteur_code) DO UPDATE SET
                    nb_pax           = EXCLUDED.nb_pax,
                    nb_employes      = EXCLUDED.nb_employes,
                    nb_plats         = EXCLUDED.nb_plats,
                    nb_materiels     = EXCLUDED.nb_materiels,
                    total_salaires   = EXCLUDED.total_salaires,
                    total_materiels  = EXCLUDED.total_materiels,
                    cout_preparation = EXCLUDED.cout_preparation,
                    revenus_plats    = EXCLUDED.revenus_plats,
                    marge_brute      = EXCLUDED.marge_brute,
                    date_chargement  = NOW()
            """, (
                client_sk, lieu_sk, date_sk, statut_sk, row['traiteur_code'],
                int(row['nb_pax']),
                int(row.get('nb_employes', 0)),
                int(row.get('nb_plats', 0)),
                int(row.get('nb_materiels', 0)),
                float(row.get('total_salaires', 0)),
                float(row.get('total_materiels', 0)),
                float(row.get('cout_preparation', 0)),
                float(row.get('revenus_plats', 0)),
                float(row.get('marge_brute', 0)),
            ))
            nb_inseres += 1

        except Exception as e:
            log.error(f"Erreur sur {row.get('traiteur_code', '?')} : {e}")
            nb_erreurs += 1

    conn.commit()
    cur.close()
    conn.close()
    log.info(f"Chargement faits terminé : {nb_inseres} lignes OK, {nb_erreurs} erreurs")

    if nb_erreurs > 0:
        raise ValueError(f"{nb_erreurs} lignes n'ont pas pu être chargées. Vérifiez les logs.")

# ============================================================
#  ÉTAPE 7 — RAPPORT FINAL
# ============================================================

def rapport_final(**context):
    """
    Se connecte au DWH et affiche un résumé dans les logs Airflow.
    Vous verrez ces chiffres dans l'interface web d'Airflow.
    """
    conn = psycopg2.connect(**DB_DWH)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fait_traiteur")
    nb_faits = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM dim_client")
    nb_clients = cur.fetchone()[0]

    cur.execute("SELECT SUM(revenus_plats), SUM(marge_brute) FROM fait_traiteur")
    revenus, marge = cur.fetchone()

    cur.execute("""
        SELECT dc.nom, dc.prenom, COUNT(*) AS nb_events, SUM(f.revenus_plats) AS ca
        FROM fait_traiteur f
        JOIN dim_client dc ON f.client_sk = dc.client_sk
        GROUP BY dc.nom, dc.prenom
        ORDER BY ca DESC
        LIMIT 5
    """)
    top_clients = cur.fetchall()

    cur.execute("""
        SELECT dd.nom_mois, COUNT(*) AS nb_events
        FROM fait_traiteur f
        JOIN dim_date dd ON f.date_sk = dd.date_sk
        GROUP BY dd.nom_mois, dd.mois
        ORDER BY dd.mois
    """)
    par_mois = cur.fetchall()

    conn.close()

    # Affichage dans les logs Airflow
    log.info("=" * 60)
    log.info("  RAPPORT ETL — Projet Traiteur")
    log.info("=" * 60)
    log.info(f"  Événements chargés  : {nb_faits}")
    log.info(f"  Clients distincts   : {nb_clients}")
    log.info(f"  Revenus totaux      : {revenus:,.0f} Ar" if revenus else "  Revenus : N/A")
    log.info(f"  Marge brute totale  : {marge:,.0f} Ar"   if marge   else "  Marge   : N/A")
    log.info("")
    log.info("  TOP 5 CLIENTS par CA :")
    for nom, prenom, nb, ca in top_clients:
        log.info(f"    {prenom} {nom} — {nb} événements — {ca:,.0f} Ar")
    log.info("")
    log.info("  ÉVÉNEMENTS PAR MOIS :")
    for mois, nb in par_mois:
        log.info(f"    {mois:<12} : {nb} événement(s)")
    log.info("=" * 60)

# ============================================================
#  DÉCLARATION DU DAG
# ============================================================

with DAG(
    dag_id          = 'etl_traiteur',
    default_args    = default_args,
    description     = 'Pipeline ETL complet — Projet Traiteur (cours DataWarehouse)',
    schedule_interval = '0 6 * * 1',   # Tous les lundis à 6h du matin
    start_date      = datetime(2024, 1, 1),
    catchup         = False,            # Ne pas rejouer les exécutions passées
    tags            = ['dwh', 'traiteur', 'etl'],
) as dag:

    # ── Tâche 1 : vérifier que les fichiers existent ──────────
    t1_verifier = PythonOperator(
        task_id         = 'verifier_sources',
        python_callable = verifier_sources,
    )

    # ── Tâche 2 : extraire depuis PostgreSQL (base Django) ────
    t2_extract_pg = PythonOperator(
        task_id         = 'extraire_postgres',
        python_callable = extraire_postgres,
    )

    # ── Tâche 3 : extraire depuis Excel + CSV ─────────────────
    t3_extract_fichiers = PythonOperator(
        task_id         = 'extraire_fichiers',
        python_callable = extraire_fichiers,
    )

    # ── Tâche 4 : transformer et calculer ─────────────────────
    t4_transformer = PythonOperator(
        task_id         = 'transformer',
        python_callable = transformer,
    )

    # ── Tâche 5 : charger les dimensions ──────────────────────
    t5_dim = PythonOperator(
        task_id         = 'charger_dimensions',
        python_callable = charger_dimensions,
    )

    # ── Tâche 6 : charger la table de faits ───────────────────
    t6_faits = PythonOperator(
        task_id         = 'charger_faits',
        python_callable = charger_faits,
    )

    # ── Tâche 7 : rapport final dans les logs ─────────────────
    t7_rapport = PythonOperator(
        task_id         = 'rapport_final',
        python_callable = rapport_final,
    )

    # ============================================================
    #  ENCHAÎNEMENT DES TÂCHES (ordre d'exécution)
    #
    #  t1 → t2 ─┐
    #            ├─→ t4 → t5 → t6 → t7
    #  t1 → t3 ─┘
    #
    #  t2 et t3 tournent EN PARALLÈLE après t1
    # ============================================================

    t1_verifier >> [t2_extract_pg, t3_extract_fichiers]
    [t2_extract_pg, t3_extract_fichiers] >> t4_transformer
    t4_transformer >> t5_dim >> t6_faits >> t7_rapport

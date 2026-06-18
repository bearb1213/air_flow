"""
Pipeline ETL Traiteur
=====================
Flux :
  verifier_sources
       │
  ┌────┴────┐   (parallèle)
  │         │
extraire_  extraire_
postgres   fichiers
  │         │
  └────┬────┘
       │
  transformer          ← nettoyage + calculs + préparation des dimensions
       │
charger_dimensions     ← dim_client, dim_lieu, dim_date, dim_plat, dim_statut
       │
 charger_faits         ← fait_traiteur (toutes les métriques)
       │
rapport_final          ← logs + email de succès (email d'erreur sur chaque échec)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.email import send_email

log = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
DATA_DIR = "/opt/airflow/data"          # volume Docker : airflow/data/ → /opt/airflow/data

CONN_SRC = "mysql_traiteur"             # Airflow connection : base source MySQL (traiteur)
CONN_DWH = "postgres_traiteur_dwh"     # Airflow connection : entrepôt     (traiteur_dwh)

REPORT_EMAILS = ["tandrifydylan@gmail.com"] # ← Modifier avec votre adresse email
# ──────────────────────────────────────────────────────────────────────────────


# ── Callback d'échec ──────────────────────────────────────────────────────────

def _failure_callback(context):
    dag_id  = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    exec_dt = context["execution_date"]
    error   = context.get("exception", "erreur inconnue")

    subject = f"[ERREUR] Pipeline ETL Traiteur — tâche '{task_id}' échouée"
    body = f"""
    <html><body style="font-family:Arial,sans-serif">
    <h2 style="color:#d9534f">Échec du pipeline ETL Traiteur</h2>
    <table cellpadding="8">
      <tr><td><b>DAG</b></td><td>{dag_id}</td></tr>
      <tr><td><b>Tâche</b></td><td>{task_id}</td></tr>
      <tr><td><b>Date</b></td><td>{exec_dt}</td></tr>
      <tr><td><b>Erreur</b></td><td><code>{error}</code></td></tr>
    </table>
    <p>Vérifiez les logs Airflow pour plus de détails.</p>
    </body></html>
    """
    try:
        send_email(to=REPORT_EMAILS, subject=subject, html_content=body)
    except Exception as exc:
        log.warning("Impossible d'envoyer l'email d'erreur : %s", exc)


# ── Tâche 1 : vérifier les fichiers sources ───────────────────────────────────

def verifier_sources(**_):
    required = [
        f"{DATA_DIR}/traiteur.xlsx",
        f"{DATA_DIR}/menu_traiteur.xlsx",
        f"{DATA_DIR}/equipe.csv",
        f"{DATA_DIR}/materiel_traiteur.csv",
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(f"Fichiers manquants dans {DATA_DIR} : {missing}")
    log.info("Tous les fichiers sources sont présents.")


# ── Tâche 2 : extraire depuis MySQL (source) ──────────────────────────────────

def extraire_mysql(**_):
    from airflow.providers.mysql.hooks.mysql import MySqlHook

    hook = MySqlHook(mysql_conn_id=CONN_SRC)

    clients = hook.get_pandas_df("SELECT * FROM clients")
    plats   = hook.get_pandas_df("""
        SELECT p.plat_code, p.label, p.type_code,
               pt.label AS type_label, p.cout_preparation, p.prix
        FROM plats p
        JOIN plat_types pt ON p.type_code = pt.type_code
    """)

    log.info("Extrait %d clients et %d plats depuis MySQL.", len(clients), len(plats))
    return {
        "clients": clients.to_json(orient="records"),
        "plats":   plats.to_json(orient="records"),
    }


# ── Tâche 3 : extraire depuis les fichiers (parallèle à t2) ──────────────────

def extraire_fichiers(**_):
    import pandas as pd

    traiteur  = pd.read_excel(f"{DATA_DIR}/traiteur.xlsx")
    menu      = pd.read_excel(f"{DATA_DIR}/menu_traiteur.xlsx")
    equipe    = pd.read_csv(f"{DATA_DIR}/equipe.csv",            sep=";")
    materiels = pd.read_csv(f"{DATA_DIR}/materiel_traiteur.csv", sep=";")

    log.info(
        "Extrait %d traiteurs, %d menus, %d équipes, %d matériels.",
        len(traiteur), len(menu), len(equipe), len(materiels),
    )
    return {
        "traiteur":  traiteur.to_json(orient="records", date_format="iso"),
        "menu":      menu.to_json(orient="records"),
        "equipe":    equipe.to_json(orient="records"),
        "materiels": materiels.to_json(orient="records"),
    }


# ── Tâche 4 : transformer ────────────────────────────────────────────────────

def transformer(**context):
    import pandas as pd

    ti   = context["ti"]
    pg   = ti.xcom_pull(task_ids="extraire_mysql")
    fils = ti.xcom_pull(task_ids="extraire_fichiers")

    clients  = pd.read_json(pg["clients"])
    plats    = pd.read_json(pg["plats"])
    traiteur = pd.read_json(fils["traiteur"])
    menu     = pd.read_json(fils["menu"])
    equipe   = pd.read_json(fils["equipe"])
    mats     = pd.read_json(fils["materiels"])

    # Nettoyage
    traiteur["date"] = pd.to_datetime(traiteur["date"])
    traiteur["lieu"] = traiteur["lieu"].str.strip().str.title()

    # Agrégation salaires
    sal = equipe.groupby("traiteur_code")["salaire"].sum().reset_index()
    sal.rename(columns={"salaire": "total_salaires"}, inplace=True)

    # Agrégation matériels
    mat = mats.groupby("traiteur_code")["prix"].sum().reset_index()
    mat.rename(columns={"prix": "total_materiels"}, inplace=True)

    # Coûts et revenus alimentaires (× nb_pax)
    mp = menu.merge(traiteur[["traiteur_code", "nb_pax"]], on="traiteur_code", how="left")
    mp["cout_ligne"]   = mp["cout_preparation"] * mp["nb_pax"]
    mp["revenu_ligne"] = mp["prix"]             * mp["nb_pax"]
    food = mp.groupby("traiteur_code").agg(
        cout_preparation=("cout_ligne",   "sum"),
        revenus_plats   =("revenu_ligne", "sum"),
    ).reset_index()

    # Table de faits intermédiaire
    facts = (traiteur
             .merge(sal,  on="traiteur_code", how="left")
             .merge(mat,  on="traiteur_code", how="left")
             .merge(food, on="traiteur_code", how="left"))

    for col in ["total_salaires", "total_materiels", "cout_preparation", "revenus_plats"]:
        facts[col] = facts[col].fillna(0)

    facts["marge_brute"] = (
        facts["revenus_plats"]
        - facts["cout_preparation"]
        - facts["total_salaires"]
        - facts["total_materiels"]
    )

    # Sérialiser les dates en ISO pour survivre au round-trip JSON
    facts["date"] = facts["date"].dt.strftime("%Y-%m-%d")

    # Données pour les dimensions
    dates = traiteur[["date"]].drop_duplicates().copy()
    dates["date_complete"] = dates["date"].dt.strftime("%Y-%m-%d")
    dates["annee"]         = dates["date"].dt.year
    dates["trimestre"]     = dates["date"].dt.quarter
    dates["mois"]          = dates["date"].dt.month
    dates["nom_mois"]      = dates["date"].dt.strftime("%B")
    dates["jour_semaine"]  = dates["date"].dt.strftime("%A")

    lieux   = traiteur[["lieu"]].drop_duplicates()
    statuts = (traiteur[["status"]].drop_duplicates()
                                   .rename(columns={"status": "statut"}))

    log.info("Transformation terminée : %d événements traités.", len(facts))
    return {
        "facts":   facts.to_json(orient="records"),
        "clients": clients.to_json(orient="records"),
        "plats":   plats.to_json(orient="records"),
        "lieux":   lieux.to_json(orient="records"),
        "statuts": statuts.to_json(orient="records"),
        "dates":   dates.drop(columns="date").to_json(orient="records"),
    }


# ── Tâche 5 : charger les dimensions ─────────────────────────────────────────

def charger_dimensions(**context):
    import pandas as pd
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from psycopg2.extras import execute_values

    ti   = context["ti"]
    data = ti.xcom_pull(task_ids="transformer")

    clients = pd.read_json(data["clients"])
    plats   = pd.read_json(data["plats"])
    lieux   = pd.read_json(data["lieux"])
    statuts = pd.read_json(data["statuts"])
    dates   = pd.read_json(data["dates"])

    hook = PostgresHook(postgres_conn_id=CONN_DWH)
    conn = hook.get_conn()
    cur  = conn.cursor()

    execute_values(cur, """
        INSERT INTO dim_client (client_code, nom, prenom, email, telephone)
        VALUES %s
        ON CONFLICT (client_code) DO UPDATE SET
            nom = EXCLUDED.nom, prenom = EXCLUDED.prenom,
            email = EXCLUDED.email, telephone = EXCLUDED.telephone
    """, [(r.client_code, r.nom, r.prenom, r.email, r.telephone)
          for _, r in clients.iterrows()])

    execute_values(cur, """
        INSERT INTO dim_lieu (lieu) VALUES %s
        ON CONFLICT (lieu) DO NOTHING
    """, [(r.lieu,) for _, r in lieux.iterrows()])

    execute_values(cur, """
        INSERT INTO dim_statut (statut) VALUES %s
        ON CONFLICT (statut) DO NOTHING
    """, [(r.statut,) for _, r in statuts.iterrows()])

    execute_values(cur, """
        INSERT INTO dim_date (date_complete, annee, trimestre, mois, nom_mois, jour_semaine)
        VALUES %s
        ON CONFLICT (date_complete) DO NOTHING
    """, [
        (r.date_complete, int(r.annee), int(r.trimestre), int(r.mois), r.nom_mois, r.jour_semaine)
        for _, r in dates.iterrows()
    ])

    execute_values(cur, """
        INSERT INTO dim_plat (plat_code, label, type_code, type_label, cout_preparation, prix)
        VALUES %s
        ON CONFLICT (plat_code) DO UPDATE SET
            label = EXCLUDED.label, type_code = EXCLUDED.type_code,
            type_label = EXCLUDED.type_label,
            cout_preparation = EXCLUDED.cout_preparation, prix = EXCLUDED.prix
    """, [
        (r.plat_code, r.label, r.type_code, r.type_label, r.cout_preparation, r.prix)
        for _, r in plats.iterrows()
    ])

    conn.commit()
    cur.close()
    conn.close()
    log.info("Dimensions chargées avec succès.")


# ── Tâche 6 : charger la table de faits ──────────────────────────────────────

def charger_faits(**context):
    import pandas as pd
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from psycopg2.extras import execute_values

    ti    = context["ti"]
    data  = ti.xcom_pull(task_ids="transformer")
    facts = pd.read_json(data["facts"])

    hook = PostgresHook(postgres_conn_id=CONN_DWH)
    conn = hook.get_conn()
    cur  = conn.cursor()

    cur.execute("SELECT client_key, client_code FROM dim_client")
    client_map = {r[1]: r[0] for r in cur.fetchall()}

    cur.execute("SELECT lieu_key, lieu FROM dim_lieu")
    lieu_map = {r[1]: r[0] for r in cur.fetchall()}

    cur.execute("SELECT statut_key, statut FROM dim_statut")
    statut_map = {r[1]: r[0] for r in cur.fetchall()}

    cur.execute("SELECT date_key, date_complete::text FROM dim_date")
    date_map = {r[1]: r[0] for r in cur.fetchall()}

    rows = [
        (
            r["traiteur_code"],
            client_map.get(r["client_code"]),
            lieu_map.get(r["lieu"]),
            date_map.get(r["date"]),
            statut_map.get(r["status"]),
            int(r["nb_pax"]),
            float(r["total_salaires"]),
            float(r["total_materiels"]),
            float(r["cout_preparation"]),
            float(r["revenus_plats"]),
            float(r["marge_brute"]),
        )
        for _, r in facts.iterrows()
    ]

    execute_values(cur, """
        INSERT INTO fait_traiteur (
            traiteur_code, client_key, lieu_key, date_key, statut_key,
            nb_pax, total_salaires, total_materiels,
            cout_preparation, revenus_plats, marge_brute
        )
        VALUES %s
        ON CONFLICT (traiteur_code) DO UPDATE SET
            client_key       = EXCLUDED.client_key,
            lieu_key         = EXCLUDED.lieu_key,
            date_key         = EXCLUDED.date_key,
            statut_key       = EXCLUDED.statut_key,
            nb_pax           = EXCLUDED.nb_pax,
            total_salaires   = EXCLUDED.total_salaires,
            total_materiels  = EXCLUDED.total_materiels,
            cout_preparation = EXCLUDED.cout_preparation,
            revenus_plats    = EXCLUDED.revenus_plats,
            marge_brute      = EXCLUDED.marge_brute,
            charge_au        = CURRENT_TIMESTAMP
    """, rows)

    conn.commit()
    cur.close()
    conn.close()
    log.info("Table de faits chargée : %d lignes.", len(rows))


# ── Tâche 7 : rapport final + email de succès ─────────────────────────────────

def rapport_final(**context):
    import pandas as pd

    ti    = context["ti"]
    data  = ti.xcom_pull(task_ids="transformer")
    facts = pd.read_json(data["facts"])

    confirmes   = facts[facts["status"] == "confirme"]
    total_ca    = float(confirmes["revenus_plats"].sum())
    total_marge = float(confirmes["marge_brute"].sum())
    nb_events   = int(len(confirmes))
    taux_marge  = (total_marge / total_ca * 100) if total_ca else 0

    top5 = (
        confirmes.groupby("client_code")["revenus_plats"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    log.info("=== RAPPORT ETL TRAITEUR ===")
    log.info("Événements confirmés : %d", nb_events)
    log.info("CA total             : %s Ar", f"{total_ca:,.0f}")
    log.info("Marge brute totale   : %s Ar", f"{total_marge:,.0f}")
    log.info("Taux de marge        : %.1f%%", taux_marge)

    exec_dt     = context["execution_date"]
    top5_rows   = "".join(
        f"<tr><td>{code}</td><td style='text-align:right'>{ca:,.0f} Ar</td></tr>"
        for code, ca in top5.items()
    )
    statut_agg  = facts.groupby("status").size().reset_index(name="count")
    statut_rows = "".join(
        f"<tr><td>{r['status']}</td><td>{r['count']}</td></tr>"
        for _, r in statut_agg.iterrows()
    )

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
    <h2 style="color:#2c7be5">Rapport ETL Traiteur — {exec_dt.strftime('%d/%m/%Y')}</h2>
    <p>Le pipeline ETL s'est terminé avec <b style="color:green">succès</b>.</p>

    <h3>Résumé global</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
      <tr style="background:#f0f4ff"><th>Métrique</th><th>Valeur</th></tr>
      <tr><td>Événements confirmés</td><td>{nb_events}</td></tr>
      <tr><td>Chiffre d'affaires</td><td>{total_ca:,.0f} Ar</td></tr>
      <tr><td>Marge brute</td><td>{total_marge:,.0f} Ar</td></tr>
      <tr><td>Taux de marge</td><td>{taux_marge:.1f} %</td></tr>
    </table>

    <h3>Répartition par statut</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
      <tr style="background:#f0f4ff"><th>Statut</th><th>Nombre</th></tr>
      {statut_rows}
    </table>

    <h3>Top 5 clients (CA)</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
      <tr style="background:#f0f4ff"><th>Client</th><th>CA</th></tr>
      {top5_rows}
    </table>

    <p style="color:#aaa;font-size:11px">
      Généré automatiquement par Apache Airflow — DAG <code>etl_traiteur</code>
    </p>
    </body></html>
    """

    subject = f"[OK] Rapport ETL Traiteur — {exec_dt.strftime('%d/%m/%Y')}"
    try:
        send_email(to=REPORT_EMAILS, subject=subject, html_content=html)
        log.info("Rapport email envoyé à %s", REPORT_EMAILS)
    except Exception as exc:
        log.warning("Impossible d'envoyer l'email de rapport : %s", exc)


# ── Définition du DAG ─────────────────────────────────────────────────────────

default_args = {
    "owner":               "airflow",
    "depends_on_past":     False,
    "retries":             1,
    "retry_delay":         timedelta(minutes=5),
    "email_on_failure":    False,
    "email_on_retry":      False,
    "on_failure_callback": _failure_callback,
}

with DAG(
    dag_id="etl_traiteur",
    default_args=default_args,
    description="ETL Traiteur : Excel + MySQL → Data Warehouse PostgreSQL + rapport email",
    schedule_interval="0 0 1 * *",   # 1er de chaque mois a minuit
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["traiteur", "etl", "dwh"],
) as dag:

    t_verif  = PythonOperator(task_id="verifier_sources",   python_callable=verifier_sources)
    t_mysql  = PythonOperator(task_id="extraire_mysql",     python_callable=extraire_mysql)
    t_files  = PythonOperator(task_id="extraire_fichiers",  python_callable=extraire_fichiers)
    t_trans  = PythonOperator(task_id="transformer",        python_callable=transformer)
    t_dims   = PythonOperator(task_id="charger_dimensions", python_callable=charger_dimensions)
    t_facts  = PythonOperator(task_id="charger_faits",      python_callable=charger_faits)
    t_report = PythonOperator(task_id="rapport_final",      python_callable=rapport_final)

    t_verif >> [t_mysql, t_files] >> t_trans >> t_dims >> t_facts >> t_report
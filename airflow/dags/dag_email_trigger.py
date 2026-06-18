"""
DAG declenchement par email du patron
======================================
Ce DAG surveille la boite email toutes les 15 minutes.
Quand un email non lu du patron (BOSS_EMAIL) arrive avec un sujet
contenant un mot-cle ("etl", "lancer", "pipeline", "rapport"),
il declenche automatiquement le pipeline etl_traiteur.

Les 3 modes de declenchement disponibles :
  1. Automatique  : 1er du mois a minuit (schedule_interval dans etl_traiteur)
  2. Bouton       : "Trigger DAG" dans l'UI Airflow -> etl_traiteur
  3. Email patron : ce DAG detecte l'email et declenche etl_traiteur
"""

from __future__ import annotations

import email as email_lib
import imaplib
import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import ShortCircuitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

log = logging.getLogger(__name__)

# ── Configuration IMAP ────────────────────────────────────────────────────────
# Renseigner ces valeurs dans airflow/.env
IMAP_HOST     = os.getenv("IMAP_HOST",     "imap.gmail.com")
IMAP_PORT     = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER     = os.getenv("IMAP_USER",     "ton_email@gmail.com")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
BOSS_EMAIL    = os.getenv("BOSS_EMAIL",    "boss@example.com")

# Mots-cles dans le sujet de l'email qui declenchent le pipeline
TRIGGER_KEYWORDS = ["etl", "lancer", "pipeline", "rapport", "run"]
# ─────────────────────────────────────────────────────────────────────────────


def _decode_subject(raw_subject: str) -> str:
    parts = email_lib.header.decode_header(raw_subject or "")
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def chercher_email_patron(**_) -> bool:
    """
    Cherche un email non lu du patron contenant un mot-cle declencheur.
    Marque l'email comme lu pour eviter les doubles declenchements.
    Retourne True si un email declencheur est trouve, False sinon.
    ShortCircuitOperator utilise ce retour pour passer ou court-circuiter la suite.
    """
    if not IMAP_PASSWORD:
        log.warning("IMAP_PASSWORD non configure dans .env — surveillance email desactivee.")
        return False

    try:
        conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        conn.login(IMAP_USER, IMAP_PASSWORD)
        conn.select("INBOX")

        # Chercher emails non lus venant du patron
        _, msg_ids = conn.search(None, f'(UNSEEN FROM "{BOSS_EMAIL}")')
        msg_ids = [m for m in msg_ids[0].split() if m]

        if not msg_ids:
            log.info("Aucun email non lu du patron (%s).", BOSS_EMAIL)
            conn.logout()
            return False

        for msg_id in msg_ids:
            _, data = conn.fetch(msg_id, "(RFC822)")
            msg     = email_lib.message_from_bytes(data[0][1])
            subject = _decode_subject(msg.get("Subject", "")).lower()

            if any(kw in subject for kw in TRIGGER_KEYWORDS):
                log.info("Email declencheur detecte — sujet : '%s'", subject)
                # Marquer comme lu pour ne pas declencher deux fois
                conn.store(msg_id, "+FLAGS", "\\Seen")
                conn.logout()
                return True

        conn.logout()
        log.info("%d email(s) du patron trouves mais aucun mot-cle declencheur.", len(msg_ids))
        return False

    except imaplib.IMAP4.error as exc:
        log.error("Erreur IMAP (identifiants ?) : %s", exc)
        return False
    except Exception as exc:
        log.error("Erreur inattendue lors de la verification email : %s", exc)
        return False


# ── DAG ───────────────────────────────────────────────────────────────────────

default_args = {
    "owner":            "airflow",
    "depends_on_past":  False,
    "retries":          0,
    "email_on_failure": False,
}

with DAG(
    dag_id="email_trigger_etl",
    default_args=default_args,
    description="Surveille la boite email et declenche etl_traiteur si email du patron detecte",
    schedule_interval="*/15 * * * *",   # verification toutes les 15 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["traiteur", "trigger", "email"],
    max_active_runs=1,  # une seule verification a la fois
) as dag:

    t_check = ShortCircuitOperator(
        task_id="chercher_email_patron",
        python_callable=chercher_email_patron,
    )

    t_trigger = TriggerDagRunOperator(
        task_id="declencher_etl_traiteur",
        trigger_dag_id="etl_traiteur",
        wait_for_completion=False,      # ne pas bloquer, lancer et continuer
        reset_dag_run=False,
    )

    t_check >> t_trigger
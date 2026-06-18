-- =============================================================
--  Schema Data Warehouse — Traiteur
--  Base cible : traiteur_dwh
--
--  Création :
--    CREATE DATABASE traiteur_dwh;
--    \c traiteur_dwh
--    \i sql/create_dwh_schema.sql
-- =============================================================

-- ── Dimensions ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_client (
    client_key  SERIAL       PRIMARY KEY,
    client_code VARCHAR(50)  UNIQUE NOT NULL,
    nom         VARCHAR(255),
    prenom      VARCHAR(255),
    email       VARCHAR(255),
    telephone   VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_lieu (
    lieu_key SERIAL       PRIMARY KEY,
    lieu     VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key      SERIAL   PRIMARY KEY,
    date_complete DATE     UNIQUE NOT NULL,
    annee         SMALLINT,
    trimestre     SMALLINT,
    mois          SMALLINT,
    nom_mois      VARCHAR(20),
    jour_semaine  VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_plat (
    plat_key         SERIAL      PRIMARY KEY,
    plat_code        VARCHAR(50) UNIQUE NOT NULL,
    label            VARCHAR(255),
    type_code        VARCHAR(50),
    type_label       VARCHAR(100),
    cout_preparation DECIMAL(10,2),
    prix             DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS dim_statut (
    statut_key SERIAL      PRIMARY KEY,
    statut     VARCHAR(50) UNIQUE NOT NULL
);

-- ── Fait ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fait_traiteur (
    traiteur_code    VARCHAR(50) PRIMARY KEY,
    client_key       INTEGER REFERENCES dim_client(client_key),
    lieu_key         INTEGER REFERENCES dim_lieu(lieu_key),
    date_key         INTEGER REFERENCES dim_date(date_key),
    statut_key       INTEGER REFERENCES dim_statut(statut_key),
    nb_pax           INTEGER,
    total_salaires   DECIMAL(14,2) DEFAULT 0,
    total_materiels  DECIMAL(14,2) DEFAULT 0,
    cout_preparation DECIMAL(14,2) DEFAULT 0,
    revenus_plats    DECIMAL(14,2) DEFAULT 0,
    marge_brute      DECIMAL(14,2) DEFAULT 0,
    charge_au        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
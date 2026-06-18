-- ============================================================
--  SCHÉMA DATA WAREHOUSE — Projet Traiteur
--  Schéma en étoile : 1 table de faits + 5 dimensions
--  Exécuter dans la base PostgreSQL : traiteur_dwh
-- ============================================================

-- Créer la base si elle n'existe pas encore (à lancer manuellement)
-- CREATE DATABASE traiteur_dwh;

-- ============================================================
--  DIMENSIONS
-- ============================================================

-- Dimension Client
CREATE TABLE IF NOT EXISTS dim_client (
    client_sk       SERIAL PRIMARY KEY,          -- surrogate key (clé DWH)
    client_code     VARCHAR(20) NOT NULL,         -- clé métier d'origine
    nom             VARCHAR(100),
    prenom          VARCHAR(100),
    email           VARCHAR(150),
    telephone       VARCHAR(30),
    date_chargement TIMESTAMP DEFAULT NOW()
);

-- Dimension Lieu (lieu de l'événement)
CREATE TABLE IF NOT EXISTS dim_lieu (
    lieu_sk         SERIAL PRIMARY KEY,
    lieu_label      VARCHAR(200) NOT NULL UNIQUE,
    date_chargement TIMESTAMP DEFAULT NOW()
);

-- Dimension Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_sk         SERIAL PRIMARY KEY,
    date_complete   DATE NOT NULL UNIQUE,
    annee           INT,
    mois            INT,
    nom_mois        VARCHAR(20),
    trimestre       INT,
    jour_semaine    VARCHAR(15),
    date_chargement TIMESTAMP DEFAULT NOW()
);

-- Dimension Plat (plats proposés dans les menus)
CREATE TABLE IF NOT EXISTS dim_plat (
    plat_sk         SERIAL PRIMARY KEY,
    plat_code       VARCHAR(20) NOT NULL,
    label           VARCHAR(200),
    type_plat       VARCHAR(50),
    prix_unitaire   NUMERIC(12,2),
    cout_preparation NUMERIC(12,2),
    date_chargement TIMESTAMP DEFAULT NOW()
);

-- Dimension Statut (statut de l'événement)
CREATE TABLE IF NOT EXISTS dim_statut (
    statut_sk       SERIAL PRIMARY KEY,
    statut_label    VARCHAR(50) NOT NULL UNIQUE,  -- confirme / annule / en attente
    date_chargement TIMESTAMP DEFAULT NOW()
);

-- ============================================================
--  TABLE DE FAITS
-- ============================================================

CREATE TABLE IF NOT EXISTS fait_traiteur (
    fait_sk             SERIAL PRIMARY KEY,

    -- Clés étrangères vers dimensions
    client_sk           INT REFERENCES dim_client(client_sk),
    lieu_sk             INT REFERENCES dim_lieu(lieu_sk),
    date_sk             INT REFERENCES dim_date(date_sk),
    statut_sk           INT REFERENCES dim_statut(statut_sk),

    -- Clés métier (pour traçabilité)
    traiteur_code       VARCHAR(20),

    -- Mesures / métriques
    nb_pax              INT,                       -- nombre de convives
    nb_employes         INT,                       -- employés mobilisés
    nb_plats            INT,                       -- nombre de plats au menu
    nb_materiels        INT,                       -- matériels utilisés

    total_salaires      NUMERIC(14,2),             -- somme des salaires employés
    total_materiels     NUMERIC(14,2),             -- somme coût matériels
    cout_preparation    NUMERIC(14,2),             -- somme coût prépa des plats × pax
    revenus_plats       NUMERIC(14,2),             -- prix vente des plats × pax
    marge_brute         NUMERIC(14,2),             -- revenus - coûts totaux

    date_chargement     TIMESTAMP DEFAULT NOW()
);

-- ============================================================
--  INDEX pour accélérer les analyses
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fait_client  ON fait_traiteur(client_sk);
CREATE INDEX IF NOT EXISTS idx_fait_date    ON fait_traiteur(date_sk);
CREATE INDEX IF NOT EXISTS idx_fait_statut  ON fait_traiteur(statut_sk);
CREATE INDEX IF NOT EXISTS idx_fait_code    ON fait_traiteur(traiteur_code);

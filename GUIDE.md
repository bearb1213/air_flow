# Guide du Pipeline ETL Traiteur — Apache Airflow

---

## Ce que fait le projet

Ce projet est un **pipeline ETL automatisé** pour une entreprise de traiteur.  
Il extrait les données de deux sources, les transforme, les charge dans un entrepôt de données, puis envoie un rapport par email.

```
Sources                     Transformation              Destination
──────                      ──────────────              ───────────
MySQL (traiteur)   ──┐                              ┌── PostgreSQL (traiteur_dwh)
                     ├──► transformer ──────────────┤      dim_client
Excel / CSV        ──┘                              │      dim_lieu
  traiteur.xlsx                                     │      dim_date
  menu_traiteur.xlsx     calculs :                  │      dim_plat
  equipe.csv             • total salaires           │      dim_statut
  materiel_traiteur.csv  • total materiels          │      fait_traiteur
                         • revenus plats × pax      └── + Email de rapport
                         • marge brute
```

---

## Architecture des fichiers

```
air_flow/
├── airflow/
│   ├── dags/
│   │   ├── dag_traiteur_etl.py      ← Pipeline principal (7 taches)
│   │   └── dag_email_trigger.py     ← Surveillance email patron
│   ├── data/                        ← Fichiers Excel/CSV a placer ici
│   │   ├── traiteur.xlsx
│   │   ├── menu_traiteur.xlsx
│   │   ├── equipe.csv
│   │   └── materiel_traiteur.csv
│   ├── logs/                        ← Logs generes automatiquement
│   ├── plugins/
│   ├── docker-compose.yml
│   └── .env                         ← Vos identifiants (a configurer)
│
├── sql/
│   ├── table.sql                    ← Schema base source (traiteur)
│   └── create_dwh_schema.sql        ← Schema entrepot (traiteur_dwh)
│
├── data/
│   ├── traiteur.xlsx
│   └── menu_traiteur.xlsx
│
├── create_csv.py                    ← Genere equipe.csv et materiel_traiteur.csv
└── GUIDE.md                         ← Ce fichier
```

---

## Prerequis

| Outil | Version | Verification |
|-------|---------|--------------|
| Docker Desktop | n'importe | `docker --version` |
| PostgreSQL | 14+ | doit tourner sur le port 5432 |
| MySQL | 8+ | doit tourner sur le port 3306 |
| Python | 3.10+ | `python --version` |

---

## Etape 1 — Preparer les bases de donnees

### 1a. Base source MySQL (`traiteur`)

Dans MySQL Workbench ou le terminal MySQL :

```sql
CREATE DATABASE traiteur;
USE traiteur;
-- Puis charger le schema et les donnees (tables employes, clients, plats, etc.)
-- SOURCE sql/table.sql;
```

> Le fichier `sql/table.sql` contient toutes les tables avec 200+ enregistrements de test.

### 1b. Base entrepot PostgreSQL (`traiteur_dwh`)

Dans pgAdmin ou psql :

```sql
CREATE DATABASE airflow;      -- base de metadonnees Airflow (obligatoire)
CREATE DATABASE traiteur_dwh; -- votre entrepot de donnees
```

Puis dans `traiteur_dwh`, executer le schema de l'entrepot :

```sql
-- Dans pgAdmin : Tools > Query Tool, selectionner la base traiteur_dwh, puis :
\i sql/create_dwh_schema.sql
```

Cela cree les tables :
- `dim_client`, `dim_lieu`, `dim_date`, `dim_plat`, `dim_statut`
- `fait_traiteur` (table de faits avec toutes les metriques)

---

## Etape 2 — Generer les fichiers CSV

```bash
cd air_flow
python create_csv.py
```

Cela genere dans `sql/` :
- `equipe.csv` — employes par evenement (poste, salaire, heures)
- `materiel_traiteur.csv` — materiels loues par evenement

### Copier les fichiers dans le bon dossier

```bash
# Windows PowerShell
Copy-Item data\traiteur.xlsx         airflow\data\
Copy-Item data\menu_traiteur.xlsx    airflow\data\
Copy-Item sql\equipe.csv             airflow\data\
Copy-Item sql\materiel_traiteur.csv  airflow\data\
```

---

## Etape 3 — Configurer le fichier `.env`

Ouvrir `airflow/.env` et remplir :

```env
AIRFLOW_UID=50000

# MySQL source (base traiteur)
MYSQL_USER=root              # votre utilisateur MySQL
MYSQL_PASSWORD=root          # votre mot de passe MySQL
MYSQL_PORT=3306

# Email SMTP (pour envoyer les rapports)
SMTP_USER=votre_email@gmail.com
SMTP_PASSWORD=               # App Password Gmail (voir ci-dessous)

# Email IMAP (pour surveiller la boite et detecter l'email du patron)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
BOSS_EMAIL=email_du_patron@exemple.com
```

### Obtenir un App Password Gmail

> Necessaire pour que Airflow puisse envoyer et lire des emails via Gmail.

1. Aller sur [myaccount.google.com/security](https://myaccount.google.com/security)
2. Activer la **Verification en 2 etapes**
3. Aller sur [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Creer un mot de passe pour "Mail" → copier les 16 caracteres
5. Coller dans `SMTP_PASSWORD=` et `IMAP_PASSWORD=` dans `.env`

---

## Etape 4 — Configurer l'adresse email dans le DAG

Ouvrir `airflow/dags/dag_traiteur_etl.py`, ligne 41 :

```python
REPORT_EMAILS = ["votre_email@gmail.com"]  # ← mettre votre adresse ici
```

---

## Etape 5 — Lancer Airflow

Depuis le dossier `airflow/` :

```bash
cd airflow

# Premiere fois seulement : initialiser la base de metadonnees
docker compose up airflow-init
# Attendre que le conteneur se termine avec "exited with code 0"

# Lancer tous les services
docker compose up -d
```

Verifier que tout tourne :

```bash
docker compose ps
```

Vous devez voir 3 conteneurs `running` :
- `airflow_webserver`
- `airflow_scheduler`
- `airflow_triggerer`

---

## Etape 6 — Acceder a l'interface

Ouvrir dans le navigateur : **http://localhost:8080**

| Champ | Valeur |
|-------|--------|
| Login | `admin` |
| Mot de passe | `admin` |

---

## Les 3 modes de declenchement

### Mode 1 — Automatique (1er du mois)

Le pipeline `etl_traiteur` se lance **automatiquement le 1er de chaque mois a minuit**.  
Aucune action requise — le scheduler Airflow s'en charge.

### Mode 2 — Bouton manuel

1. Dans l'interface Airflow, cliquer sur le DAG **`etl_traiteur`**
2. Cliquer sur le bouton **▶ Trigger DAG** (en haut a droite)
3. Le pipeline demarre immediatement

![Trigger button](https://airflow.apache.org/docs/apache-airflow/stable/_images/trigger_dag_run.png)

### Mode 3 — Email du patron

1. Le DAG **`email_trigger_etl`** surveille votre boite email toutes les **15 minutes**
2. Quand le patron envoie un email avec un mot-cle dans l'objet :
   - `etl`, `lancer`, `pipeline`, `rapport`, ou `run`
3. Airflow detecte l'email, le marque comme lu, et lance automatiquement `etl_traiteur`

**Exemple d'email du patron :**
```
De    : patron@entreprise.com
Objet : Lancer le rapport ETL de ce mois
```
→ Pipeline se declenche dans les 15 minutes.

---

## Ce que fait le pipeline etape par etape

```
verifier_sources
      │
      ├──────────────────────────────────────────────────┐
      │                                                  │
 extraire_mysql                                  extraire_fichiers
 (parallele)                                     (parallele)
      │                                                  │
      │  Lit depuis MySQL :                              │  Lit les fichiers :
      │  • clients (20 clients)                          │  • traiteur.xlsx
      │  • plats + plat_types (28 plats)                 │  • menu_traiteur.xlsx
      │                                                  │  • equipe.csv
      │                                                  │  • materiel_traiteur.csv
      │                                                  │
      └──────────────────────────────────────────────────┘
                              │
                         transformer
                              │
                Fusionne toutes les donnees et calcule :
                • total_salaires  = somme des salaires par evenement
                • total_materiels = somme des couts de location
                • cout_preparation = cout_plat × nb_pax (par evenement)
                • revenus_plats    = prix_plat × nb_pax (par evenement)
                • marge_brute      = revenus - couts - salaires - materiels
                              │
                    charger_dimensions
                              │
                Charge en PostgreSQL (traiteur_dwh) :
                • dim_client  (20 clients)
                • dim_lieu    (lieux des evenements)
                • dim_date    (dates avec annee/mois/trimestre)
                • dim_plat    (28 plats avec types)
                • dim_statut  (confirme / annule / en attente)
                              │
                      charger_faits
                              │
                Charge la table fait_traiteur :
                • 56 evenements avec toutes les metriques
                • ON CONFLICT DO UPDATE (idempotent : relancable sans doublon)
                              │
                     rapport_final
                              │
                Envoie un email HTML avec :
                • Nombre d'evenements confirmes
                • Chiffre d'affaires total
                • Marge brute et taux de marge
                • Repartition par statut
                • Top 5 clients par CA
```

---

## Verifier les resultats

### Dans l'interface Airflow

1. Cliquer sur le DAG `etl_traiteur`
2. Cliquer sur la derniere execution (cercle vert = succes)
3. Cliquer sur une tache pour voir ses logs detailles

### Dans PostgreSQL (pgAdmin)

Se connecter a la base `traiteur_dwh` et executer :

```sql
-- Verifier les faits charges
SELECT COUNT(*) FROM fait_traiteur;  -- doit retourner 56

-- CA et marge des evenements confirmes
SELECT
    SUM(revenus_plats)    AS chiffre_affaires,
    SUM(marge_brute)      AS marge_totale,
    ROUND(SUM(marge_brute) / SUM(revenus_plats) * 100, 1) AS taux_marge_pct
FROM fait_traiteur f
JOIN dim_statut s ON f.statut_key = s.statut_key
WHERE s.statut = 'confirme';

-- Top 5 clients
SELECT
    c.nom, c.prenom,
    SUM(f.revenus_plats) AS ca
FROM fait_traiteur f
JOIN dim_client c ON f.client_key = c.client_key
JOIN dim_statut s ON f.statut_key = s.statut_key
WHERE s.statut = 'confirme'
GROUP BY c.client_key, c.nom, c.prenom
ORDER BY ca DESC
LIMIT 5;
```

### Email recu

Apres chaque execution reussie, vous recevez un email comme celui-ci :

```
Objet : [OK] Rapport ETL Traiteur — 01/06/2024

Rapport ETL Traiteur — 01/06/2024
Le pipeline ETL s'est termine avec succes.

Resume global
─────────────────────────────────
Evenements confirmes    : 32
Chiffre d'affaires      : 48 320 000 Ar
Marge brute             : 12 150 000 Ar
Taux de marge           : 25.1 %

Top 5 clients (CA)
─────────────────────────────────
CLI005   4 200 000 Ar
CLI012   3 850 000 Ar
...
```

En cas d'erreur, vous recevez immediatement :

```
Objet : [ERREUR] Pipeline ETL Traiteur — tache 'extraire_mysql' echouee
```

---

## Arreter Airflow

```bash
cd airflow
docker compose down
```

Pour supprimer aussi les logs et les donnees :

```bash
docker compose down -v
```

---

## Commandes utiles

```bash
# Voir les logs en temps reel
docker compose logs -f airflow-scheduler

# Tester une seule tache sans lancer tout le pipeline
docker exec airflow_scheduler airflow tasks test etl_traiteur verifier_sources 2024-01-01

# Lister les DAGs disponibles
docker exec airflow_scheduler airflow dags list

# Declencher le pipeline manuellement depuis le terminal
docker exec airflow_scheduler airflow dags trigger etl_traiteur

# Voir l'etat du dernier run
docker exec airflow_scheduler airflow dags list-runs -d etl_traiteur
```

---

## Problemes courants

| Erreur | Cause probable | Solution |
|--------|---------------|----------|
| `airflow-init` echoue | La base `airflow` n'existe pas dans PostgreSQL | `CREATE DATABASE airflow;` dans pgAdmin |
| `extraire_mysql` echoue | MySQL inaccessible ou credentials incorrects | Verifier `MYSQL_USER`/`MYSQL_PASSWORD` dans `.env` |
| `charger_faits` echoue | La base `traiteur_dwh` n'existe pas | `CREATE DATABASE traiteur_dwh;` puis executer `create_dwh_schema.sql` |
| Email non envoye | App Password manquant ou incorrect | Regener un App Password sur `myaccount.google.com/apppasswords` |
| DAG n'apparait pas dans l'UI | Erreur de syntaxe Python dans le DAG | `docker compose logs airflow-scheduler` pour voir l'erreur |
| `email_trigger_etl` ne declenche pas | `BOSS_EMAIL` incorrect ou `IMAP_PASSWORD` vide | Verifier `.env` et relancer `docker compose up -d` |
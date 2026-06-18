# Projet Traiteur — Pipeline ETL avec Apache Airflow
## Cours : DataWarehouse

---

## Structure du projet

```
traiteur_airflow/
│
├── install_airflow.sh          ← Script d'installation (lancer 1 fois)
│
├── dags/
│   └── dag_traiteur_etl.py     ← Le DAG Airflow (votre pipeline ETL)
│
├── sql/
│   └── create_dwh_schema.sql   ← Schéma du Data Warehouse à créer
│
├── data/                       ← Copiez vos fichiers ici
│   ├── traiteur.xlsx
│   ├── menu_traiteur.xlsx
│   ├── equipe.csv
│   └── materiel_traiteur.csv
│
└── README.md                   ← Ce fichier
```

---

## Étape 1 — Créer la base Data Warehouse

Ouvrez pgAdmin ou psql et exécutez :

```sql
CREATE DATABASE traiteur_dwh;
```

Puis connectez-vous à `traiteur_dwh` et exécutez le fichier :
```
sql/create_dwh_schema.sql
```

---

## Étape 2 — Copier vos fichiers de données

```bash
cp /chemin/vers/traiteur.xlsx           data/
cp /chemin/vers/menu_traiteur.xlsx      data/
cp /chemin/vers/equipe.csv              data/
cp /chemin/vers/materiel_traiteur.csv   data/
```

---

## Étape 3 — Installer Airflow

```bash
# Rendre le script exécutable
chmod +x install_airflow.sh

# Lancer l'installation (prend ~5 minutes)
./install_airflow.sh
```

Si vous êtes sur Windows, lancez les commandes du script une par une dans Git Bash.

---

## Étape 4 — Démarrer Airflow (2 terminaux)

**Terminal 1 — Webserver :**
```bash
source venv/bin/activate
airflow webserver --port 8080
```

**Terminal 2 — Scheduler :**
```bash
source venv/bin/activate
airflow scheduler
```

Ouvrez ensuite : **http://localhost:8080**
Login : `admin` / `admin123`

---

## Étape 5 — Configurer la connexion PostgreSQL dans l'UI

1. Dans l'interface Airflow, allez dans **Admin > Connections**
2. Cliquez **+** pour ajouter une connexion
3. Remplissez :
   - **Connection Id** : `postgres_traiteur_dwh`
   - **Connection Type** : `Postgres`
   - **Host** : `localhost`
   - **Database** : `traiteur_dwh`
   - **Login** : `postgres`
   - **Password** : `tsila`
   - **Port** : `5432`
4. Cliquez **Save**

---

## Étape 6 — Lancer le DAG

1. Dans l'interface Airflow, cherchez le DAG **`etl_traiteur`**
2. Activez-le en cliquant le bouton ON/OFF
3. Cliquez sur **▶ Trigger DAG** pour l'exécuter manuellement
4. Cliquez sur la dernière exécution pour voir les logs de chaque tâche

---

## Ce que fait le pipeline (les 7 tâches)

```
verifier_sources
       │
  ┌────┴────┐          ← Extraction en PARALLÈLE
  │         │
extraire_  extraire_
postgres   fichiers
  │         │
  └────┬────┘
       │
  transformer          ← Nettoyage + calculs + préparation des dimensions
       │
charger_dimensions     ← dim_client, dim_lieu, dim_date, dim_plat, dim_statut
       │
 charger_faits         ← fait_traiteur avec toutes les métriques
       │
rapport_final          ← Résumé dans les logs (CA, marge, top clients...)
```

---

## Métriques calculées pour chaque événement

| Mesure | Calcul |
|--------|--------|
| `total_salaires` | Somme des salaires des employés mobilisés |
| `total_materiels` | Somme du coût des matériels loués |
| `cout_preparation` | Somme(coût_prépa × nb_pax) pour chaque plat |
| `revenus_plats` | Somme(prix × nb_pax) pour chaque plat |
| `marge_brute` | revenus_plats − cout_prépa − salaires − matériels |

---

## Commandes utiles

```bash
# Lister les DAGs
airflow dags list

# Tester une seule tâche (sans exécuter tout le pipeline)
airflow tasks test etl_traiteur verifier_sources 2024-01-01

# Voir les logs d'une tâche
airflow tasks logs etl_traiteur transformer 2024-01-01

# Relancer manuellement
airflow dags trigger etl_traiteur
```

---

## Questions fréquentes

**Q : J'ai une erreur "ModuleNotFoundError: No module named 'airflow'"**
→ Vous avez oublié d'activer le venv : `source venv/bin/activate`

**Q : Le DAG n'apparaît pas dans l'interface**
→ Copiez le fichier dans `~/airflow/dags/` et attendez 30 secondes

**Q : Erreur de connexion à PostgreSQL**
→ Vérifiez que PostgreSQL tourne : `sudo service postgresql status`

**Q : "fait_traiteur already exists" au rechargement**
→ Normal, le `ON CONFLICT ... DO UPDATE` gère ça automatiquement

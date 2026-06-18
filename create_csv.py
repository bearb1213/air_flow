"""
Script pour créer un fichier CSV
"""
import csv
from datetime import datetime

def create_csv(headers, data, filename):
    """
    Crée un fichier CSV avec les données fournies
    """
    # Sauvegarder le fichier CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        # Écrire les en-têtes
        writer.writerow(headers)
        
        # Écrire les données
        writer.writerows(data)
    
    print(f"✓ Fichier CSV créé avec succès: {filename}")

if __name__ == "__main__":
    # poste : plongeur , serveur , cuisinier
    # Les traiteurs avec statut 'confirme' peuvent avoir 0, 1, 2 ou 3 employes
    
    header_equipe = ["traiteur_code", "emp_code", "poste", "salaire", "heure_travail"]  # heure_travail en int (heures)
    data_equipe = [
        # TRT001 - 2 employes (court événement - 6h)
        ['TRT001', 'EMP001', 'Cuisinier', 95000.00, 7],
        ['TRT001', 'EMP002', 'Serveur', 65000.00, 6],
        
        # TRT002 - 3 employes (long événement - 10h)
        ['TRT002', 'EMP003', 'Cuisinier', 98000.00, 10],
        ['TRT002', 'EMP004', 'Serveur', 72000.00, 10],
        ['TRT002', 'EMP005', 'Plongeur', 50000.00, 9],
        
        # TRT004 - 1 employe (moyen - 8h)
        ['TRT004', 'EMP006', 'Cuisinier', 105000.00, 8],
        
        # TRT006 - 2 employes (court - 6h)
        ['TRT006', 'EMP007', 'Serveur', 68000.00, 6],
        ['TRT006', 'EMP008', 'Plongeur', 48000.00, 5],
        
        # TRT007 - 3 employes (long - 11h)
        ['TRT007', 'EMP009', 'Cuisinier', 110000.00, 11],
        ['TRT007', 'EMP010', 'Serveur', 70000.00, 11],
        ['TRT007', 'EMP011', 'Plongeur', 52000.00, 10],
        
        # TRT009 - 2 employes (moyen - 8h)
        ['TRT009', 'EMP012', 'Cuisinier', 92000.00, 8],
        ['TRT009', 'EMP013', 'Serveur', 64000.00, 8],
        
        # TRT010 - 3 employes (long - 10h)
        ['TRT010', 'EMP014', 'Cuisinier', 108000.00, 10],
        ['TRT010', 'EMP015', 'Serveur', 75000.00, 9],
        ['TRT010', 'EMP016', 'Plongeur', 54000.00, 10],
        
        # TRT012 - 1 employe (court - 6h)
        ['TRT012', 'EMP017', 'Cuisinier', 102000.00, 6],
        
        # TRT013 - 2 employes (moyen - 8h)
        ['TRT013', 'EMP018', 'Serveur', 66000.00, 8],
        ['TRT013', 'EMP019', 'Plongeur', 51000.00, 7],
        
        # TRT016 - 1 employe (court - 7h)
        ['TRT016', 'EMP020', 'Cuisinier', 100000.00, 7],
        
        # TRT019 - 0 employe
        
        # TRT020 - 2 employes (moyen - 9h)
        ['TRT020', 'EMP001', 'Serveur', 70000.00, 9],
        ['TRT020', 'EMP002', 'Plongeur', 49000.00, 8],
        
        # TRT021 - 1 employe (court - 6h)
        ['TRT021', 'EMP003', 'Cuisinier', 96000.00, 6],
        
        # TRT022 - 3 employes (long - 11h)
        ['TRT022', 'EMP004', 'Cuisinier', 107000.00, 11],
        ['TRT022', 'EMP005', 'Serveur', 71000.00, 10],
        ['TRT022', 'EMP006', 'Plongeur', 53000.00, 9],
        
        # TRT024 - 2 employes (moyen - 8h)
        ['TRT024', 'EMP007', 'Cuisinier', 93000.00, 8],
        ['TRT024', 'EMP008', 'Serveur', 67000.00, 7],
        
        # TRT025 - 1 employe (court - 5h)
        ['TRT025', 'EMP009', 'Plongeur', 50000.00, 5],
        
        # TRT026 - 3 employes (long - 12h)
        ['TRT026', 'EMP010', 'Cuisinier', 109000.00, 12],
        ['TRT026', 'EMP011', 'Serveur', 74000.00, 11],
        ['TRT026', 'EMP012', 'Plongeur', 55000.00, 10],
        
        # TRT027 - 0 employe
        
        # TRT029 - 2 employes (moyen - 9h)
        ['TRT029', 'EMP013', 'Cuisinier', 94000.00, 9],
        ['TRT029', 'EMP014', 'Serveur', 69000.00, 9],
        
        # TRT030 - 1 employe (court - 7h)
        ['TRT030', 'EMP015', 'Cuisinier', 103000.00, 7],
        
        # TRT031 - 3 employes (long - 10h)
        ['TRT031', 'EMP016', 'Cuisinier', 111000.00, 10],
        ['TRT031', 'EMP017', 'Serveur', 76000.00, 9],
        ['TRT031', 'EMP018', 'Plongeur', 56000.00, 8],
        
        # TRT032 - 2 employes (moyen - 8h)
        ['TRT032', 'EMP019', 'Cuisinier', 97000.00, 8],
        ['TRT032', 'EMP020', 'Serveur', 68000.00, 8],
        
        # TRT034 - 1 employe (court - 6h)
        ['TRT034', 'EMP001', 'Cuisinier', 104000.00, 6],
        
        # TRT035 - 3 employes (long - 11h)
        ['TRT035', 'EMP002', 'Cuisinier', 106000.00, 11],
        ['TRT035', 'EMP003', 'Serveur', 73000.00, 10],
        ['TRT035', 'EMP004', 'Plongeur', 51000.00, 9],
        
        # TRT037 - 0 employe
        
        # TRT038 - 2 employes (moyen - 9h)
        ['TRT038', 'EMP005', 'Cuisinier', 99000.00, 9],
        ['TRT038', 'EMP006', 'Serveur', 72000.00, 8],
        
        # TRT039 - 1 employe (court - 5h)
        ['TRT039', 'EMP007', 'Plongeur', 50000.00, 5],
        
        # TRT041 - 3 employes (long - 12h)
        ['TRT041', 'EMP008', 'Cuisinier', 112000.00, 12],
        ['TRT041', 'EMP009', 'Serveur', 77000.00, 11],
        ['TRT041', 'EMP010', 'Plongeur', 57000.00, 10],
        
        # TRT042 - 2 employes (moyen - 8h)
        ['TRT042', 'EMP011', 'Cuisinier', 91000.00, 8],
        ['TRT042', 'EMP012', 'Serveur', 65000.00, 7],
        
        # TRT043 - 1 employe (court - 6h)
        ['TRT043', 'EMP013', 'Cuisinier', 101000.00, 6],
        
        # TRT044 - 2 employes (moyen - 9h)
        ['TRT044', 'EMP014', 'Serveur', 71000.00, 9],
        ['TRT044', 'EMP015', 'Plongeur', 52000.00, 8],
        
        # TRT045 - 0 employe
        
        # TRT047 - 1 employe (court - 7h)
        ['TRT047', 'EMP016', 'Cuisinier', 89000.00, 7],
        
        # TRT049 - 3 employes (long - 10h)
        ['TRT049', 'EMP017', 'Cuisinier', 113000.00, 10],
        ['TRT049', 'EMP018', 'Serveur', 78000.00, 9],
        ['TRT049', 'EMP019', 'Plongeur', 58000.00, 9],
        
        # TRT052 - 2 employes (moyen - 8h)
        ['TRT052', 'EMP020', 'Cuisinier', 98000.00, 8],
        ['TRT052', 'EMP001', 'Serveur', 69000.00, 7],
        
        # TRT053 - 1 employe (court - 6h)
        ['TRT053', 'EMP002', 'Cuisinier', 90000.00, 6],
        
        # TRT055 - 2 employes (long - 10h)
        ['TRT055', 'EMP003', 'Serveur', 73000.00, 10],
        ['TRT055', 'EMP004', 'Plongeur', 53000.00, 9],
        
        # TRT056 - 1 employe (court - 8h)
        ['TRT056', 'EMP005', 'Cuisinier', 114000.00, 8],
    ]
    filename_equipe = "sql/equipe.csv"

    create_csv(header_equipe, data_equipe, filename_equipe)

    # =====================
    # MATERIEL PAR TRAITEUR
    # =====================
    header_materiel = ["traiteur_code", "materiel_code", "nombre", "prix"]
    data_materiel = [
        # TRT001 - 2 materiels
        ['TRT001', 'MAT001', 8, 40000.00],
        ['TRT001', 'MAT002', 50, 25000.00],
        
        # TRT002 - 3 materiels
        ['TRT002', 'MAT001', 12, 60000.00],
        ['TRT002', 'MAT003', 1, 15000.00],
        ['TRT002', 'MAT008', 2, 24000.00],
        
        # TRT004 - 1 materiel
        ['TRT004', 'MAT001', 10, 50000.00],
        
        # TRT006 - 2 materiels
        ['TRT006', 'MAT002', 40, 20000.00],
        ['TRT006', 'MAT017', 2, 3000.00],
        
        # TRT007 - 3 materiels
        ['TRT007', 'MAT001', 15, 75000.00],
        ['TRT007', 'MAT003', 1, 15000.00],
        ['TRT007', 'MAT005', 2, 16000.00],
        
        # TRT009 - 2 materiels
        ['TRT009', 'MAT002', 45, 22500.00],
        ['TRT009', 'MAT019', 1, 80000.00],
        
        # TRT010 - 3 materiels
        ['TRT010', 'MAT001', 14, 70000.00],
        ['TRT010', 'MAT003', 1, 15000.00],
        ['TRT010', 'MAT008', 3, 36000.00],
        
        # TRT012 - 1 materiel
        ['TRT012', 'MAT009', 8, 48000.00],
        
        # TRT013 - 2 materiels
        ['TRT013', 'MAT002', 35, 17500.00],
        ['TRT013', 'MAT017', 3, 4500.00],
        
        # TRT016 - 0 materiels
        
        # TRT019 - 2 materiels
        ['TRT019', 'MAT001', 16, 80000.00],
        ['TRT019', 'MAT011', 1, 10000.00],
        
        # TRT020 - 1 materiel
        ['TRT020', 'MAT002', 30, 15000.00],
        
        # TRT021 - 2 materiels
        ['TRT021', 'MAT001', 11, 55000.00],
        ['TRT021', 'MAT005', 1, 8000.00],
        
        # TRT022 - 3 materiels
        ['TRT022', 'MAT001', 18, 90000.00],
        ['TRT022', 'MAT003', 1, 15000.00],
        ['TRT022', 'MAT019', 1, 80000.00],
        
        # TRT024 - 1 materiel
        ['TRT024', 'MAT002', 25, 12500.00],
        
        # TRT025 - 2 materiels
        ['TRT025', 'MAT001', 13, 65000.00],
        ['TRT025', 'MAT008', 1, 12000.00],
        
        # TRT026 - 3 materiels
        ['TRT026', 'MAT001', 20, 100000.00],
        ['TRT026', 'MAT011', 1, 10000.00],
        ['TRT026', 'MAT020', 1, 50000.00],
        
        # TRT027 - 0 materiels
        
        # TRT029 - 2 materiels
        ['TRT029', 'MAT002', 38, 19000.00],
        ['TRT029', 'MAT005', 2, 16000.00],
        
        # TRT030 - 1 materiel
        ['TRT030', 'MAT009', 9, 54000.00],
        
        # TRT031 - 3 materiels
        ['TRT031', 'MAT001', 17, 85000.00],
        ['TRT031', 'MAT003', 1, 15000.00],
        ['TRT031', 'MAT008', 2, 24000.00],
        
        # TRT032 - 2 materiels
        ['TRT032', 'MAT002', 42, 21000.00],
        ['TRT032', 'MAT017', 2, 3000.00],
        
        # TRT034 - 1 materiel
        ['TRT034', 'MAT001', 9, 45000.00],
        
        # TRT035 - 3 materiels
        ['TRT035', 'MAT001', 16, 80000.00],
        ['TRT035', 'MAT011', 1, 10000.00],
        ['TRT035', 'MAT019', 1, 80000.00],
        
        # TRT037 - 0 materiels
        
        # TRT038 - 2 materiels
        ['TRT038', 'MAT002', 36, 18000.00],
        ['TRT038', 'MAT005', 1, 8000.00],
        
        # TRT039 - 1 materiel
        ['TRT039', 'MAT021', 1, 12000.00],
        
        # TRT041 - 3 materiels
        ['TRT041', 'MAT001', 19, 95000.00],
        ['TRT041', 'MAT012', 1, 20000.00],
        ['TRT041', 'MAT020', 1, 50000.00],
        
        # TRT042 - 2 materiels
        ['TRT042', 'MAT002', 40, 20000.00],
        ['TRT042', 'MAT008', 1, 12000.00],
        
        # TRT043 - 1 materiel
        ['TRT043', 'MAT009', 10, 60000.00],
        
        # TRT044 - 2 materiels
        ['TRT044', 'MAT001', 12, 60000.00],
        ['TRT044', 'MAT017', 3, 4500.00],
        
        # TRT045 - 0 materiels
        
        # TRT047 - 1 materiel
        ['TRT047', 'MAT002', 32, 16000.00],
        
        # TRT049 - 3 materiels
        ['TRT049', 'MAT001', 21, 105000.00],
        ['TRT049', 'MAT003', 1, 15000.00],
        ['TRT049', 'MAT019', 1, 80000.00],
        
        # TRT052 - 2 materiels
        ['TRT052', 'MAT001', 15, 75000.00],
        ['TRT052', 'MAT011', 1, 10000.00],
        
        # TRT053 - 1 materiel
        ['TRT053', 'MAT009', 11, 66000.00],
        
        # TRT055 - 2 materiels
        ['TRT055', 'MAT002', 48, 24000.00],
        ['TRT055', 'MAT005', 2, 16000.00],
        
        # TRT056 - 0 materiels
    ]
    filename_materiel = "sql/materiel_traiteur.csv"

    create_csv(header_materiel, data_materiel, filename_materiel)
 
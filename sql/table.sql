
CREATE TABLE employes (
    emp_code VARCHAR(255) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL ,
    prenom VARCHAR(255) ,
    email VARCHAR(255) ,
    salaire_j DECIMAL(10,2)
    telephone VARCHAR(255)  
);

CREATE TABLE clients (
    client_code VARCHAR(255) PRIMARY KEY ,
    nom VARCHAR(255) NOT NULL ,
    prenom VARCHAR(255) ,
    email VARCHAR(255) NOT NULL ,
    telephone VARCHAR(255) 
);

CREATE TABLE materiel_types (
    type_code VARCHAR(255) PRIMARY KEY ,
    label VARCHAR(255) NOT NULL
);

CREATE TABLE materiels (
    materiel_code VARCHAR(255) PRIMARY KEY ,
    label VARCHAR(255) NOT NULL,
    type_code VARCHAR(255) REFERENCES materiel_type(type_code),
    longueur DECIMAL(12,2) DEFAULT 0,
    largeur DECIMAL(12,2) DEFAULT 0,
    hauteur DECIMAL(12,2) DEFAULT 0,
    cout_emprunt DECIMAL(10,2) ,
    caution DECIMAL(10,2)
);

CREATE TABLE plat_types (
    type_code VARCHAR(255) PRIMARY KEY ,
    label VARCHAR(255) NOT NULL ,
);
 
CREATE TABLE plats (
    plat_code VARCHAR(255) PRIMARY KEY,
    label VARCHAR(255) NOT NULL ,
    type_code VARCHAR(255) NOT NULL ,
    cout_preparation DECIMAL(10,2) NOT NULL ,
    prix DECIMAL(10,2) NOT NULL 
);


-- =====================
-- employes (20 total)
-- =====================
INSERT INTO employes (emp_code, nom, prenom, email, salaire_j, telephone) VALUES
('EMP001', 'Rakoto', 'Jean', 'jean.rakoto@entreprise.mg', 85000.00, '034 12 345 67'),
('EMP002', 'Ratsima', 'Marie', 'marie.ratsima@entreprise.mg', 92000.00, '033 98 765 43'),
('EMP003', 'Andria', 'Paul', 'paul.andria@entreprise.mg', 78000.00, '032 55 111 22'),
('EMP004', 'Rasoa', 'Clara', 'clara.rasoa@entreprise.mg', 105000.00, '034 77 888 99'),
('EMP005', 'Randriam', 'Luc', 'luc.randriam@entreprise.mg', 67000.00, '033 22 444 55'),
('EMP006', 'Raharison', 'Tina', 'tina.raharison@entreprise.mg', 91000.00, '034 55 667 88'),
('EMP007', 'Randria', 'Mika', 'mika.randria@entreprise.mg', 73000.00, '032 11 999 44'),
('EMP008', 'Rakotondrabe', 'Feno', 'feno.rako@entreprise.mg', 88000.00, '033 66 222 11'),
('EMP009', 'Rajaonarison', 'Haja', 'haja.rajao@entreprise.mg', 110000.00, '034 33 777 55'),
('EMP010', 'Andriantsoa', 'Nivo', 'nivo.andrian@entreprise.mg', 69000.00, '032 88 333 66'),
('EMP011', 'Ramarolahy', 'Aina', 'aina.ramaro@entreprise.mg', 95000.00, '033 77 111 88'),
('EMP012', 'Rakotoarison', 'Seta', 'seta.rakoto@entreprise.mg', 82000.00, '034 22 555 99'),
('EMP013', 'Ratolojanahary', 'Dina', 'dina.ratol@entreprise.mg', 76000.00, '032 44 888 22'),
('EMP014', 'Randriamahefa', 'Lova', 'lova.randriam@entreprise.mg', 101000.00, '033 55 444 77'),
('EMP015', 'Rasoanaivo', 'Vola', 'vola.rasoa@entreprise.mg', 87000.00, '034 99 222 44'),
('EMP016', 'Andriamanana', 'Fidy', 'fidy.andria@entreprise.mg', 72000.00, '032 66 777 33'),
('EMP017', 'Rakotondrazaka', 'Niry', 'niry.rako@entreprise.mg', 98000.00, '033 11 888 55'),
('EMP018', 'Ralaivao', 'Tojo', 'tojo.ralai@entreprise.mg', 83000.00, '034 44 333 11'),
('EMP019', 'Ramanantoanina', 'Bodo', 'bodo.raman@entreprise.mg', 115000.00, '032 99 666 44'),
('EMP020', 'Ranaivoson', 'Zo', 'zo.ranaivo@entreprise.mg', 70000.00, '033 33 555 22');

-- =====================
-- clients (20 total)
-- =====================
INSERT INTO clients (client_code, nom, prenom, email, telephone) VALUES
('CLI001', 'Rabemananjara', 'Hery', 'hery.rabe@gmail.com', '034 11 222 33'),
('CLI002', 'Randrianarison', 'Soa', 'soa.rand@yahoo.com', '033 44 555 66'),
('CLI003', 'Rakotomalala', 'Fidy', 'fidy.rakoto@gmail.com', '032 77 888 00'),
('CLI004', 'Andriamasinoro', 'Tojo', 'tojo.andria@email.mg', '034 99 111 22'),
('CLI005', 'Rafaralahy', 'Nirina', 'nirina.rafar@gmail.com', '033 33 666 77'),
('CLI006', 'Rakotonirina', 'Haingo', 'haingo.rako@gmail.com', '034 55 333 88'),
('CLI007', 'Randriamboavonjy', 'Sitraka', 'sitraka.rand@yahoo.com', '032 22 777 44'),
('CLI008', 'Rasoazanany', 'Miora', 'miora.rasoa@gmail.com', '033 88 444 11'),
('CLI009', 'Andrianarivo', 'Mahefa', 'mahefa.andria@email.mg', '034 66 999 55'),
('CLI010', 'Rakotondratsima', 'Lalao', 'lalao.rako@gmail.com', '032 11 555 33'),
('CLI011', 'Rajaobelina', 'Ravo', 'ravo.rajao@gmail.com', '033 99 222 77'),
('CLI012', 'Randrianantoandro', 'Lanto', 'lanto.rand@yahoo.com', '034 44 888 00'),
('CLI013', 'Ramaroson', 'Tantely', 'tantely.ramas@gmail.com', '032 77 333 99'),
('CLI014', 'Rakotovao', 'Hasina', 'hasina.rako@email.mg', '033 55 111 44'),
('CLI015', 'Andriambelo', 'Tiana', 'tiana.andria@gmail.com', '034 22 666 88'),
('CLI016', 'Ratsimbazafy', 'Hanitra', 'hanitra.rats@gmail.com', '032 88 999 22'),
('CLI017', 'Rakotoarivelo', 'Mamy', 'mamy.rako@yahoo.com', '033 11 444 66'),
('CLI018', 'Randriamahazosoa', 'Volatiana', 'vola.rand@gmail.com', '034 77 555 33'),
('CLI019', 'Rajaonah', 'Herizo', 'herizo.rajao@email.mg', '032 44 222 88'),
('CLI020', 'Andriantsalama', 'Misa', 'misa.andrian@gmail.com', '033 66 888 11');

-- =====================
-- materiel_types (8 total)
-- =====================
INSERT INTO materiel_types (type_code, label) VALUES
('MTYP001', 'Mobilier'),
('MTYP002', 'Sonorisation'),
('MTYP003', 'Eclairage'),
('MTYP004', 'Vaisselle'),
('MTYP005', 'Decoration'),
('MTYP006', 'Tente et Structure'),
('MTYP007', 'electromenager'),
('MTYP008', 'Textile');

-- =====================
-- materiels (25 total)
-- =====================
INSERT INTO materiels (materiel_code, label, type_code, longueur, largeur, hauteur, cout_emprunt, caution) VALUES
('MAT001', 'Table ronde 8 places',      'MTYP001', 150.00, 150.00,  75.00,  5000.00,  20000.00),
('MAT002', 'Chaise pliante',            'MTYP001',  45.00,  45.00,  90.00,   500.00,   2000.00),
('MAT003', 'Systeme de sonorisation',   'MTYP002', 120.00,  60.00,  80.00, 15000.00,  80000.00),
('MAT004', 'Microphone sans fil',       'MTYP002',  30.00,   8.00,   8.00,  3000.00,  15000.00),
('MAT005', 'Projecteur LED',            'MTYP003',  40.00,  30.00,  20.00,  8000.00,  40000.00),
('MAT006', 'Guirlande lumineuse 5m',    'MTYP003', 500.00,   0.00,   0.00,  2000.00,   5000.00),
('MAT007', 'Service assiettes x10',     'MTYP004',  30.00,  30.00,   5.00,  4000.00,  25000.00),
('MAT008', 'Arche florale',             'MTYP005', 200.00,  50.00, 220.00, 12000.00,  30000.00),
('MAT009', 'Table rectangulaire 10p',   'MTYP001', 240.00,  80.00,  75.00,  6000.00,  22000.00),
('MAT010', 'Tabouret bar',              'MTYP001',  35.00,  35.00, 110.00,   800.00,   3000.00),
('MAT011', 'Enceinte Bluetooth 500W',   'MTYP002',  50.00,  40.00,  60.00, 10000.00,  50000.00),
('MAT012', 'Table de mixage DJ',        'MTYP002',  60.00,  40.00,  15.00, 20000.00, 100000.00),
('MAT013', 'Spot PAR LED couleur',      'MTYP003',  20.00,  20.00,  25.00,  5000.00,  20000.00),
('MAT014', 'Chandelier 5 branches',     'MTYP003',  40.00,  40.00,  60.00,  7000.00,  18000.00),
('MAT015', 'Flûtes à champagne x12',    'MTYP004',   8.00,   8.00,  22.00,  3000.00,  15000.00),
('MAT016', 'Couverts inox x10',         'MTYP004',  25.00,  10.00,   2.00,  2500.00,  12000.00),
('MAT017', 'Nappe blanche 3m',          'MTYP008', 300.00, 150.00,   0.10,  1500.00,   5000.00),
('MAT018', 'Chemin de table dore',      'MTYP008', 300.00,  30.00,   0.10,  1000.00,   3000.00),
('MAT019', 'Tente 10x10m',              'MTYP006',1000.00,1000.00, 350.00, 80000.00, 300000.00),
('MAT020', 'Podium scene 4x3m',         'MTYP006', 400.00, 300.00,  60.00, 50000.00, 200000.00),
('MAT021', 'Refrigerateur portable',    'MTYP007',  60.00,  55.00,  85.00, 12000.00,  60000.00),
('MAT022', 'Chauffe-plat electrique',   'MTYP007',  50.00,  35.00,  20.00,  5000.00,  25000.00),
('MAT023', 'Panneau de bienvenue',      'MTYP005',  80.00,   5.00, 180.00,  4000.00,  10000.00),
('MAT024', 'Centre de table floral',    'MTYP005',  30.00,  30.00,  40.00,  6000.00,   8000.00),
('MAT025', 'Photobooth cadre bois',     'MTYP005', 120.00,  10.00, 150.00, 15000.00,  40000.00);

-- =====================
-- plat_types (7 total)
-- =====================
INSERT INTO plat_types (type_code, label) VALUES
('PTYP001', 'Entree'),
('PTYP002', 'Plat principal'),
('PTYP003', 'Dessert'),
('PTYP004', 'Boisson'),
('PTYP005', 'Amuse-bouche'),
('PTYP006', 'Cocktail');

-- =====================
-- plats (30 total)
-- =====================
INSERT INTO plats (plat_code, label, type_code, cout_preparation, prix) VALUES
('PLT001', 'Salade de crudites',              'PTYP001',  3000.00,   6000.00),
('PLT002', 'Veloute de legumes',              'PTYP001',  4000.00,   7500.00),
('PLT003', 'Carpaccio de thon',               'PTYP001',  7000.00,  13000.00),
('PLT004', 'Salade avocat crevettes',         'PTYP001',  8000.00,  14000.00),
('PLT005', 'Soupe de tomate basilic',         'PTYP001',  3500.00,   7000.00),
('PLT006', 'Romazava traditionnel',           'PTYP002',  8000.00,  15000.00),
('PLT007', 'Poulet grille sauce coco',        'PTYP002', 10000.00,  18000.00),
('PLT008', 'Riz cantonnais',                  'PTYP002',  5000.00,   9000.00),
('PLT009', 'Zebu braise sauce poivre vert',   'PTYP002', 14000.00,  25000.00),
('PLT010', 'Poisson sauce gingembre',         'PTYP002', 11000.00,  20000.00),
('PLT011', 'Brochettes de porc marine',       'PTYP002',  9000.00,  16000.00),
('PLT012', 'Lasagnes bolognaise',             'PTYP002', 10000.00,  17000.00),
('PLT013', 'Poulet rôti pommes de terre',     'PTYP002', 12000.00,  21000.00),
('PLT014', 'Gâteau vanille maison',           'PTYP003',  6000.00,  10000.00),
('PLT015', 'Salade de fruits frais',          'PTYP003',  3500.00,   6500.00),
('PLT016', 'Mousse au chocolat',              'PTYP003',  5000.00,   9000.00),
('PLT017', 'Panna cotta fruits rouges',       'PTYP003',  5500.00,   9500.00),
('PLT018', 'Creme brûlee',                    'PTYP003',  4500.00,   8500.00),
('PLT019', 'Tarte aux fraises',               'PTYP003',  7000.00,  12000.00),
('PLT020', 'Jus de fruits naturel',           'PTYP004',  2000.00,   4000.00),
('PLT021', 'Eau minerale (bouteille)',        'PTYP004',   500.00,   1500.00),
('PLT022', 'Punch maison sans alcool',        'PTYP004',  3000.00,   5500.00),
('PLT023', 'Cafe / The',                      'PTYP004',  1000.00,   2500.00),
('PLT024', 'Limonade gingembre maison',       'PTYP004',  2500.00,   4500.00),
('PLT025', 'Mini-brochettes aperitives x6',   'PTYP005',  4000.00,   7000.00),
('PLT026', 'Verrines legumes x4',             'PTYP005',  3500.00,   6000.00),
('PLT027', 'Cocktail de bienvenue (verre)',   'PTYP006',  3000.00,   5000.00),
('PLT028', 'Cocktail petillant au gingembre', 'PTYP006',  3500.00,   6000.00);
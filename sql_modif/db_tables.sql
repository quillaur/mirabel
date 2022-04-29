CREATE TABLE IF NOT EXISTS Targetscan(
    IdTargetscan INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdTargetscan)
);


CREATE TABLE IF NOT EXISTS Svmicro(
    IdSvmicro INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdSvmicro)
);

CREATE TABLE IF NOT EXISTS Pita(
    IdPita INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdPita)
);

CREATE TABLE IF NOT EXISTS Miranda(
    IdMiranda INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMiranda)
);

CREATE TABLE IF NOT EXISTS Mirwalk(
    IdMirwalk INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Localisation ENUM('3UTR', '5UTR', 'CDS'),
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirwalk)
);

CREATE TABLE IF NOT EXISTS Mirtarbase(
    IdMirtarbase INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Experiment LONGTEXT,
	PRIMARY KEY (IdMirtarbase)
);
ALTER TABLE Mirtarbase CONVERT TO CHARACTER SET utf8;

CREATE TABLE IF NOT EXISTS Mirecords(
    IdMirecords INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Experiment LONGTEXT,
	PRIMARY KEY (IdMirecords)
);
ALTER TABLE Mirecords CONVERT TO CHARACTER SET utf8;

CREATE TABLE IF NOT EXISTS Mirmap(
    IdMirmap INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirmap)
);

CREATE TABLE IF NOT EXISTS Mirdb(
    IdMirdb INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirdb)
);

CREATE TABLE IF NOT EXISTS Comir(
    IdComir INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdComir)
);

-- CREATE TABLE IF NOT EXISTS Mirabel(
--     IdMirabel INT UNSIGNED AUTO_INCREMENT,
-- 	Mimat int(11) NOT NULL,
-- 	GeneID int(11) NOT NULL,
-- 	Score FLOAT,
-- 	Validated ENUM("0", "1") DEFAULT "0",
-- 	PRIMARY KEY (IdMirabel)
-- );

-- CREATE UNIQUE INDEX unique_mir_gene
-- ON Mirabel(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mbstar(
    IdMbstar INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMbstar)
);

CREATE TABLE IF NOT EXISTS Exprtarget(
    IdExprtarget INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdExprtarget)
);

CREATE TABLE IF NOT EXISTS Rna22(
    IdRna22 INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdRna22)
);

CREATE TABLE IF NOT EXISTS Mirdip(
    IdMirdip INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirdip)
);

CREATE TABLE IF NOT EXISTS ExistingMirabel(
    Name VARCHAR(50) NOT NULL UNIQUE,
	Targetscan ENUM("0", "1") DEFAULT "0",
	Miranda ENUM("0", "1") DEFAULT "0",
	Pita ENUM("0", "1") DEFAULT "0",
	Svmicro ENUM("0", "1") DEFAULT "0",
	Comir ENUM("0", "1") DEFAULT "0",
	Mirmap ENUM("0", "1") DEFAULT "0",
	Mirdb ENUM("0", "1") DEFAULT "0",
	Mirwalk ENUM("0", "1") DEFAULT "0",
	Mbstar ENUM("0", "1") DEFAULT "0",
	Exprtarget ENUM("0", "1") DEFAULT "0"
);

CREATE UNIQUE INDEX unique_Targetscan_mir_gene
ON Targetscan(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Svmicro_mir_gene
ON Svmicro(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Pita_mir_gene
ON Pita(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Miranda_mir_gene
ON Miranda(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mirwalk_mir_gene
ON Mirwalk(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mirtarbase_mir_gene
ON Mirtarbase(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mirecords_mir_gene
ON Mirecords(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mirmap_mir_gene
ON Mirmap(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mirdb_mir_gene
ON Mirdb(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Comir_mir_gene
ON Comir(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mbstar_mir_gene
ON Mbstar(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Rna22_mir_gene
ON Rna22(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Mirdip_mir_gene
ON Mirdip(Mimat, GeneID);

CREATE UNIQUE INDEX unique_Exprtarget_mir_gene
ON Exprtarget(Mimat, GeneID);

-- CREATE UNIQUE INDEX unique_gene_id
-- ON genes3(ncbi_gene_id);
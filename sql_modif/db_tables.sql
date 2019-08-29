CREATE TABLE IF NOT EXISTS Targetscan(
    IdTargetscan INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdTargetscan)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Targetscan(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Svmicro(
    IdSvmicro INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdSvmicro)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Svmicro(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Pita(
    IdPita INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdPita)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Pita(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Miranda(
    IdMiranda INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMiranda)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Miranda(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mirwalk(
    IdMirwalk INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Localisation ENUM('3UTR', '5UTR', 'CDS'),
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirwalk)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Mirwalk(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mirtarbase(
    IdMirtarbase INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Experiment LONGTEXT,
	PRIMARY KEY (IdMirtarbase)
);
ALTER TABLE Mirtarbase CONVERT TO CHARACTER SET utf8;

CREATE UNIQUE INDEX unique_mir_gene
ON Mirtarbase(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mirecords(
    IdMirecords INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Experiment LONGTEXT,
	PRIMARY KEY (IdMirecords)
);
ALTER TABLE Mirecords CONVERT TO CHARACTER SET utf8;

CREATE UNIQUE INDEX unique_mir_gene
ON Mirecords(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mirmap(
    IdMirmap INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirmap)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Mirmap(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mirdb(
    IdMirdb INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirdb)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Mirdb(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Comir(
    IdComir INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdComir)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Comir(Mimat, GeneID);

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

CREATE UNIQUE INDEX unique_mir_gene
ON Mbstar(Mimat, GeneID);

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

CREATE UNIQUE INDEX unique_mir_gene
ON Rna22(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS Mirdip(
    IdMirdip INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirdip)
);

CREATE UNIQUE INDEX unique_mir_gene
ON Mirdip(Mimat, GeneID);

CREATE UNIQUE INDEX unique_mir_gene
ON Exprtarget(Mimat, GeneID);

CREATE TABLE IF NOT EXISTS ExistingMirabel(
    Name VARCHAR(50) NOT NULL UNIQUE,
	Targetscan ENUM("0", "1") DEFAULT "0",
	Miranda ENUM("0", "1") DEFAULT "0",
	Pita ENUM("0", "1") DEFAULT "0",
	Svmicro ENUM("0", "1") DEFAULT "0",
	Comir ENUM("0", "1") DEFAULT "0",
	Mirmap ENUM("0", "1") DEFAULT "0",
	Mirdb ENUM("0", "1") DEFAULT "0",
	Mirwalk ENUM("0", "1") DEFAULT "0"
);

alter table ExistingMirabel add Mbstar ENUM("0", "1") DEFAULT "0";
alter table ExistingMirabel add Exprtarget ENUM("0", "1") DEFAULT "0";

CREATE UNIQUE INDEX unique_gene_id
ON genes3(ncbi_gene_id);
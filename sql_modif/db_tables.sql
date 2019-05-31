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

CREATE TABLE IF NOT EXISTS Mirabel(
    IdMirabel INT UNSIGNED AUTO_INCREMENT,
	Mimat int(11) NOT NULL,
	GeneID int(11) NOT NULL,
	Score FLOAT,
	Validated ENUM("0", "1") DEFAULT "0",
	PRIMARY KEY (IdMirabel)
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
	Mirwalk ENUM("0", "1") DEFAULT "0"
);

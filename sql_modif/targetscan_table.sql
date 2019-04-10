CREATE TABLE IF NOT EXISTS Targetscan(
    IdTargetscan INT UNSIGNED AUTO_INCREMENT,
	MirName VARCHAR(50) NOT NULL,
	GeneID VARCHAR(50) NOT NULL,
	GeneSymbol VARCHAR(50),
	ContextScore FLOAT,
	WeightedContextScore FLOAT,
	PRIMARY KEY (IdTargetscan)
);
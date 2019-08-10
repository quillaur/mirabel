# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 29/03/2019
# Purpose: library of many useful functions.

import configparser
import os
import mysql.connector
import logging
import itertools
from collections import defaultdict

# Set logging module
logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

# widgets = ['Data processing: ', Percentage(), ' ', Bar(marker='0',left='[',right=']'),
#    ' ', ETA(), ' ', FileTransferSpeed()] #see docs for other options
# pbar = ProgressBar(widgets=widgets, maxval=len(scores_dict[db]))
# pbar.start()
# i = 0
# i += 1
# pbar.update(i)
# pbar.finish()


def extract_config():
    """
    Get configuration parameters from config.cfg file.

    :return: dictionary of config parameters.
    :rtype: ConfigParser
    """
    config = configparser.ConfigParser()
    # Get current directory
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(["config.cfg", os.path.expanduser(dir_path.replace("scripts", ""))])

    return config


def mysql_connection(config):
    """
    Set mysql connection

    :param config: configuration parameters dictionary

    :return: connection
    """
    return mysql.connector.connect(
        host=config["DB"]["HOST"],
        user=config["DB"]["USER"],
        passwd=config["DB"]["PASSWORD"],
        db=config["DB"]["DATABASE"]
    )


def chunk(input_list: list, chunk_size: int):
    """
    Yields successive n-sized chunks from input list.

    :param input_list: list you wish to chunk.
    :type input_list: list
    :param chunk_size: how many chunks you wish.
    :type chunk_size: int
    """
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]


def check_files_presence(files_list: list):
    """
    Check that all files exist.
    :param files_list: list of files you wish to check the presence of.
    :type files_list: list

    :return: True if all files present, else false.
    """
    for file in files_list:
        if not os.path.exists(file):
            return False
    return True


def truncate_table(config: dict, table: str):
    connection = mysql_connection(config)
    logging.info("Truncating {} table...".format(table))
    query = "TRUNCATE TABLE {};".format(table)
    cursor = connection.cursor()
    cursor.execute(query)

    # Test if truncate worked
    query = "SELECT count(*) FROM {};".format(table)
    cursor.execute(query)
    if cursor.fetchone()[0] == 0:
        logging.info("Truncate successful !")
    else:
        logging.warning("Truncate FAILED !")

    connection.close()


def get_mirna_conversion_info(config: dict):
    connection = mysql_connection(config)
    query = "SELECT M.nameR, MM.number FROM miR AS M INNER JOIN miR_mimat AS MM ON M.id = MM.mir_id;"
    cursor = connection.cursor()
    cursor.execute(query)

    results_dico = {
        row[0]: row[1]
        for row in cursor
    }

    connection.close()

    return results_dico


def get_gene_conversion_info(config: dict):
    connection = mysql_connection(config)
    query = "SELECT ncbi_gene_id, description, preferredGeneSymbol FROM genes3;"
    cursor = connection.cursor()
    cursor.execute(query)

    result_dico = {}
    for row in cursor:
        gene_names = row[1].replace(";", ",").split(", ")
        if not isinstance(gene_names, list):
            gene_names = row[1].split(" ")

        gene_names.append(row[2])
        gene_names = list(set(gene_names))
        for name in gene_names:
            result_dico[name] = row[0]

    connection.close()

    return result_dico


def get_mirnas(config: dict, db_name: str):
    connection = mysql_connection(config)
    query = "SELECT Mimat FROM {};".format(db_name)
    cursor = connection.cursor()
    cursor.execute(query)

    results_set = set(itertools.chain.from_iterable(cursor))

    connection.close()

    return results_set


def get_predictions_for_mirna(config: dict, db_name: str, mirna: int, elem: str="GeneID"):
    connection = mysql_connection(config)
    if "Svmicro" in db_name:
        query = "SELECT {}, Score FROM {} WHERE Mimat = {} AND Score > 0;".format(elem, db_name, mirna)
    else:
        query = "SELECT {}, Score FROM {} WHERE Mimat = {} ;".format(elem, db_name, mirna)

    cursor = connection.cursor()
    cursor.execute(query)

    results_list = [[int(row[0]), float(row[1])] for row in cursor]

    connection.close()

    return results_list


def get_validated_interactions(config: dict):
    query = "SELECT Mimat, GeneID FROM Mirtarbase;"
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)

    result_dico = defaultdict(list)

    for row in cursor:
        result_dico[int(row[0])].append(int(row[1]))

    query = "SELECT Mimat, GeneID FROM Mirecords;"
    cursor = connection.cursor()
    cursor.execute(query)

    for row in cursor:
        result_dico[int(row[0])].append(int(row[1]))

    connection.close()

    return result_dico

def get_existing_mirabels():
    query = "SELECT Name, Targetscan, Miranda, Pita, Svmicro, Comir, Mirmap, Mirwalk, Mirdb, Mbstar, Exprtarget FROM ExistingMirabel;"
    config = extract_config()
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)

    name_list = ["Name", "Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirwalk", "Mirdb", "Mbstar", "Exprtarget"]

    result_dico = defaultdict(list)
    for row in cursor:
        db_list = [v for i, v in enumerate(name_list) if row[i] == "1"]
        result_dico[row[0]].extend(db_list)

    connection.close()

    results_list = []
    for key, value in result_dico.items():
        tmp_list = [key]
        tmp_list.extend(value)
        results_list.append(tmp_list)

    return results_list

def create_mirabel_table(db_name: str):
    query = """CREATE TABLE IF NOT EXISTS {0}(
            Id{0} INT UNSIGNED AUTO_INCREMENT,
            Mimat int(11) NOT NULL,
            GeneID int(11) NOT NULL,
            Score FLOAT,
            Validated ENUM("0", "1") DEFAULT "0",
            PRIMARY KEY (Id{0}));""".format(db_name)
    config = extract_config()
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.close()

def get_mirabel_metrics(db_name: str):
    query = "SELECT * FROM {};".format(db_name)
    config = extract_config()
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()

    interaction_number = 0
    mimat_list = []
    gene_list = []
    validated_number = 0
    for row in rows:
        interaction_number += 1
        mimat_list.append(row[1])
        gene_list.append(row[2])

        if row[4] == '1':
            validated_number += 1   

    return interaction_number, len(list(set(mimat_list))), len(list(set(gene_list))), validated_number

def insert_to_existing_mirabels(db_name: str, databases: list):
    database_names = ", ".join(databases)
    value_list = ", ".join(['"1"' for db in databases])
    query = """REPLACE INTO ExistingMirabel (Name, {}) 
            VALUES ('{}', {});""".format(database_names, db_name, value_list)
    config = extract_config()
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    connection.close()

def delete_table(db_name: str):
    query = "DROP TABLE IF EXISTS {};".format(db_name)
    config = extract_config()
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()

    query = "DELETE FROM ExistingMirabel WHERE Name = '{}';".format(db_name)
    cursor.execute(query)
    connection.commit()

    connection.close()

def get_common_mirnas(all_db: list):
    config = extract_config()
    logging.info("Getting all miRNAs between these databases: {}...".format(all_db))
    db_mirs_lists = [get_mirnas(config, db) for db in all_db]

    logging.info("Intersecting common miRNAs ...")
    common_mirnas = list(set(db_mirs_lists[0]).intersection(*db_mirs_lists))

    return common_mirnas

def get_common_intrinsic_mirnas(mirabel: str):
    # Get aggregated databases
    query = "SELECT * FROM ExistingMirabel WHERE Name = '{}'".format(mirabel)
    config = extract_config()
    connection = mysql_connection(config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)

    aggregated_db = []
    for row in cursor:
        for elem in row.keys():
            if row[elem] == "1":
                aggregated_db.append(elem)

    return get_common_mirnas(aggregated_db)



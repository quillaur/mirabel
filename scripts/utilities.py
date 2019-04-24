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


def get_predictions_for_mirna(config: dict, db_name: str, mirna: int, order: str, elem: str="GeneID"):
    connection = mysql_connection(config)
    if "Svmicro" in db_name:
        query = "SELECT {} FROM {} WHERE Mimat = {} AND Score > 0 ORDER BY Score {};".format(elem, db_name, mirna, order)
    else:
        query = "SELECT {} FROM {} WHERE Mimat = {} ORDER BY Score {};".format(elem, db_name, mirna, order)
    cursor = connection.cursor()
    cursor.execute(query)

    results_list = list(itertools.chain.from_iterable(cursor))

    connection.close()

    return results_list


def get_validated_interactions(config: dict):
    query = "SELECT Mimat, GeneID FROM Mirtarbase;"
    connection = mysql_connection(config)
    cursor = connection.cursor()
    cursor.execute(query)

    result_dico = defaultdict(list)

    for row in cursor:
        result_dico[row[0]].append(row[1])

    query = "SELECT Mimat, GeneID FROM Mirecords;"
    cursor = connection.cursor()
    cursor.execute(query)

    for row in cursor:
        result_dico[row[0]].append(row[1])

    connection.close()

    return result_dico
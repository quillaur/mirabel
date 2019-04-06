# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 20/03/2019
# Purpose: Get raw data from targetscan website

import logging
import sys
import click
import zipfile

# Personal imports
import utilities


def read_txt_zip_file(filename: str, species: str):
    """
    Extract predictions from targetscan zip text file.

    :param filename: name of file
    :type filename: str
    :param species: species you are looking for. So far 'hsa' only.
    :type species: str

    :return: list of dicts of predictions (easier to insert this than list of lists)

    Examle parsed_data:
    ['Gene ID', 'Gene Symbol', 'Transcript ID', 'Gene Tax ID', 'miRNA', 'Site Type', 'UTR_start', 'UTR end', 'context++ score', 'context++ score percentile', 'weighted context++ score', 'weighted context++ score percentile']
    ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9544', 'mml-miR-23a-3p', '3', '142', '149', '-0.428', '97', '-0.388', '97']
    ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9544', 'mml-miR-23b-3p', '3', '142', '149', '-0.428', '97', '-0.388', '97']
    ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9598', 'ptr-miR-23a', '3', '143', '150', '-0.419', '97', '-0.419', '98']
    ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9598', 'ptr-miR-23b', '3', '143', '150', '-0.419', '97', '-0.419', '98']

    Exemple to_insert_dict:
    {'Gene ID': 'ENSG00000121410.7', 'Gene Symbol': 'A1BG', 'Transcript ID': 'ENST00000263100.3',
    'Gene Tax ID': '9606', 'miRNA': 'hsa-miR-23b-3p', 'Site Type': '3', 'UTR_start': '143',
    'UTR end': '150', 'context++ score': '-0.434', 'context++ score percentile': '97',
    'weighted context++ score': '-0.434', 'weighted context++ score percentile': '98'}
    """
    with zipfile.ZipFile(filename, "r") as my_zip:
        for my_txt in my_zip.namelist():
            with my_zip.open(my_txt) as my_file:
                handle = my_file.read()

                parsed_data = [row.split("\t") for row in handle.decode("utf-8").split("\n")]
                header = [elem for elem in parsed_data[0]]
                del parsed_data[0]

                # Keys of the dict = header item and values = the content of parsed_data
                predictions_list = []
                for row in parsed_data:
                    # Sometimes row = [''] so check length of row before use
                    if len(row) > 1 and species in row[4]:
                        to_insert_dict = {}
                        for key in header:
                            to_insert_dict[key] = row[header.index(key)]

                        predictions_list.append(to_insert_dict)

    return predictions_list


if __name__ == '__main__':
    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set project config
    config = utilities.extract_config()

    # Set variables
    file_name = config["TARGETSCAN"]["SAVE FILE TO"]
    url = config["TARGETSCAN"]["URL"]

    # Download
    try:
        utilities.download(url, file_name)

    except Exception as e:
        logging.error("Download issue: {}".format(e))
        sys.exit("Run aborted.")

    # Data post-processing before DB insert
    logging.info("Post-processing data...")
    predictions_list = read_txt_zip_file(filename=file_name, species="hsa")

    # Insert data in mysql DB
    connection = utilities.mysql_connection(config)
    if click.confirm("Do you wish to TRUNCATE Targetscan table content "
                     "before inserting data?", default=False):
        logging.info("Truncating Targetscan table...")
        query = "TRUNCATE TABLE Targetscan;"
        cursor = connection.cursor()
        cursor.execute(query)
        cursor.commit()

    logging.info("Inserting data in Targetscan table...")
    query = "INSERT INTO Targetscan (MirName, GeneID, GeneSymbol, ContextScore, WeightedContextScore) " \
            "VALUES (%(miRNA)s, %(Gene ID)s, %(Gene Symbol)s, %(context++ score)s, %(weighted context++ score)s);"
    cursor = connection.cursor()

    for sub_list in utilities.chunk(predictions_list, 1000):
        cursor.executemany(query, sub_list)
    connection.commit()
    connection.close()

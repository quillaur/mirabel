# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 20/03/2019
# Purpose: Get raw data from targetscan website

import logging
import sys
import click
import zipfile
from datetime import datetime
import os

# Personal imports
import utilities


def read_txt_zip_file(filename: str, species: str):
    """
    Extract predictions from targetscan zip text file.

    :param filename: name of file
    :type filename: str
    :param species: species you are looking for. So far 'hsa' only.
    :type species: str

    Yield file content line by line (otherwise 1 file is too large and overload my computer).

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
                count = 0
                for line in my_file:
                    count += 1
                    if count == 1:
                        header = line.decode("utf-8").replace("\n", "").split("\t")
                        continue

                    parsed_data = line.decode("utf-8").replace("\n", "").split("\t")

                    if len(parsed_data) > 1 and species in parsed_data[1]:
                        to_insert_dict = {}
                        for key in header:
                            to_insert_dict[key] = parsed_data[header.index(key)]

                        yield to_insert_dict

                    else:
                        continue


if __name__ == '__main__':
    # Start execution timing
    startTime = datetime.now()

    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set project config
    config = utilities.extract_config()

    # Set variables
    dir_name = config["TARGETSCAN"]["SAVE FILE TO"]
    urls = [config["TARGETSCAN"]["URL_0"], config["TARGETSCAN"]["URL_1"]]

    # Prepare local file paths
    wanted_files = []
    for url in urls:
        file_name = url.split("/")[-1]
        file_name = os.path.join(dir_name, file_name)
        wanted_files.append(file_name)

    # Check that file was not already downloaded
    download_tag = utilities.check_files_presence(files_list=wanted_files)

    # Download
    if download_tag:
        # If so, do you wish to download it anyway?
        if click.confirm("The files you wish to download already exists on your system. "
                         "Do you still wish to download them anyway?", default=False):
            # If user answer 'yes' then I need to download all files.
            download_tag = False

    if not download_tag:
        for url in urls:
            try:
                utilities.download(url, wanted_files[urls.index(url)])

            except Exception as e:
                logging.error("Download issue: {}".format(e))
                sys.exit("Run aborted.")

    # Truncating table data content?
    if click.confirm("Do you wish to TRUNCATE Targetscan table content "
                     "before inserting data?", default=True):
        utilities.truncate_table(config, table="Targetscan")

    # Data post-processing before DB insert
    logging.info("Post-processing and inserting data in Targetscan table...")
    for file in wanted_files:
        predictions_list = []

        for insert_dict in read_txt_zip_file(filename=file, species="hsa"):
            predictions_list.append(insert_dict)

            if len(predictions_list) > 1000:
                query = "INSERT INTO Targetscan (MirName, GeneID, GeneSymbol, ContextScore, WeightedContextScore) " \
                        "VALUES (%(miRNA)s, %(Gene ID)s, %(Gene Symbol)s, %(context++ score)s, " \
                        "%(weighted context++ score)s);"
                connection = utilities.mysql_connection(config)
                cursor = connection.cursor()
                cursor.executemany(query, predictions_list)
                connection.commit()
                connection.close()
                predictions_list = []

        logging.info("{} / {} file(s) done !".format(wanted_files.index(file) + 1, len(wanted_files)))

    logging.info("Run completed.")
    logging.info("Execution time: {}".format(datetime.now() - startTime))

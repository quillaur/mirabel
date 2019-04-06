# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 07/04/2019
# Purpose: Get raw data from miranda website

import logging
import sys
import click
import zipfile
import os
import gzip

# Personal imports
import utilities


def read_txt_gzip_file(filename: str, species: str):
    """
    Open and reformat data from txt.gz file to insert into mysql.
    :param filename: name of file to open.
    :type filename: str
    :param species: which species to keep.
    :type species: str

    Yield file content line by line (otherwise 1 file is too large and overload my computer).
    """
    with gzip.open(filename, "r") as my_txt:
        count = 0
        for line in my_txt:
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
    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set project config
    config = utilities.extract_config()

    # Set variables
    dir_name = config["MIRANDA"]["SAVE FILE TO"]
    urls = [config["MIRANDA"]["URL_0"], config["MIRANDA"]["URL_1"],
            config["MIRANDA"]["URL_2"], config["MIRANDA"]["URL_3"]]

    # Prepare local file paths
    wanted_files = []
    for url in urls:
        file_name = url.split("/")[-1]
        file_name = os.path.join(dir_name, file_name)
        wanted_files.append(file_name)

    # Check that file was not already downloaded
    download_tag = utilities.check_files_presence(files_list=wanted_files)

    if download_tag:
        # If so, do you wish to download it anyway?
        if not click.confirm("The files you wish to download already exists on your system. "
                             "Do you still wish to download them anyway?", default=False):
            download_tag = False

        if download_tag:
            for url in urls:
                try:
                    utilities.download(url, wanted_files[urls.index(url)])

                except Exception as e:
                    logging.error("Download issue: {}".format(e))
                    sys.exit("Run aborted.")

    # Truncating Miranda data content?
    connection = utilities.mysql_connection(config)
    if click.confirm("Do you wish to TRUNCATE Miranda table content "
                     "before inserting data?", default=True):
        logging.info("Truncating Miranda table...")
        query = "TRUNCATE TABLE Miranda;"
        cursor = connection.cursor()
        cursor.execute(query)

    # Data post-processing before DB insert
    logging.info("Post-processing and inserting data in Miranda table...")
    for file in wanted_files[:2]:
        predictions_list = []

        for insert_dict in read_txt_gzip_file(filename=file, species="hsa"):
            predictions_list.append(insert_dict)

            if len(predictions_list) > 1000:
                # Insert in mysql
                query = "INSERT INTO Miranda (MirName, GeneID, GeneSymbol, MirsvrScore) " \
                        "VALUES (%(mirna_name)s, %(gene_id)s, %(gene_symbol)s, %(mirsvr_score)s);"
                connection = utilities.mysql_connection(config)
                cursor = connection.cursor()
                cursor.executemany(query, predictions_list)
                connection.commit()
                connection.close()
                predictions_list = []

        logging.info("{} / 4 file(s) done !".format(wanted_files.index(file) + 1))

    logging.info("Run completed.")

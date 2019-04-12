# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 07/04/2019
# Purpose: Get raw data from miranda website

import logging
import sys
import click
import os
import gzip
from datetime import datetime
import argparse

# Personal imports
import utilities
from downloader import Downloader


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
    # Start execution timing
    startTime = datetime.now()

    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set project config
    config = utilities.extract_config()

    # Set variables
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action="store_true", help="If -d present: download all files, else don't.")
    args = parser.parse_args()

    if args.d:
        # Launch download (db_name must be spelled the same way as in your config !)
        downloader = Downloader(db_name="MIRANDA")
        downloader.run()

    # # Truncating Miranda data content?
    # connection = utilities.mysql_connection(config)
    # if click.confirm("Do you wish to TRUNCATE Miranda table content "
    #                  "before inserting data?", default=True):
    #     logging.info("Truncating Miranda table...")
    #     query = "TRUNCATE TABLE Miranda;"
    #     cursor = connection.cursor()
    #     cursor.execute(query)
    #
    # # Data post-processing before DB insert
    # logging.info("Post-processing and inserting data in Miranda table...")
    # for file in wanted_files:
    #     predictions_list = []
    #
    #     for insert_dict in read_txt_gzip_file(filename=file, species="hsa"):
    #         predictions_list.append(insert_dict)
    #
    #         if len(predictions_list) > 1000:
    #             # Insert in mysql
    #             query = "INSERT INTO Miranda (MirName, GeneID, GeneSymbol, MirsvrScore) " \
    #                     "VALUES (%(mirna_name)s, %(gene_id)s, %(gene_symbol)s, %(mirsvr_score)s);"
    #             connection = utilities.mysql_connection(config)
    #             cursor = connection.cursor()
    #             cursor.executemany(query, predictions_list)
    #             connection.commit()
    #             connection.close()
    #             predictions_list = []
    #
    #     logging.info("{} / {} file(s) done !".format(wanted_files.index(file) + 1, len(wanted_files)))
    #
    # logging.info("Run completed.")
    # logging.info("Execution time: {}".format(datetime.now() - startTime))

# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 23/04/2019
# Purpose: Create a module to do statistical analysis of aggregated data.

import logging
import subprocess
import csv
from ast import literal_eval
from progressbar import *

# Personal imports
from scripts import utilities
from scripts.updater import Updater

class Rocker:
    """
    General class to aggregate all wanted data.
    """
    def __init__(self, db_list: list, db_compare: list):
        """
        Aggregator init.

        :param db_list: list of databases from which to aggregate predictions
        :param db_compare: list of databases with which you wish to compare aggregated data
        """
        # Get logging module from main script
        self.logger = logging.getLogger(__name__)

        # Set project config
        self.config = utilities.extract_config()

        # Variables
        self.ascendant = ["Targetscan", "Miranda", "Pita", "Mirmap"]
        self.db_list = db_list
        self.db_compare = db_compare
        self.all_db = self.db_list + self.db_compare

    def get_common_mirnas(self):
        logging.info("Getting all miRNAs between these databases: {}...".format(self.all_db))
        db_mirs_lists = [utilities.get_mirnas(self.config, db) for db in self.all_db]

        logging.info("Intersecting common miRNAs ...")
        common_mirnas = list(set(db_mirs_lists[0]).intersection(*db_mirs_lists))

        return common_mirnas

    def write_tmp_predictions_to_file(self, filename: str, predictions_lists: list):
        # Write results temporary in CSV so as to be aggregated with R
        with open(filename, "w") as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=";")
            csv_writer.writerow("score", "label")
            max_size = max([len(sublist) for sublist in predictions_lists])
            i = 0
            while i < max_size:
                to_write_list = []
                for sublist in predictions_lists:
                    try:
                        to_write_list.append(sublist[i])
                    except IndexError:
                        to_write_list.append(None)

                csv_writer.writerow(to_write_list)
                i += 1

    def make_rocs(self):
        # Aggregate with R RobustRankAggreg
        subprocess.call("scripts/aggregation.r")

    def get_labels(self):
        query = "SELECT "
        connection = utilities.mysql_connection(self.config)

    def run(self):
        # Truncate Mirabel table
        utilities.truncate_table(self.config, "Mirabel")

        # Get common mirnas between all aggregated DB
        common_mirnas = self.get_common_mirnas()
        logging.info("Making roc curves for given databases...")

        # Pre-process data for each DB for each miRNAs
        for db in self.all_db:
            order = "ASC" if db in self.ascendant else "DESC"

            widgets = ['Test: ', Percentage(), ' ', Bar(marker='0',left='[',right=']'),
               ' ', ETA(), ' ', FileTransferSpeed()] #see docs for other options
            pbar = ProgressBar(widgets=widgets, maxval=len(common_mirnas))
            pbar.start()
            i = 0
            for mirna in common_mirnas:
                i += 1
                pbar.update(i)
                scores_list = utilities.get_predictions_for_mirna(self.config, db, mirna, order, elem="Score")
                labels_list = self.get_labels()
                self.write_tmp_predictions_to_file(self.config["FILES"]["TMP_PREDICTIONS"], predictions_lists)
            pbar.finish()

        self.make_rocs()

        logging.info("Rock analysis done.")
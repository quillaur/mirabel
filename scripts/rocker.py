# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 23/04/2019
# Purpose: Create a module to do statistical analysis of aggregated data.

import os
import logging
import subprocess
import csv
from ast import literal_eval
from progressbar import *
from collections import defaultdict

# Personal imports
from scripts import utilities
from scripts.updater import Updater

class Rocker:
    """
    General class to aggregate all wanted data.
    """
    def __init__(self, db_main: str, db_compare: str):
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
        self.ascendant = ["Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel"]
        self.db_main = db_main
        self.db_comp = db_compare
        self.all_db = [db_main, db_compare]
        self.ascendant.append(self.db_main)

    def get_common_mirnas(self):
        logging.info("Getting all miRNAs between these databases: {}...".format(self.all_db))
        db_mirs_lists = [utilities.get_mirnas(self.config, db) for db in self.all_db]

        logging.info("Intersecting common miRNAs ...")
        common_mirnas = list(set(db_mirs_lists[0]).intersection(*db_mirs_lists))

        return common_mirnas

    def write_tmp_roc_data_to_file(self, filename: str, scores_dict: dict):
        # Write results temporary in CSV so as to be aggregated with R
        with open(filename, "w") as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=";")
            csv_writer.writerow(["score", "label"])
            for mimat in scores_dict:
                for gene_id in scores_dict[mimat]:
                    csv_writer.writerow([scores_dict[mimat][gene_id]["Score"], scores_dict[mimat][gene_id]["Validated"]])

    def make_rocs(self):
        # Aggregate with R RobustRankAggreg
        subprocess.call("scripts/rocker.r")

    def get_scores_and_labels(self, db: str, mirna_list: list):
        order = "ASC" if db in self.ascendant else "DESC"
        mirna_list = ", ".join([str(mirna_id) for mirna_id in mirna_list])
        query = """SELECT Score, Validated, GeneID, Mimat FROM {} WHERE Mimat IN ({}) ORDER BY Score {};""".format(db, mirna_list, order)
        connection = utilities.mysql_connection(self.config)
        cursor = connection.cursor()
        cursor.execute(query)
        # results_list = [[row[0], row[1], row[2]] for row in cursor]
        results_dict = defaultdict(dict)
        for row in cursor:
            results_dict[row[3]][row[2]] = {
                "Score": row[0],
                "Validated": row[1]
            }
        connection.close()

        return results_dict

    def run(self):
        # Get common mirnas between all aggregated DB
        common_mirnas = self.get_common_mirnas()

        if common_mirnas:
            # Pre-process data for each DB for each miRNAs
            scores_dict = {}
            for db in self.all_db:
                logging.info("Getting scores and labels for {}...".format(db))
                scores_dict[db] = self.get_scores_and_labels(db, common_mirnas)

            reformated_scores_dict = {}
            for db in self.all_db:
                # Get list of other DB
                other_db = [db_name for db_name in self.all_db if db_name != db]
                logging.info("Intersecting common interactions for {}...".format(db))
                # widgets = ['Data processing: ', Percentage(), ' ', Bar(marker='0',left='[',right=']'),
                #    ' ', ETA(), ' ', FileTransferSpeed()] #see docs for other options
                # pbar = ProgressBar(widgets=widgets, maxval=len(scores_dict[db]))
                # pbar.start()
                # i = 0
                # For each mirna in the db
                reformated_scores_dict[db] = defaultdict(dict)
                count = 0
                count_val = 0
                for mimat in scores_dict[db]:
                    # i += 1
                    # pbar.update(i)
                    # For each gene in the db
                    for gene_id in scores_dict[db][mimat]:
                        # Check presence in each other db to compare
                        for db_comp in other_db:
                            if gene_id in scores_dict[db_comp][mimat]:
                                reformated_scores_dict[db][mimat][gene_id] = {
                                    "Score": scores_dict[db][mimat][gene_id]["Score"],
                                    "Validated": scores_dict[db][mimat][gene_id]["Validated"]
                                }
                                count += 1 

                                if scores_dict[db][mimat][gene_id]["Validated"] == '1':
                                    count_val += 1

                                break
                # pbar.finish()
                logging.info("{} common interactions found for {}.".format(count, db))
                logging.info("Within these common interactions, {} are validated ones.".format(count_val))
                logging.info("Writing scores and labels for {}...".format(db))
                filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_tmp_roc_data.txt".format(db))
                self.write_tmp_roc_data_to_file(filename, reformated_scores_dict[db])

            self.make_rocs()

            logging.info("Rock analysis done.")

            return True
        return False

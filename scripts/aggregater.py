# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 12/04/2019
# Purpose: Create a module to aggregate miRna target predictions between selected databases.

import logging
import subprocess
import csv
from ast import literal_eval
from progressbar import *

# Personal imports
from scripts import utilities
from scripts.updater import Updater

class Aggregator:
    """
    General class to aggregate all wanted data.
    """
    def __init__(self, db_list: list):
        """
        Aggregator init.

        :param db_list: list of databases from which to aggregate predictions
        """
        # Get logging module from main script
        self.logger = logging.getLogger(__name__)

        # Set project config
        self.config = utilities.extract_config()

        # Variables
        self.ascendant = ["Targetscan", "Miranda", "Pita", "Mirmap"]
        self.db_list = db_list
        self.validated_interactions = utilities.get_validated_interactions(self.config)

    def get_mirnas_for_each_db(self):
        logging.info("Getting all miRNAs for these databases: {}...".format(self.db_list))
        db_mirs_lists = [utilities.get_mirnas(self.config, db) for db in self.db_list]

        filename = "resources/tmp_mirna_list.txt"
        with open(filename, "w") as my_txt:
            my_txt.write(str(db_mirs_lists))

        with open(filename, "r") as my_file:
            handle = my_file.read()
            db_mirs_lists = literal_eval(handle)

        logging.info("Intersecting common miRNAs ...")
        all_mirnas = list(set([mir for mir_group in db_mirs_lists for mir in mir_group]))

        return all_mirnas

    def get_predictions(self, mirna: int):
        results_list_of_lists = []
        for db in self.db_list:
            order = "ASC" if db in self.ascendant else "DESC"
            predictions_list = utilities.get_predictions_for_mirna(self.config, db, mirna, order)
            results_list_of_lists.append(predictions_list)

        return results_list_of_lists

    def write_tmp_predictions_to_file(self, filename: str, predictions_lists: list):
        # Write results temporary in CSV so as to be aggregated with R
        with open(filename, "w") as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=";")
            csv_writer.writerow(self.db_list)
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

    def make_aggregation(self):
        # Aggregate with R RobustRankAggreg
        subprocess.call("scripts/aggregation.r")

    def get_aggregation_results(self, mirna):
        with open(self.config["FILES"]["TMP_AGGREGATIONS"], "r") as my_txt:
            handle = my_txt.read()
            content = handle.split("\n")
            # Remove headers
            del content[0]

            to_insert_list = []
            for row in content:
                data = row.split("\t") if row else ""
                if data:
                   to_insert_dico = {
                   "Mimat": mirna, 
                   "gene_id": int(data[0]), 
                   "score": data[1],
                   "validated": "1" if int(data[0]) in self.validated_interactions[mirna] else "0"
                   }
                   to_insert_list.append(to_insert_dico)
        
        return to_insert_list

    def update_mirabel(self, mirna):
        to_insert_list = self.get_aggregation_results(mirna)
        # Insert aggregated data in base
        updater = Updater(db_name="Mirabel")
        updater.insert_into_db(to_insert_list)

    def run(self):
        # Truncate Mirabel table
        utilities.truncate_table(self.config, "Mirabel")

        # Get common mirnas between all aggregated DB
        all_mirnas = self.get_mirnas_for_each_db()
        logging.info("Aggregating predictions between given databases...")

        # Make aggregation for each miRNAs
        widgets = ['Test: ', Percentage(), ' ', Bar(marker='0',left='[',right=']'),
           ' ', ETA(), ' ', FileTransferSpeed()] #see docs for other options
        pbar = ProgressBar(widgets=widgets, maxval=len(all_mirnas))
        pbar.start()
        i = 0
        for mirna in all_mirnas:
            i += 1
            pbar.update(i)
            predictions_lists = self.get_predictions(mirna)
            self.write_tmp_predictions_to_file(self.config["FILES"]["TMP_PREDICTIONS"], predictions_lists)
            self.make_aggregation()
            self.update_mirabel(mirna)
        pbar.finish()

        logging.info("Aggregation done.")
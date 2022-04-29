# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 12/04/2019
# Purpose: Create a module to aggregate miRna target predictions between selected databases.

import logging
import subprocess
import csv
from ast import literal_eval
from progressbar import *
import os
from operator import itemgetter

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
        self.ascendant = ["Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel", "Rna22"]
        self.db_list = db_list
        self.validated_interactions = utilities.get_validated_interactions(self.config)

    def get_mirnas_for_each_db(self):
        logging.info("Getting all miRNAs for these databases: {}...".format(self.db_list))
        db_mirs_lists = [utilities.get_mirnas(self.config, db) for db in self.db_list]

        all_mirnas = list(set([mir for mir_group in db_mirs_lists for mir in mir_group]))

        # # Keep only common miRNAs to all DB
        # all_common_mirnas  = []
        # for mirna in all_mirnas:
        #     keep_in = True
        #     for indice, value in enumerate(db_mirs_lists):
        #         if mirna not in db_mirs_lists[indice]:
        #             keep_in = False

        #     if keep_in:
        #         all_common_mirnas.append(mirna)

        ##### For test purpose #####
        # filename = "resources/tmp_mirna_list.txt"
        # with open(filename, "w") as my_txt:
            # my_txt.write(str(all_common_mirnas))

        # with open(filename, "r") as my_file:
        #     handle = my_file.read()
        #     all_common_mirnas = literal_eval(handle)

        return all_mirnas

    def get_predictions(self, mirna: int):
        results_list_of_lists = []
        for db in self.db_list:
            predictions_list = utilities.get_predictions_for_mirna(self.config, db, mirna)

            if predictions_list:
                # Sort by score write results to file
                if db in self.ascendant or "Mirabel" in db:
                    order = False 
                else: 
                    order = True 
                predictions_list = sorted(predictions_list, key=itemgetter(1), reverse=order)
                results_list_of_lists.append([elem[0] for elem in predictions_list])

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

    def update_mirabel(self, mirna, db_name):
        to_insert_list = self.get_aggregation_results(mirna)
        # Insert aggregated data in base
        updater = Updater(db_name=db_name)
        updater.insert_into_db(to_insert_list)

    def run(self, db_name):
        # Truncate Mirabel table
        utilities.truncate_table(self.config, db_name)

        # Create resources directory if it does not already exists
        if not os.path.isdir(self.config["FILES"]["RESOURCES"]):
            os.makedirs(self.config["FILES"]["TMP_ROC_DATA"])
            os.makedirs(self.config["FILES"]["TMP_RANDOM_SETS"])
            os.makedirs(self.config["FILES"]["PERM_COMPARISONS"])
            os.makedirs(self.config["FILES"]["PERM_IMAGES"])

        # Get common mirnas between all aggregated DB
        all_mirnas = self.get_mirnas_for_each_db()
        logging.info("{} miRNAs fetched.".format(len(all_mirnas)))
        logging.info("Aggregating predictions between given databases...")

        # Make aggregation for each miRNAs
        widgets = ['Aggregation: ', Percentage(), ' ', Bar(marker='0',left='[',right=']'),
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
            self.update_mirabel(mirna, db_name)
        pbar.finish()

        # Add this new miRabel to tracking table
        utilities.insert_to_existing_mirabels(db_name, self.db_list)

        logging.info("Aggregation done.")
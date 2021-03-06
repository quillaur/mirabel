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
import random
from shutil import move
from operator import itemgetter
from progressbar import ProgressBar

# Personal imports
from scripts import utilities
from scripts.updater import Updater

class Rocker:
    """
    General class to aggregate all wanted data.
    """
    def __init__(self, db_main: str, db_compare: list):
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
        self.ascendant = ["Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel", "Rna22"]
        self.db_main = db_main
        self.db_comp = db_compare
        self.all_db = [db_main]
        self.all_db.extend(self.db_comp)
        self.ascendant.append(self.db_main)

    def write_tmp_roc_data_to_file(self, filename: str, interactions: list):
        # Write results temporary in CSV so as to be aggregated with R
        with open(filename, "w") as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=";")
            csv_writer.writerow(["score", "label", "precision", "recall", "f_score"])
            for interaction in interactions:
                csv_writer.writerow(interaction)

    def make_rocs(self):
        subprocess.call("scripts/rocker.r")
        subprocess.call("scripts/random_rocker.r")

    def make_pr(self):
        subprocess.call("scripts/precis_recall.r")
        # subprocess.call("scripts/random_pr.r")

    def get_scores_and_labels(self, db: str, mirna_list: list):
        mirna_list = ", ".join([str(mirna_id) for mirna_id in mirna_list])
        query = """SELECT Score, Validated, GeneID, Mimat FROM {} WHERE Mimat IN ({});""".format(db, mirna_list)
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

    def make_sub_datasets(self, common_mirnas: list, reformated_scores_dict: dict, db_name: str):
        # Make 10 random sub-sets of 50k interactions
        sub = 0
        filenames = []
        while sub < 10:
            sub_dict = {db_name: defaultdict(dict)}
            for db in self.db_comp:
                sub_dict[db] = defaultdict(dict)

            c = 0
            validate_numb = 0
            while c < 50000:
                for mimat in common_mirnas:
                    if mimat in reformated_scores_dict[db_name]:
                        gene_id_list = list(reformated_scores_dict[db_name][mimat].keys())
                        gene_id = random.choice(gene_id_list)
                        sub_dict[db_name][mimat][gene_id] = {
                                "Score": reformated_scores_dict[db_name][mimat][gene_id]["Score"],
                                "Validated": reformated_scores_dict[db_name][mimat][gene_id]["Validated"]
                            }

                        # Get the same interaction for all other compared DB
                        for db in self.db_comp:
                            sub_dict[db][mimat][gene_id] = {
                                "Score": self.scores_dict[db][mimat][gene_id]["Score"],
                                "Validated": self.scores_dict[db][mimat][gene_id]["Validated"]
                            }

                        c += 1

                        if sub_dict[db_name][mimat][gene_id]["Validated"] == "1":
                            validate_numb += 1

            print("Number of val interactions in this sub-dataset: {}".format(validate_numb))
            sub += 1

            # Sort by score write results to file
            for db in self.all_db:
                order = False if db in self.ascendant or "Mirabel" in db else True
                lol_interactions = self.sort_by_score(sub_dict[db], descending=order)
                # compute precision / recall / f-score
                lol_interactions = self.compute_precision_recall(lol_interactions)
                # Write results to file
                filename = os.path.join(self.config["FILES"]["TMP_RANDOM_SETS"], "{}_tmp_random_set_{}.txt".format(db, sub))
                # if db == self.db_main:
                #     filename = os.path.join(self.config["FILES"]["TMP_RANDOM_SETS"], "{}_main_tmp_random_set_{}.txt".format(db, sub))
                # else:
                #     filename = os.path.join(self.config["FILES"]["TMP_RANDOM_SETS"], "{}_comp_tmp_random_set_{}.txt".format(db, sub))
                self.write_tmp_roc_data_to_file(filename, lol_interactions)
                filenames.append(filename)

        return filenames

    def compute_precision_recall(self, interactions: list):
        # Calculate precision for each interaction
        logging.info("Compute precision...")
        # widgets = ['Data processing: ', Percentage(), ' ', Bar(marker='0',left='[',right=']'),
        #    ' ', ETA(), ' ', FileTransferSpeed()] #see docs for other options
        # pbar = ProgressBar(widgets=widgets, maxval=len(interactions))
        # pbar.start()
        # i = 0
           
        count_val = 0
        for indice, interaction in enumerate(interactions):
            if interaction[1] == 1:
                count_val += 1

            # Precision
            precision = count_val/(indice+1)
            interaction.append(precision)
            
        #     i += 1
        #     pbar.update(i)
        # pbar.finish()

        # Compute recall for each interaction
        logging.info("Compute recall and f-score...")
        # pbar = ProgressBar(widgets=widgets, maxval=len(interactions))
        # pbar.start()
        # i = 0

        count_val_2 = 0
        for indice, interaction in enumerate(interactions):
            if interaction[1] == 1:
                count_val_2 += 1
            
            # Recall
            recall = count_val_2 / count_val
            interaction.append(recall)

            # Compute f_score
            if interaction[3] > 0:
                f_score = 2 * ((interaction[2] * interaction[3]) / (interaction[2] + interaction[3]))
                interaction.append(f_score)
            else:
                interaction.append(0)

        #     i += 1
        #     pbar.update(i)
        # pbar.finish()

        return interactions

    def sort_by_score(self, scores_dict: dict, descending: bool):
        # Make a list of tuples from given interactions
        lol_interactions = []
        for mimat in scores_dict:
            for gene_id in scores_dict[mimat]:
                lol_interactions.append([float(scores_dict[mimat][gene_id]["Score"]), int(scores_dict[mimat][gene_id]["Validated"])])
                    
        # Sort results by score
        lol_interactions = sorted(lol_interactions, key=itemgetter(0), reverse=descending)

        # Limit to 1M interactions because of computer resources (on PR AUC calculation)
        lol_interactions = lol_interactions[:750000]

        return lol_interactions

    def move_files(self, ori_dir: str, dest_dir, file_type: str):
        if file_type == "data":
            all_stats = [stat for stat in os.listdir(ori_dir) if os.path.isfile(os.path.join(ori_dir, stat)) and "results" in stat]
        else:
            all_stats = [stat for stat in os.listdir(ori_dir) if os.path.isfile(os.path.join(ori_dir, stat))]

        for stat in all_stats:
            src = os.path.join(ori_dir, stat)
            if os.path.isfile(src):
                dst = os.path.join(dest_dir, stat)
                logging.info("Moving {}".format(src))
                move(src, dst)
            else:
                logging.error("File NOT found: {}".format(src))

    def run(self):
        # Check if dir exists
        formated_comp_db = "_".join(self.db_comp)
        perm_data_dir = os.path.join(self.config["FILES"]["PERM_COMPARISONS"], "{}_vs_{}".format(self.db_main, formated_comp_db))
        if os.path.isdir(perm_data_dir):
            return True
        else:
            # Get common mirnas between all aggregated DB
            common_extrinsic_mirnas = utilities.get_common_mirnas(self.all_db)
            if "Mirabel" in self.db_main:
                mirab_intrinsic_mirnas = utilities.get_common_intrinsic_mirnas(self.db_main)
                common_mirnas = list(set(mirab_intrinsic_mirnas) & set(common_extrinsic_mirnas))
            else:
                common_mirnas = common_extrinsic_mirnas

            print("{} common mirnas found".format(len(common_mirnas)))
            print("Taking only the first 1k".format(len(common_mirnas)))
            common_mirnas = common_mirnas[:1000]

            # Create a permanent directory to store this comparison
            perm_img_dir = os.path.join(self.config["FILES"]["PERM_IMAGES"], "{}_vs_{}".format(self.db_main, formated_comp_db))
            directories = [perm_data_dir, perm_img_dir]
        
            try:
                for directory in directories:
                    os.mkdir(directory)
            except OSError:  
                print("Creation of the directory {} failed".format(directory))
            else:  
                print("Successfully created the directory {}".format(directory))

        if common_mirnas:
            # Pre-process data for each DB for each miRNAs
            self.scores_dict = {}
            for db in self.all_db:
                logging.info("Getting scores and labels for {}...".format(db))
                self.scores_dict[db] = self.get_scores_and_labels(db, common_mirnas)

            common_genes = defaultdict(list)
            logging.info("Intersecting common interactions for {}...".format(self.all_db))

            reformated_scores_dict = {self.db_main: defaultdict(dict)}
            count = 0
            count_val = 0
            for mimat in common_mirnas:
                # For each gene in the db
                for gene_id in self.scores_dict[self.db_main][mimat]:
                    add_in = True
                    # Check presence in each other db to compare
                    for db_comp in self.db_comp:
                        if gene_id not in self.scores_dict[db_comp][mimat]:
                            add_in = False

                    if add_in:
                        common_genes[mimat].append(gene_id)
                        reformated_scores_dict[self.db_main][mimat][gene_id] = {
                                "Score": self.scores_dict[self.db_main][mimat][gene_id]["Score"],
                                "Validated": self.scores_dict[self.db_main][mimat][gene_id]["Validated"]
                            }
                        count += 1 

                        if self.scores_dict[self.db_main][mimat][gene_id]["Validated"] == '1':
                            count_val += 1

            # Sort by score write results to file
            logging.info("{} common interactions found for {}.".format(count, self.all_db))
            logging.info("Within these common interactions, {} are validated ones.".format(count_val))
            if count > 750000:
                logging.warning("Due to resource limitations, only the first 500K interactions will be used for comparison.")
            logging.info("Sort interactions by score...")
            lol_interactions = self.sort_by_score(reformated_scores_dict[self.db_main], descending=False)
            # compute precision / recall / f-score
            lol_interactions = self.compute_precision_recall(lol_interactions)
            # write results to file
            logging.info("Writing scores and labels for {}...".format(self.db_main))
            filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_tmp_roc_data.txt".format(self.db_main))
            # filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_main_tmp_roc_data.txt".format(self.db_main))
            # perm_filename = os.path.join(perm_data_dir, "{}_roc_data.txt".format(self.db_main))
            self.write_tmp_roc_data_to_file(filename, lol_interactions)
            # self.write_tmp_roc_data_to_file(perm_filename, reformated_scores_dict[self.db_main])

            logging.info("Making random sub-sets for {}...".format(self.db_main))
            filenames = self.make_sub_datasets(common_mirnas, reformated_scores_dict, self.db_main)
            filenames.append(filename)

            reformated_scores_dict = {}
            for db in self.db_comp:
                # For each mirna in the db
                reformated_scores_dict[db] = defaultdict(dict)
                for mimat in common_mirnas:
                    for gene_id in common_genes[mimat]:
                        reformated_scores_dict[db][mimat][gene_id] = {
                                        "Score": self.scores_dict[db][mimat][gene_id]["Score"],
                                        "Validated": self.scores_dict[db][mimat][gene_id]["Validated"]
                                    }
                
                # Sort by score write results to file
                order = False if db in self.ascendant or "Mirabel" in db else True
                lol_interactions = self.sort_by_score(reformated_scores_dict[db], descending=order)
                # compute precision / recall / f-score
                lol_interactions = self.compute_precision_recall(lol_interactions)
                # write results to file
                logging.info("Writing scores and labels for {}...".format(db))
                filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_tmp_roc_data.txt".format(db))
                # filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_comp_tmp_roc_data.txt".format(db))
                # perm_filename = os.path.join(perm_data_dir, "{}_roc_data.txt".format(db))
                self.write_tmp_roc_data_to_file(filename, lol_interactions)
                # self.write_tmp_roc_data_to_file(perm_filename, reformated_scores_dict[db])

                # logging.info("Making random sub-sets for {}...".format(db))
                # filenames_1 = self.make_sub_datasets(common_mirnas, reformated_scores_dict, db)
                # filenames_1.append(filename)
                
                # if not self.all_in_one:
                #     self.make_rocs()
                #     self.make_pr()
                #     self.move_files(ori_dir=self.config["FILES"]["RESOURCES"], dest_dir=perm_data_dir, file_type="data")
                #     self.move_files(ori_dir="static/", dest_dir=perm_img_dir, file_type="img")

                    # Remove files so as not to create issue with the next comparison
                    # for filename in filenames_1:
                    #     if os.path.isfile(filename):
                    #         logging.info("Removing {}".format(filename))
                    #         os.remove(filename)

            # if self.all_in_one:
            self.make_rocs()
            self.make_pr()
            self.move_files(ori_dir=self.config["FILES"]["RESOURCES"], dest_dir=perm_data_dir, file_type="data")
            self.move_files(ori_dir="static/", dest_dir=perm_img_dir, file_type="img")
                
                # filenames.extend(filenames_1)

            # for filename in filenames:
            #     if os.path.isfile(filename):
            #         logging.info("Removing {}".format(filename))
            #         os.remove(filename)

            logging.info("Rock analysis done.")

            return True
        return False

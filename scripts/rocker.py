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
from shutil import copyfile

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
        self.ascendant = ["Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel"]
        self.db_main = db_main
        self.db_comp = db_compare
        self.all_db = [db_main]
        self.all_db.extend(self.db_comp)
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
        subprocess.call("scripts/rocker.r")
        subprocess.call("scripts/random_rocker.r")

    def make_pr(self):
        subprocess.call("scripts/precis_recall.r")
        subprocess.call("scripts/random_pr.r")

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

    def make_sub_datasets(self, common_mirnas: list, reformated_scores_dict: dict, db_name: str):
        # Make 10 random sub-sets of 50k interactions
        sub = 0
        filenames = []
        while sub < 10:
            sub_dict = {db_name: defaultdict(dict)}
            c = 0
            while c < 50000:
                for mimat in common_mirnas:
                    if mimat in reformated_scores_dict[db_name]:
                        gene_id_list = list(reformated_scores_dict[db_name][mimat].keys())
                        gene_id = random.choice(gene_id_list)
                        sub_dict[db_name][mimat][gene_id] = {
                                "Score": reformated_scores_dict[db_name][mimat][gene_id]["Score"],
                                "Validated": reformated_scores_dict[db_name][mimat][gene_id]["Validated"]
                            }
                        c += 1

            sub += 1
            filename = os.path.join(self.config["FILES"]["TMP_RANDOM_SETS"], "{}_tmp_random_set_{}.txt".format(db_name, sub))
            self.write_tmp_roc_data_to_file(filename, sub_dict[db_name])
            filenames.append(filename)

        return filenames

    def run(self):
        # Check if dir exists
        formated_comp_db = "_".join(self.db_comp)
        perm_data_dir = os.path.join(self.config["FILES"]["PERM_COMPARISONS"], "{}_vs_{}".format(self.db_main, formated_comp_db))
        if os.path.isdir(perm_data_dir):
            return True
        else:
            # Get common mirnas between all aggregated DB
            common_mirnas = utilities.get_common_mirnas(self.all_db)

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
            scores_dict = {}
            for db in self.all_db:
                logging.info("Getting scores and labels for {}...".format(db))
                scores_dict[db] = self.get_scores_and_labels(db, common_mirnas)

            common_genes = defaultdict(list)
            logging.info("Intersecting common interactions for {}...".format(self.all_db))

            reformated_scores_dict = {self.db_main: defaultdict(dict)}
            count = 0
            count_val = 0
            for mimat in common_mirnas[:5]:
                # For each gene in the db
                for gene_id in scores_dict[self.db_main][mimat]:
                    add_in = True
                    # Check presence in each other db to compare
                    for db_comp in self.db_comp:
                        if gene_id not in scores_dict[db_comp][mimat]:
                            add_in = False

                    if add_in:
                        common_genes[mimat].append(gene_id)
                        reformated_scores_dict[self.db_main][mimat][gene_id] = {
                                "Score": scores_dict[self.db_main][mimat][gene_id]["Score"],
                                "Validated": scores_dict[self.db_main][mimat][gene_id]["Validated"]
                            }
                        count += 1 

                        if scores_dict[self.db_main][mimat][gene_id]["Validated"] == '1':
                            count_val += 1

            logging.info("{} common interactions found for {}.".format(count, self.all_db))
            logging.info("Within these common interactions, {} are validated ones.".format(count_val))
            logging.info("Writing scores and labels for {}...".format(self.db_main))
            filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_tmp_roc_data.txt".format(self.db_main))
            # perm_filename = os.path.join(perm_data_dir, "{}_roc_data.txt".format(self.db_main))
            self.write_tmp_roc_data_to_file(filename, reformated_scores_dict[self.db_main])
            # self.write_tmp_roc_data_to_file(perm_filename, reformated_scores_dict[self.db_main])

            filenames = self.make_sub_datasets(common_mirnas, reformated_scores_dict, self.db_main)
            filenames.append(filename)

            reformated_scores_dict = {}
            for db in self.db_comp:
                # For each mirna in the db
                reformated_scores_dict[db] = defaultdict(dict)
                for mimat in common_mirnas[:5]:
                    for gene_id in common_genes[mimat]:
                        reformated_scores_dict[db][mimat][gene_id] = {
                                        "Score": scores_dict[db][mimat][gene_id]["Score"],
                                        "Validated": scores_dict[db][mimat][gene_id]["Validated"]
                                    }
            
                logging.info("Writing scores and labels for {}...".format(db))
                filename = os.path.join(self.config["FILES"]["TMP_ROC_DATA"], "{}_tmp_roc_data.txt".format(db))
                # perm_filename = os.path.join(perm_data_dir, "{}_roc_data.txt".format(db))
                self.write_tmp_roc_data_to_file(filename, reformated_scores_dict[db])
                # self.write_tmp_roc_data_to_file(perm_filename, reformated_scores_dict[db])

                filenames_1 = self.make_sub_datasets(common_mirnas, reformated_scores_dict, db)
                filenames_1.append(filename)
                
                self.make_rocs()

                all_stats = [stat for stat in os.listdir(self.config["FILES"]["RESOURCES"]) if os.path.isfile(os.path.join(self.config["FILES"]["RESOURCES"], stat)) and "results" in stat]
                for stat in all_stats:
                    src = os.path.join(self.config["FILES"]["RESOURCES"], stat)
                    if os.path.isfile(src):
                        dst = os.path.join(perm_data_dir, stat)
                        copyfile(src, dst)
                        os.remove(src)
                    else:
                        logging.error("File NOT found: {}".format(src))

                self.make_pr()

                # Copy images and stats results to permanent directory
                all_img = [img for img in os.listdir("static/") if os.path.isfile(os.path.join("static/", img))]
                for img in all_img:
                    src = os.path.join("static/", img)
                    if os.path.isfile(src):
                        dst = os.path.join(perm_img_dir, img)
                        copyfile(src, dst)
                        os.remove(src)
                    else:
                        logging.error("File NOT found: {}".format(src))

                # Remove files so as not to create issue with the next comparison
                for filename in filenames_1:
                    if os.path.isfile(filename):
                        os.remove(filename)

            logging.info("Rock analysis done.")

            for filename in filenames:
                if os.path.isfile(filename):
                    os.remove(filename)

            return True
        return False

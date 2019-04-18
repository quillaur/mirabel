# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 14/04/2019
# Purpose: Download and insert data from publicly available microRNA databases.

import logging
from datetime import datetime
import argparse
import sys
import csv

# Personal imports
from scripts import utilities
from scripts.downloader import Downloader
from scripts.updater import Updater


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
    parser.add_argument('-u', action="store_true", help="If -u present: update all files, else don't.")
    parser.add_argument('-l', '--list', nargs='*',
                        help='Pass a list of databases you wish to download or upload. Default is all.',
                        default=[])
    args = parser.parse_args()

    # db_name must start with a capitalized letter followed by non-capitalized letters
    # (same as the corresponding SQL tables).
    # By default, database is as followed.
    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Mirtarbase", "Mirecords", "Comir", "Mirmap", "Mirdb", "Mirwalk"]

    # Check database requested by user is available:
    is_in_list = True
    if args.list:
        for db in args.list:
            if db not in db_list:
                is_in_list = False
                break
        if not is_in_list:
            logging.warning("One or more requested database(s) in {} are not available for download / update.".format(args.list))
            logging.warning("Run aborted.")
            sys.exit(1)
        
        db_list = args.list

    if args.u:
        for db in db_list:
            logging.info("##############################")
            logging.info("########## {} ##########".format(db.upper()))
            logging.info("##############################")
            if args.d and not "Svmicro" in db and not "Mirecords" in db and not "Comir" in db:
                # Launch download
                downloader = Downloader(db_name=db.upper())
                downloader.run()
            
            # Update mysql DB
            updater = Updater(db_name=db)
            updater.run()

            logging.info("{} / {} Database(s) done !\n".format(db_list.index(db) + 1, len(db_list)))

    # Get common miRNAs
    logging.info("Getting all common miRNAs between {}...".format(db_list))
    db_mirs_lists = [utilities.get_mirnas(config, db) for db in db_list]
    common_mirnas = list(set(db_mirs_lists[0]).intersection(*db_mirs_lists))

    # Define how to rank predictions for DBs
    # SVmicro = descendant
    ascendant = ["Targetscan", "Miranda", "Pita"]
    # Make aggregation for each miRNAs
    for mirna in common_mirnas:
        # Get mirna data from DB
        results_list_of_lists = []
        for db in db_list:
            order = "ASC" if db in ascendant else "DESC"
            predictions_list = utilities.get_predictions_for_mirna(config, db, mirna, order)
            results_list_of_lists.append(predictions_list)

        # Write results temporary in CSV so as to be aggregated with R
        with open("resources/tmp_predictions_lists.csv", "w") as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=";")
            csv_writer.writerow(db_list)
            max_size = max([len(sublist) for sublist in results_list_of_lists])
            while i < max_size:
                to_write_list = []
                for sublist in results_list_of_lists:
                    try:
                        to_write_list.append(sublist[i])
                    except IndexError:
                        to_write_list.append(None)

                csv_writer.writerow(to_write_list)

        # Aggregate with R RobustRankAggreg
        
    logging.info("Run completed.")
    logging.info("Execution time: {}".format(datetime.now() - startTime))
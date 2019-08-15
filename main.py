# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 14/04/2019
# Purpose: Download and insert data from publicly available microRNA databases.

import logging
from datetime import datetime
import argparse
import sys

# Personal imports
from scripts import utilities
from scripts.downloader import Downloader
from scripts.updater import Updater
from scripts.aggregater import Aggregator
from scripts.rocker import Rocker


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
                        help='Pass the list of databases you wish to aggregate. Default is empty list (but all DB later).',
                        default=[])
    parser.add_argument('-lc', '--list-compare', nargs='*',
                        help='Pass the list of databases you wish to compare to the aggregated ones. Default is empty list.',
                        default=[])
    args = parser.parse_args()

    # db_name must start with a capitalized letter followed by non-capitalized letters
    # (same as the corresponding SQL tables).
    # By default, all databases are used.
    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Mirtarbase", "Mirecords", "Comir", "Mirmap", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget", "Rna22", "Mirdip"]

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

    logging.info("Run completed.")
    logging.info("Execution time: {}".format(datetime.now() - startTime))
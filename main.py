# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 14/04/2019
# Purpose: Download and insert data from publicly available microRNA databases.

import logging
from datetime import datetime
import argparse

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
    parser.add_argument('-l', '--list', nargs='*',
                        help='Pass a list of databases you wish to download or upload. Default is all.',
                        default=[])
    args = parser.parse_args()

    if not args.list:
        # db_name must start with a capitalized letter followed by non-capitalized letters
        # (same as the corresponding SQL tables).
        db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Mirtarbase"]
    else:
        db_list = args.list

    for db in db_list:
        logging.info("####################################################")
        logging.info("########## {} ##########".format(db.upper()))
        logging.info("####################################################")
        if args.d:
            # Launch download
            downloader = Downloader(db_name=db.upper())
            downloader.run()

        # Update mysql DB
        updater = Updater(db_name=db)
        updater.run()

        logging.info("{} / {} Database(s) done !\n".format(db_list.index(db) + 1, len(db_list)))

    logging.info("Run completed.")
    logging.info("Execution time: {}".format(datetime.now() - startTime))
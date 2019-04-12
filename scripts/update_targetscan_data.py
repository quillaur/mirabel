# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 20/03/2019
# Purpose: Get raw data from targetscan website

import logging
from datetime import datetime
import argparse

# Personal imports
import utilities
from downloader import Downloader
from updater import Updater


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
        downloader = Downloader(db_name="TARGETSCAN")
        downloader.run()

    # Update mysql DB
    updater = Updater(db_name="TARGETSCAN")
    updater.run()

    logging.info("Run completed.")
    logging.info("Execution time: {}".format(datetime.now() - startTime))

# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 11/04/2019
# Purpose: Get raw data from SVmicro website

import logging
from datetime import datetime

# Personal imports
import utilities
from updater import Updater


if __name__ == '__main__':
    # Start execution timing
    startTime = datetime.now()

    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set project config
    config = utilities.extract_config()

    # Update mysql DB
    updater = Updater(db_name="Svmicro")
    updater.run()

    logging.info("Run completed.")
    logging.info("Execution time: {}".format(datetime.now() - startTime))

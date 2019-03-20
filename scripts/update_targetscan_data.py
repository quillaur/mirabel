# Author: Aurélien Quillet
# Date: 20/03/2019
# Purpose: Get raw data from targetscan website

import logging
from requests import get  # to make GET request
import os.path
import sys


def download(url: str, file_name: str):
    """
    Download file from URL.
    :param url: address to get the file from.
    :param file_name: name of file to write downloaded data in.
    :return: None
    """
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        response = get(url)
        # write to file
        file.write(response.content)


if __name__ == '__main__':
    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set variables
    file_name = "/home/quillaur/github_projects/mirabel/targetscan/data_raw/conserved_site_context_scores.txt.zip"
    url = "http://www.targetscan.org/vert_72/vert_72_data_download/Conserved_Site_Context_Scores.txt.zip"
    logging.info("Downloading {}...".format(url))

    try:
        download(url, file_name)
        # Check that download is successful:
        if os.path.exists(file_name):
            logging.info("Download successful.")
        else:
            logging.warning("Download failed.")
    except Exception as e:
        logging.error("Download issue: {}".format(e))
        sys.exit("Run aborted.")


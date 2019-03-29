# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 20/03/2019
# Purpose: Get raw data from targetscan website

import logging
from requests import get  # to make GET request
import os.path
import sys
import click

# Personal imports
import utilities


def download(url: str, file_name: str):
    """
    Download file from URL.
    :param url: address to get the file from.
    :param file_name: name of file to write downloaded data in.
    :return: None
    """
    # Check that file was not already downloaded
    download_tag = True
    short_file_name = file_name.split("/")[-1]
    if os.path.exists(file_name):
        # If so, do you wish to download it anyway?
        if not click.confirm("{} already exists on your system. "
                             "Do you still wish to download it anyway?".format(short_file_name), default=False):
            download_tag = False

    if download_tag:
        logging.info("Downloading {}...".format(url))
        # open in binary mode
        with open(file_name, "wb") as file:
            # get request
            response = get(url)
            # write to file
            file.write(response.content)

        # Check that download is successful:
        if os.path.exists(file_name):
            logging.info("Download successful.")
        else:
            logging.warning("Download failed.")
    else:
        logging.info("You do not wish to download {}".format(short_file_name))


if __name__ == '__main__':
    # Set logging module
    logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")

    # Set project config
    config = utilities.extract_config()

    # Set variables
    file_name = config["TARGETSCAN"]["SAVE FILE TO"]
    url = config["TARGETSCAN"]["URL"]

    try:
        download(url, file_name)

    except Exception as e:
        logging.error("Download issue: {}".format(e))
        sys.exit("Run aborted.")


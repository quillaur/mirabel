# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 12/04/2019
# Purpose: Create a module to download URL files.

import logging
import os
import sys
from requests import get  # to make GET request

# Personal imports
import utilities


class Downloader:
    """
    General class to download all wanted data.
    """
    def __init__(self, db_name: str):
        """
        Downloader init.

        :param db_name: Name of the public database to download. WARNING: must be the same spelling as in your config !
        :type db_name: str
        """
        # Get logging module from main script
        self.logger = logging.getLogger(__name__)

        # Set project config
        self.config = utilities.extract_config()

        # Which DB to download
        self.db_name = db_name

        # Download path and URL
        self.dir_name = self.config[self.db_name]["SAVE FILE TO"]
        self.urls = [self.config[self.db_name][url] for url in self.config[self.db_name] if "URL" in url]
        self.filenames = [os.path.join(self.dir_name, url.split("/")[-1]) for url in self.urls]

    def download(self, url: str, file_name: str):
        """
        Download file from URL.
        :param url: address to get the file from.
        :param file_name: name of file to write downloaded data in.
        :return: None
        """
        self.logger.info("Downloading {}...".format(url))
        # open in binary mode
        with open(file_name, "wb") as file:
            # get request
            response = get(url)
            # write to file
            file.write(response.content)

        # Check that download is successful:
        if os.path.exists(file_name):
            self.logger.info("Download successful.")
        else:
            self.logger.warning("Download failed.")

    def run(self):
        for url in self.urls:
            try:
                self.download(url, self.filenames[self.urls.index(url)])

            except Exception as e:
                self.logger.error("Download issue: {}".format(e))
                sys.exit("Run aborted.")

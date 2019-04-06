# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 29/03/2019
# Purpose: read configuration files

import configparser
import os
import mysql.connector
import click
import logging
from requests import get  # to make GET request

# Set logging module
logging.basicConfig(level="DEBUG", format="%(asctime)s - %(levelname)s - %(message)s")


def extract_config():
    """
    Get configuration parameters from config.cfg file.

    :return: dictionary of config parameters.
    :rtype: ConfigParser
    """
    config = configparser.ConfigParser()
    # Get current directory
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(["config.cfg", os.path.expanduser(dir_path.replace("scripts", ""))])

    return config


def mysql_connection(config):
    """
    Set mysql connection

    :param config: configuration parameters dictionary

    :return: connection
    """
    return mysql.connector.connect(
        host=config["DB"]["HOST"],
        user=config["DB"]["USER"],
        passwd=config["DB"]["PASSWORD"],
        db=config["DB"]["DATABASE"]
    )


def chunk(input_list: list, chunk_size: int):
    """
    Yields successive n-sized chunks from input list.

    :param input_list: list you wish to chunk.
    :type input_list: list
    :param chunk_size: how many chunks you wish.
    :type chunk_size: int
    """
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]


def download(url: str, file_name: str):
    """
    Download file from URL.
    :param url: address to get the file from.
    :param file_name: name of file to write downloaded data in.
    :return: None
    """
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


def check_files_presence(files_list: list):
    """
    Check that all files exist.
    :param files_list: list of files you wish to check the presence of.
    :type files_list: list

    :return: True if all files present, else false.
    """
    for file in files_list:
        if not os.path.exists(file):
            return False
    return True

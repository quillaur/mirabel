# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 29/03/2019
# Purpose: read configuration files

import configparser
import os
import mysql.connector


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


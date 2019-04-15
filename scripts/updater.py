# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 12/04/2019
# Purpose: Create a module to update downloaded files into mysql DB.

import logging
import os
import gzip
import zipfile
import pandas
import tarfile
import lzma

# Personal imports
from scripts import utilities


class Updater:
    """
        General class to update all wanted data.
        """

    def __init__(self, db_name: str):
        """
        Updater init.

        :param db_name: Name of the public database to update. WARNING: must be the same spelling as in your config !
        :type db_name: str
        """
        # Get logging module from main script
        self.logger = logging.getLogger(__name__)

        # Set project config
        self.config = utilities.extract_config()

        # Which DB to download
        self.db_name = db_name

        # File paths
        if "Svmicro" in self.db_name:
            self.dir_name = self.config[self.db_name.upper()]["SAVE FILE TO"]
            self.filenames = []
            with open(self.config[self.db_name.upper()]["URL_0"], "r") as my_txt:
                for line in my_txt:
                    self.filenames.append(os.path.join(self.dir_name, line).strip())
        else:
            self.dir_name = self.config[self.db_name.upper()]["SAVE FILE TO"]
            self.urls = [self.config[self.db_name.upper()][url] for url in self.config[self.db_name.upper()] if "url" in url]
            self.filenames = [os.path.join(self.dir_name, url.split("/")[-1]) for url in self.urls]

    def truncate_table(self):
        connection = utilities.mysql_connection(self.config)
        self.logger.info("Truncating {} table...".format(self.db_name))
        query = "TRUNCATE TABLE {};".format(self.db_name)
        cursor = connection.cursor()
        cursor.execute(query)

        # Test if truncate worked
        query = "SELECT count(*) FROM {};".format(self.db_name)
        cursor.execute(query)
        if cursor.fetchone()[0] == 0:
            self.logger.info("Truncate successful !")
        else:
            self.logger.warning("Truncate FAILED !")

        connection.close()

    def parse_lines(self, file, mir_col: int, species: str = "hsa"):
        """
        Parse line by line to format data before insertion.

        :param file: opened file object
        :param mir_col: index of the list containing mirna name.
        :param species: species you are looking for. So far 'hsa' only.

        Yield file content line by line (otherwise file can be too large and overload my computer).
        """
        count = 0
        header = ""
        for line in file:
            count += 1
            if count == 1:
                header = line.decode("utf-8").replace("\n", "").split("\t")
                continue

            parsed_data = line.decode("utf-8").replace("\n", "").split("\t")

            if len(parsed_data) > 1 and species in parsed_data[mir_col]:
                to_insert_dict = {}
                for key in header:
                    if key in self.config[self.db_name.upper()]:
                        to_insert_dict[self.config[self.db_name.upper()][key]] = parsed_data[header.index(key)]

                yield to_insert_dict

            else:
                continue

    def read_downloaded_file(self, filename: str):
        """
        Decide which function to use to open file and parse / insert it into DB.

        :param filename: name of file
        :return: None
        """
        predictions_list = []
        if "Svmicro" in self.db_name:
            with open(filename, "r") as my_file:
                for insert_dict in self.parse_svmicro_line(file=my_file, filename=filename):
                    predictions_list.append(insert_dict)
                    if len(predictions_list) > 1000:
                        self.insert_into_db(predictions_list)
                        predictions_list = []

                self.insert_into_db(predictions_list)

        elif ".xls" in filename:
            # Read excel file into a dataframe
            data_xlsx = pandas.read_excel(filename)
            for insert_dict in self.parse_xlsx(data_xlsx):
                predictions_list.append(insert_dict)
                if len(predictions_list) > 1000:
                    self.insert_into_db(predictions_list)
                    predictions_list = []

            self.insert_into_db(predictions_list)

        elif "tar.gz" in filename:
            tar = tarfile.open(filename, "r:gz")
            for member in tar.getmembers():
                print(member)
                file = tar.extractfile(member)
                if file is not None:
                    # for line in file.read():
                    #     print(line)
                    content = file.read()
                    print(content.decode("UTF-8"))

        elif ".xz" in filename:
            with lzma.open(filename) as my_file:
                for line in my_file:
                    print(line)
                    break

        elif ".gz" in filename:
            with gzip.open(filename, "r") as my_file:
                for insert_dict in self.parse_lines(file=my_file,
                                                    mir_col=int(self.config[self.db_name.upper()]["MIR_NAME_COL"]),
                                                    species="hsa"):
                    predictions_list.append(insert_dict)
                    if len(predictions_list) > 1000:
                        self.insert_into_db(predictions_list)
                        predictions_list = []

                self.insert_into_db(predictions_list)

        elif ".zip" in filename:
            with zipfile.ZipFile(filename, "r") as my_zip:
                for my_txt in my_zip.namelist():
                    with my_zip.open(my_txt) as my_file:
                        for insert_dict in self.parse_lines(file=my_file,
                                                            mir_col=int(self.config[self.db_name.upper()]["MIR_NAME_COL"]),
                                                            species="hsa"):
                            predictions_list.append(insert_dict)
                            if len(predictions_list) > 1000:
                                self.insert_into_db(predictions_list)
                                predictions_list = []

                        self.insert_into_db(predictions_list)

    def parse_xlsx(self, xlsx_data):
        """
        Transform panda dataframe (made out of xlsx file) so that I can insert them into mysql.

        :param xlsx_data: xlsx file content as panda dataframe.

        yield dictionary to insert into mysql.
        """
        headers = list(xlsx_data.keys())
        for indice, row in enumerate(xlsx_data[headers[0]]):
            to_insert_dict = {}
            for header in headers:
                if header in self.config[self.db_name.upper()]:
                    try:
                        to_insert_dict[self.config[self.db_name.upper()][header]] = str(xlsx_data[header][indice])
                    except Exception as e:
                        to_insert_dict[self.config[self.db_name.upper()][header]] = str(xlsx_data[header][indice].decode("UTF-8"))
            yield to_insert_dict

    def parse_svmicro_line(self, file, filename):
        """
        Special data parsin for SVmicro.

        :param file: file object to parse.
        :param filename: name of file to parse.

        yield dictionary to insert into mysql.
        """
        for line in file:
            data = line.replace("\n", "").split("\t")
            if len(data) > 1:
                yield {
                    "mirna_name": filename.split("/")[-1].replace(".txt", ""),
                    "gene_id": None,
                    "gene_symbol": data[0],
                    "score": data[1]
                }
            else:
                continue

    def insert_into_db(self, predictions_list):
        """
        Insert parsed data in mysql DB.

        :param predictions_list: list of dictionaries containing parsed data to insert.

        :return: None
        """
        if "Mirtarbase" in self.db_name or "Mirecords" in self.db_name:
            query = "INSERT INTO {} (MirName, GeneID, GeneSymbol, Experiment) " \
                    "VALUES (%(mirna_name)s, %(gene_id)s, %(gene_symbol)s, %(experiment)s);".format(self.db_name)
        else:
            query = "INSERT INTO {} (MirName, GeneID, GeneSymbol, Score) " \
                    "VALUES (%(mirna_name)s, %(gene_id)s, %(gene_symbol)s, %(score)s);".format(self.db_name)
        connection = utilities.mysql_connection(self.config)
        cursor = connection.cursor()
        cursor.executemany(query, predictions_list)
        connection.commit()
        connection.close()

    def run(self):
        self.truncate_table()

        logging.info("Processing and inserting data in {} table...".format(self.db_name))
        for file in self.filenames:
            self.read_downloaded_file(filename=file)

            logging.info("{} / {} file(s) done !".format(self.filenames.index(file) + 1, len(self.filenames)))

# Author: Aurélien Quillet
# Contact: aurelien.quillet@gmail.com
# Date: 12/04/2019
# Purpose: Create a module to update downloaded files into mysql DB.

import logging
import os
import gzip
import zipfile

# Personal imports
import utilities


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

        Examle parsed_data for targetscan:
        ['Gene ID', 'Gene Symbol', 'Transcript ID', 'Gene Tax ID', 'miRNA', 'Site Type', 'UTR_start', 'UTR end', 'context++ score', 'context++ score percentile', 'weighted context++ score', 'weighted context++ score percentile']
        ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9544', 'mml-miR-23a-3p', '3', '142', '149', '-0.428', '97', '-0.388', '97']
        ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9544', 'mml-miR-23b-3p', '3', '142', '149', '-0.428', '97', '-0.388', '97']
        ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9598', 'ptr-miR-23a', '3', '143', '150', '-0.419', '97', '-0.419', '98']
        ['ENSG00000121410.7', 'A1BG', 'ENST00000263100.3', '9598', 'ptr-miR-23b', '3', '143', '150', '-0.419', '97', '-0.419', '98']

        Exemple to_insert_dict for targetscan:
        {'Gene ID': 'ENSG00000121410.7', 'Gene Symbol': 'A1BG', 'Transcript ID': 'ENST00000263100.3',
        'Gene Tax ID': '9606', 'miRNA': 'hsa-miR-23b-3p', 'Site Type': '3', 'UTR_start': '143',
        'UTR end': '150', 'context++ score': '-0.434', 'context++ score percentile': '97',
        'weighted context++ score': '-0.434', 'weighted context++ score percentile': '98'}

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

    def parse_svmicro_line(self, file, filename):
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

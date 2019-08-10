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
import sys
import mysql.connector

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

        # Which DB to update
        self.db_name = db_name

        self.species = "hsa"
        self.mirna_dico = utilities.get_mirna_conversion_info(self.config)
        self.gene_dico = utilities.get_gene_conversion_info(self.config)
        self.unknown_mirs = []
        self.unknown_genes = []
        self.validated_interactions = utilities.get_validated_interactions(self.config)

        # File paths
        if "Svmicro" in self.db_name or "Mbstar" in self.db_name:
            self.dir_name = self.config[self.db_name.upper()]["SAVE FILE TO"]
            self.filenames = []
            with open(self.config[self.db_name.upper()]["URL_0"], "r") as my_txt:
                for line in my_txt:
                    self.filenames.append(os.path.join(self.dir_name, line).strip())
        elif "Mirabel" in self.db_name:
            self.dir_name = ""
            self.urls = []
            self.filenames = []
        else:
            self.dir_name = self.config[self.db_name.upper()]["SAVE FILE TO"]
            self.urls = [self.config[self.db_name.upper()][url] for url in self.config[self.db_name.upper()] if "url" in url]
            self.filenames = [os.path.join(self.dir_name, url.split("/")[-1]) for url in self.urls]

    def parse_lines(self, file, mir_col: int, filename: str="", species: str = "hsa", decode: bool = True):
        """
        Parse line by line to format data before insertion.

        :param file: opened file object
        :param mir_col: index of the list containing mirna name.
        :param species: species you are looking for. So far 'hsa' only.
        :param decode: indicating if content needs to be decode or not. Default is True.

        Yield file content line by line (otherwise file can be too large and overload my computer).
        """
        count = 0
        header = ""
        if "Mirmap" in self.db_name:
            separator = ","
        elif "Comir" in self.db_name or "Exprtarget" in self.db_name:
            separator = " "
        else:
            separator = "\t"

        for line in file:
            count += 1
            if count == 1:
                if "Mirdb" in self.db_name:
                    header = ["mirna_name", "", "score", "gene_id"]
                else:
                    # Comir has wierd '"' symbol stuck around each word
                    header = line.decode("utf-8").replace("\n", "").split(separator) if decode else line.replace("\n", "").replace("\"", "").split(separator)
                
                continue

            parsed_data = line.decode("utf-8").replace("\n", "").split(separator) if decode else line.replace("\n", "").replace("\"", "").split(separator)

            if "Comir" in self.db_name or "Exprtarget" in self.db_name:
                del parsed_data[0]

            if len(parsed_data) > 1 and (species in parsed_data[mir_col] or "MIMAT" in parsed_data[mir_col]):
                to_insert_dict = {}
                for key in header:
                    if key in self.config[self.db_name.upper()]:
                        to_insert_dict[self.config[self.db_name.upper()][key]] = parsed_data[header.index(key)]

                if "Mirdb" in self.db_name or "Exprtarget" in self.db_name:
                    to_insert_dict["gene_symbol"] = None
                    try:
                        to_insert_dict["gene_id"] = int(to_insert_dict["gene_id"])
                    except Exception as e:
                        self.unknown_genes.append(to_insert_dict["gene_id"])
                        continue

                elif "Mirwalk" in self.db_name:
                    to_insert_dict["gene_id"] = None
                    if "3UTR" in filename:
                        to_insert_dict["localisation"] = "3UTR"
                    elif "5UTR" in filename:
                        to_insert_dict["localisation"] = "5UTR"
                    else:
                        to_insert_dict["localisation"] = "CDS"

                # Reformat for insert
                if "." in to_insert_dict["mirna_name"]:
                    mir_name = to_insert_dict["mirna_name"].split(".")[0]
                else:
                    mir_name = to_insert_dict["mirna_name"]
                
                if mir_name in self.mirna_dico:
                    to_insert_dict["Mimat"] = self.mirna_dico[mir_name]
                elif "MIMAT" in mir_name:
                    to_insert_dict["Mimat"] = int(mir_name.replace("MIMAT", ""))
                else:
                    self.unknown_mirs.append(mir_name)
                    continue

                if not to_insert_dict["gene_id"] or not isinstance(to_insert_dict["gene_id"], int):
                    if to_insert_dict["gene_symbol"] in self.gene_dico:
                        to_insert_dict["gene_id"] = self.gene_dico[to_insert_dict["gene_symbol"]]
                    else:
                        self.unknown_genes.append(to_insert_dict["gene_symbol"])
                        continue

                # Get the label
                to_insert_dict["validated"] = "1" if int(to_insert_dict["gene_id"]) in self.validated_interactions[int(to_insert_dict["Mimat"])] else "0"

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
        if "Svmicro" in self.db_name or "Mbstar" in self.db_name:
            with open(filename, "r") as my_file:
                for insert_dict in self.parse_svmicro_line(file=my_file, filename=filename):
                    predictions_list.append(insert_dict)
                    if len(predictions_list) > 1000:
                        self.insert_into_db(predictions_list)
                        predictions_list = []

                self.insert_into_db(predictions_list)

        elif "Comir" in self.db_name or "Exprtarget" in self.db_name:
            my_path = self.config[self.db_name.upper()]["SAVE FILE TO"]
            comir_files = [os.path.join(my_path, f) for f in os.listdir(my_path) if os.path.isfile(os.path.join(my_path, f))]
            for file in comir_files:
                with open(file, "r") as my_file:
                    for insert_dict in self.parse_lines(file=my_file,
                                                    mir_col=int(self.config[self.db_name.upper()]["MIR_NAME_COL"]),
                                                    species=self.species,
                                                    decode=False):
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

        elif ".xz" in filename:
            with lzma.open(filename) as my_file:
                for insert_dict in self.parse_lines(file=my_file,
                                                    mir_col=int(self.config[self.db_name.upper()]["MIR_NAME_COL"]),
                                                    species=self.species):
                    predictions_list.append(insert_dict)
                    if len(predictions_list) > 1000:
                        self.insert_into_db(predictions_list)
                        predictions_list = []

                self.insert_into_db(predictions_list)

        elif ".7z" in filename:
            alt_filename = filename.replace(".7z", ".txt")
            if not os.path.exists(alt_filename):
                # No known other choice than to uncompress it first...
                os.system("7z x {} -o{}".format(filename, self.dir_name))
            else:
                with open(alt_filename, "r") as my_file:
                    for insert_dict in self.parse_lines(file=my_file,
                                                    mir_col=int(self.config[self.db_name.upper()]["MIR_NAME_COL"]),
                                                    species=self.species,
                                                    decode=False,
                                                    filename=alt_filename):
                        predictions_list.append(insert_dict)
                        if len(predictions_list) > 1000:
                            self.insert_into_db(predictions_list)
                            predictions_list = []

                    self.insert_into_db(predictions_list)

        elif ".gz" in filename:
            with gzip.open(filename, "r") as my_file:
                for insert_dict in self.parse_lines(file=my_file,
                                                    mir_col=int(self.config[self.db_name.upper()]["MIR_NAME_COL"]),
                                                    species=self.species):
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
                                                            species=self.species):
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
            
            # Reformat for insert
            if "." in to_insert_dict["mirna_name"]:
                mir_name = to_insert_dict["mirna_name"].split(".")[0]
            elif "[" in to_insert_dict["mirna_name"]:
                mir_name = to_insert_dict["mirna_name"].strip("[]")
            else:
                mir_name = to_insert_dict["mirna_name"]
            
            if mir_name in self.mirna_dico:
                if self.species in mir_name:
                    to_insert_dict["Mimat"] = self.mirna_dico[mir_name]
                else:
                    continue
            else:
                self.unknown_mirs.append(mir_name)
                continue

            if not to_insert_dict["gene_id"] or not isinstance(to_insert_dict["gene_id"], int):
                if to_insert_dict["gene_symbol"] in self.gene_dico:
                    to_insert_dict["gene_id"] = self.gene_dico[to_insert_dict["gene_symbol"]]
                else:
                    self.unknown_genes.append(to_insert_dict["gene_symbol"])
                    continue

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

            if len(data) == 1:
                data = line.replace("\n", "").replace('"', '').split(" ")
                del data[0]

            mir_name = filename.split("/")[-1].replace(".txt", "")
            if len(data) > 1:
                if data[0] in self.gene_dico:
                    mimat = int(mir_name.replace("MIMAT", ""))
                    yield {
                    "mirna_name": mir_name,
                    "gene_id": self.gene_dico[data[0]],
                    "gene_symbol": data[0],
                    "score": data[1],
                    "Mimat": mimat,
                    "validated": "1" if self.gene_dico[data[0]] in self.validated_interactions[mimat] else "0"
                }

                else:
                    self.unknown_genes.append(data[0])
                    continue
            else:
                continue

    def insert_into_db(self, predictions_list):
        """
        Insert parsed data in mysql DB.

        :param predictions_list: list of dictionaries containing parsed data to insert.

        :return: None
        """
        if "Mirtarbase" in self.db_name or "Mirecords" in self.db_name:
            query = "INSERT INTO {} (Mimat, GeneID, Experiment) " \
                    "VALUES (%(Mimat)s, %(gene_id)s, %(experiment)s);".format(self.db_name)
        elif "Mirwalk" in self.db_name:
            query = "INSERT INTO {} (Mimat, GeneID, Score, Localisation, Validated) " \
                    "VALUES (%(Mimat)s, %(gene_id)s, %(score)s, %(localisation)s, %(validated)s) " \
                    "ON DUPLICATE KEY UPDATE Mimat = VALUES(Mimat), " \
                    "GeneID = VALUES(GeneID), " \
                    "Score = VALUES(Score), " \
                    "Validated = VALUES(Validated), " \
                    "Localisation = VALUES(Localisation);".format(self.db_name)
        else:
            query = "INSERT INTO {} (Mimat, GeneID, Score, Validated) " \
                    "VALUES (%(Mimat)s, %(gene_id)s, %(score)s, %(validated)s) " \
                    "ON DUPLICATE KEY UPDATE Mimat = VALUES(Mimat), " \
                    "GeneID = VALUES(GeneID), " \
                    "Score = VALUES(Score), " \
                    "Validated = VALUES(Validated);".format(self.db_name)
        connection = utilities.mysql_connection(self.config)
        cursor = connection.cursor()
        try:
            cursor.executemany(query, predictions_list)
        except Exception as e:
            self.logger.error("Insert ERROR: {}".format(e))
            # for insert_dict in predictions_list:
            #     try:
            #         cursor.execute(query, insert_dict)
            #     except mysql.connector.errors.IntegrityError as e:
            #         pass

        connection.commit()
        connection.close()

    def run(self):
        utilities.truncate_table(config=self.config, table=self.db_name)

        self.logger.info("Processing and inserting data in {} table...".format(self.db_name))
        for file in self.filenames:
            self.read_downloaded_file(filename=file)

            self.logger.info("{} / {} file(s) done !".format(self.filenames.index(file) + 1, len(self.filenames)))

        self.unknown_genes = list(set(self.unknown_genes))
        self.unknown_mirs = list(set(self.unknown_mirs))
        if self.unknown_mirs:
            self.logger.warning("{} miRs interactions could not be inserted because the miR is unknown in the database !".format(len(self.unknown_mirs)))
            self.logger.warning("Exemples : {}".format(self.unknown_mirs[:100]))
        if self.unknown_genes:
            self.logger.warning("{} miRs interactions could not be inserted because the gene symbol is unknown in the database !".format(len(self.unknown_genes)))
            self.logger.warning("Exemples : {}".format(self.unknown_genes[:100]))


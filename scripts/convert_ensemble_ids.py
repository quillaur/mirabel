import mysql.connector
# https://www.biorxiv.org/content/biorxiv/early/2014/09/17/009332.full.pdf
import mygene

# Personal imports
import utilities


def get_gene_ids(config: dict):
	query = "SELECT ncbi_gene_id from genes3;"

	connection = utilities.mysql_connection(config)
	cursor = connection.cursor()
	cursor.execute(query)

	results_list = [int(row[0]) for row in cursor]

	connection.close()

	return results_list

def convert_gene_ids(gene_id_list: list):
	mg = mygene.MyGeneInfo()
	query_results = mg.querymany(gene_id_list, scopes='entrezgene', fields='ensembl.gene', species='human')

	result_dict = {}
	for res in query_results:
		if "ensembl" in res:
			try:
				result_dict[int(res["query"])] = res["ensembl"]["gene"]
			except Exception as e:
				result_dict[int(res["query"])] = res["ensembl"][0]["gene"]
				continue

	return result_dict


if __name__ == '__main__':
	print("Script initiated.")
	config = utilities.extract_config()
	print("Config extracted.")
	gene_ids_list = get_gene_ids(config)
	print("I got {} gene IDs.".format(len(gene_ids_list)))
	converter_dict = convert_gene_ids(gene_ids_list)
	print("I converted {} gene IDs.".format(len(converter_dict)))

	# Reformat for insert
	data_list = [{"ncbi_gene_id": key, "EnsembleID": value} for key, value in converter_dict.items()]

	query = """
			INSERT INTO genes3 (ncbi_gene_id, EnsembleID) 
			VALUES (%(ncbi_gene_id)s, %(EnsembleID)s) 
			ON DUPLICATE KEY UPDATE EnsembleID = VALUES(EnsembleID);
			"""
	connection = utilities.mysql_connection(config)
	cursor = connection.cursor()
	cursor.executemany(query, data_list)

	# for convert_dict in data_list:
	# 	query = "UPDATE genes3 SET EnsembleID = '{}' WHERE ncbi_gene_id = '{}';".format(convert_dict["EnsembleID"], convert_dict["ncbi_gene_id"])
	# 	print(query)
	# 	cursor.execute(query)

	connection.commit()
	connection.close()
	print("Insertion done. Script done.")

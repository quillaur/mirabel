#! /usr/bin/Rscript

## Statistic analysis

library("flux")

print("I am random_pr.py !")

tmp_files_list = list.files("resources/tmp_roc_data/random_sets")
# print(tmp_files_list)
db_name_list = c()
for (file in tmp_files_list) {
	db_name = strsplit(file, "_tmp")[[1]][1]
	if ("Mirabel" %in% db_name && !(db_name %in% db_name_list)) {
		db_name_list = c(db_name, db_name_list)
	} else if (!(db_name %in% db_name_list)) {
		db_name_list = c(db_name_list, db_name)
	}

	if (length(db_name_list) == 2) {
		break
	}
}
# print(db_name_list)

db_1_files = c()
db_2_files = c()
for (file in tmp_files_list) {
	# print(file)
	for (i in 1:10) {
		test_number = paste("_", as.character(i), ".txt", sep = "")
		if (length(grep(test_number, file)) > 0 && length(grep(db_name_list[1], file)) > 0) {
			db_1_files[i] = file

		} else if (length(grep(test_number, file)) > 0 && length(grep(db_name_list[2], file)) > 0) {
			db_2_files[i] = file

		}
  	}
}
# print(db_1_files)
# print(db_2_files)

compute_pr = function(res_df)
{
	pr_df_0 = data.frame(val_number = res_df[1,2])
	pr_df_0$precision = sum(res_df[1,2])
	pr_df_0$recall = 0
	pr_df_0$f_score = 0

	for (x in 2:nrow(res_df))
	{
		pr_df_0[x,1] = sum(res_df[1:x,2])
		pr_df_0[x,2] = pr_df_0[x,1] / x
		pr_df_0[x,3] = pr_df_0[x,1] / sum(res_df[,2])

		if(pr_df_0[x,3] > 0)
		{
			pr_df_0[x,4] = 2*((pr_df_0[x,2] * pr_df_0[x,3])/(pr_df_0[x,2] + pr_df_0[x,3]))
		}
		else
	    {
	        pr_df_0[x,4] = 0
	    }
	}

	return(pr_df_0)
}

all_pr_auc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE) 
increasing = c("Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel")
decreasing = c("Svmicro", "Comir", "Mirdb", "Mirwalk")

for (i in 1:10) {
	db_name = strsplit(file, "_tmp")[[1]][1]
	file_0 = file.path("resources/tmp_roc_data/random_sets", db_1_files[i])
	print(file_0)
	res0 = read.table(file_0, header = TRUE, sep = ";")
	file_1 = file.path("resources/tmp_roc_data/random_sets", db_2_files[i])
	print(file_1)
	res1 = read.table(file_1, header = TRUE, sep = ";")
	
	# Mirabel order is increasing
	res0 = res0[order(res0$score, decreasing = FALSE),]

	# The other DB, we don't know the sense
	if (db_name_list[2] %in% decreasing) {
		res1 = res1[order(res1$score, decreasing = TRUE),]
	} else {
		res1 = res1[order(res1$score, decreasing = FALSE),]
	}

	# print(head(res0))
	# print(head(res1))

	# Precision versus Recall
	pr_df_0 = compute_pr(res0)
	auc.pr_df_0 = auc(pr_df_0$recall, pr_df_0$precision)
	pr_df_1 = compute_pr(res1)
	auc.pr_df_1 = auc(pr_df_1$recall, pr_df_1$precision)
	AUC = data.frame(res0=auc.pr_df_0, res1=auc.pr_df_1, stringsAsFactors=FALSE)
	all_pr_auc = rbind(all_pr_auc, AUC)
}

mean_pr_db_1 = mean(all_pr_auc$res0)
mean_pr_db_2 = mean(all_pr_auc$res1)
sem_pr_db_1 = sd(all_pr_auc$res0)/sqrt(nrow(all_pr_auc))
sem_pr_db_2 = sd(all_pr_auc$res1)/sqrt(nrow(all_pr_auc))

names(all_pr_auc)[names(all_pr_auc)=="res0"] = db_name_list[1]
names(all_pr_auc)[names(all_pr_auc)=="res1"] = db_name_list[2]

print(all_pr_auc)

result_file = paste("resources/", db_name_list[1], "_", db_name_list[2], "_stats_pr_results.txt", sep = "")
sink(result_file)
print(all_pr_auc)
print(paste("Mean:", mean_pr_db_1, mean_pr_db_2))
print(paste("SEM:", sem_pr_db_1, sem_pr_db_2))
t.test(all_pr_auc[,1], all_pr_auc[,2])
sink()

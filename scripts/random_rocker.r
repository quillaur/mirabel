#! /usr/bin/Rscript

## Statistic analysis

library("pROC")

print("I am random_rocker.py !")

tmp_files_list = list.files("resources/tmp_roc_data/random_sets")
print(tmp_files_list)
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
print(db_name_list)

db_1_files = c()
db_2_files = c()
for (file in tmp_files_list) {
	print(file)
	for (i in 1:10) {
		test_number = paste("_", as.character(i), ".txt", sep = "")
		if (length(grep(test_number, file)) > 0 && length(grep(db_name_list[1], file)) > 0) {
			db_1_files[i] = file

		} else if (length(grep(test_number, file)) > 0 && length(grep(db_name_list[2], file)) > 0) {
			db_2_files[i] = file

		}
  	}
}
print(db_1_files)
print(db_2_files)

all_auc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE) 
all_pauc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE)
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

	print(head(res0))
	print(head(res1))

	# roc.res0 is a list
	roc.res0 = roc(label~score, res0)
	roc.res1 = roc(label~score, res1)
	
	auc.res0 = auc(roc.res0)
	auc.res1 = auc(roc.res1)
	AUC = data.frame(res0=auc.res0, res1=auc.res1, stringsAsFactors=FALSE)
	all_auc = rbind(all_auc, AUC)

	# Partial AUC
	p.auc.res0 = auc(roc.res0, partial.auc=c(1,0.9), partial.auc.focus=c("specificity"))
	p.auc.res1 = auc(roc.res1, partial.auc=c(1,0.9), partial.auc.focus=c("specificity"))
	pAUC = data.frame(res0=p.auc.res0, res1=p.auc.res1, stringsAsFactors=FALSE)
	all_pauc = rbind(all_pauc, pAUC)	
}
# all_auc$init = NULL
# all_pauc$init = NULL
# Rename column
names(all_auc)[names(all_auc)=="res0"] = db_name_list[1]
names(all_auc)[names(all_auc)=="res1"] = db_name_list[2]
names(all_pauc)[names(all_pauc)=="res0"] = db_name_list[1]
names(all_pauc)[names(all_pauc)=="res1"] = db_name_list[2]
print(all_auc)
print(all_pauc)

# Test 2 ROC
# db_name_list = c()
# for (file in tmp_files_list) {
# 	db_name = strsplit(file, "_tmp")[[1]][1]
# 	if (!(db_name %in% db_name_list)) {
# 		db_name_list = c(db_name_list, db_name)
# 	}	
# }
# test.roc.0 = roc.test(roc1, roc2, method=c("bootstrap"), boot.n = 100, boot.stratified = TRUE)
# print(test.roc.0)
# lapply(test.roc.0, write, paste("resources/", db_name_list[1], "_", db_name_list[2], "_roc_stats.txt", sep = ""), append=FALSE, ncolumns=1000)

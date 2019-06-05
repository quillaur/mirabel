#! /usr/bin/Rscript

## Statistic analysis

library("pROC")

print("I am random_rocker.py !")

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

all_auc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE) 
all_pauc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE) 
all_specif = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE)
all_sensi = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE)
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

	# Get opti Sensi and specif
	best_pt_0 = coords(roc.res0, x = "best", ret=c("specificity", "sensitivity"), best.method = "closest.topleft")
	best_pt_1 = coords(roc.res1, x = "best", ret=c("specificity", "sensitivity"), best.method = "closest.topleft")
	specif = data.frame(res0=best_pt_0[1], res1=best_pt_1[1], stringsAsFactors=FALSE)
	sensi = data.frame(res0=best_pt_0[2], res1=best_pt_1[2], stringsAsFactors=FALSE)
	all_specif = rbind(all_specif, specif)
	all_sensi = rbind(all_sensi, sensi)
}

mean_db_1 = mean(all_auc$res0)
mean_db_2 = mean(all_auc$res1)
sem_db_1 = sd(all_auc$res0)/sqrt(nrow(all_auc))
sem_db_2 = sd(all_auc$res1)/sqrt(nrow(all_auc))

mean_p_db_1 = mean(all_pauc$res0)
mean_p_db_2 = mean(all_pauc$res1)
sem_p_db_1 = sd(all_pauc$res0)/sqrt(nrow(all_pauc))
sem_p_db_2 = sd(all_pauc$res1)/sqrt(nrow(all_pauc))

mean_spe_1 = mean(all_specif$res0)
mean_spe_2 = mean(all_specif$res1)
sem_spe_1 = sd(all_specif$res0)/sqrt(nrow(all_specif))
sem_spe_2 = sd(all_specif$res1)/sqrt(nrow(all_specif))

mean_sen_1 = mean(all_sensi$res0)
mean_sen_2 = mean(all_sensi$res1)
sem_sen_1 = sd(all_sensi$res0)/sqrt(nrow(all_sensi))
sem_sen_2 = sd(all_sensi$res1)/sqrt(nrow(all_sensi))

names(all_auc)[names(all_auc)=="res0"] = db_name_list[1]
names(all_auc)[names(all_auc)=="res1"] = db_name_list[2]
names(all_pauc)[names(all_pauc)=="res0"] = db_name_list[1]
names(all_pauc)[names(all_pauc)=="res1"] = db_name_list[2]
names(all_specif)[names(all_specif)=="res0"] = db_name_list[1]
names(all_specif)[names(all_specif)=="res1"] = db_name_list[2]
names(all_sensi)[names(all_sensi)=="res0"] = db_name_list[1]
names(all_sensi)[names(all_sensi)=="res1"] = db_name_list[2]

print(all_auc)
print(all_pauc)
print(all_specif)
print(all_sensi)

result_file = paste("resources/", db_name_list[1], "_", db_name_list[2], "_stats_results.txt", sep = "")
sink(result_file)
print(all_auc)
print(paste("Mean:", mean_db_1, mean_db_2))
print(paste("SEM:", sem_db_1, sem_db_2))
t.test(all_auc[,1], all_auc[,2])

print(all_pauc)
print(paste("Mean:", mean_p_db_1, mean_p_db_2))
print(paste("SEM:", sem_p_db_1, sem_p_db_2))
t.test(all_pauc[,1], all_pauc[,2])

print(all_specif)
print(paste("Mean:", mean_spe_1, mean_spe_2))
print(paste("SEM:", sem_spe_1, sem_spe_2))
t.test(all_specif[,1], all_specif[,2])

print(all_sensi)
print(paste("Mean:", mean_sen_1, mean_sen_2))
print(paste("SEM:", sem_sen_1, sem_sen_2))
t.test(all_sensi[,1], all_sensi[,2])
sink()

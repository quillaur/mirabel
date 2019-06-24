#! /usr/bin/Rscript

## Statistic analysis
InsPack = function(pack) 
{ 
	if (!pack %in% installed.packages()) 
	{ 
		print(paste("installing",pack)) 
		install.packages(pack, repos=structure(c(CRAN="http://cloud.r-project.org/")))
	} 
	else
	{
		print(paste(pack," already installed"))
	}
} 
InsPack("pROC")
library("pROC")
InsPack("rowr")
library("rowr")

print("I am random_rocker.py !")

tmp_files_list = list.files("resources/tmp_roc_data/random_sets")
# print(tmp_files_list)

db_name_list = c()
# I need miRabel to be the first element of the vector, so I loop twice through the loop.
for (i in 1:2)
{
	for (file in tmp_files_list) 
	{
		db_name = strsplit(file, "_tmp")[[1]][1]
		if (!(db_name %in% db_name_list) && grepl("Mirabel", db_name)) 
		{
			db_name_list = c(db_name_list, db_name)
		}
		else if (!(db_name %in% db_name_list) && length(db_name_list) > 0)
		{
			db_name_list = c(db_name_list, db_name)
		}
	}
}
print(db_name_list)

all_auc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE) 
all_pauc = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE) 
all_specif = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE)
all_sensi = data.frame(res0=c(), res1=c(), stringsAsFactors=FALSE)
increasing = c("Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel")
decreasing = c("Svmicro", "Comir", "Mirdb", "Mirwalk")

for (db_name in db_name_list)
{
	AUC = data.frame()
	pAUC = data.frame()
	specif = data.frame()
	sensi = data.frame()
	for (i in 1:10) {
		file_name = paste(db_name, "_tmp_random_set_", i, ".txt", sep="")
		file_0 = file.path("resources/tmp_roc_data/random_sets", file_name)
		print(file_0)
		res0 = read.table(file_0, header = TRUE, sep = ";")

		# roc.res0 is a list
		roc.res0 = roc(label~score, res0)
		auc.res0 = auc(roc.res0)
		tmp_AUC = data.frame(res0=auc.res0, stringsAsFactors=FALSE)
		AUC = rbind(AUC, tmp_AUC)

		# Partial AUC
		p.auc.res0 = auc(roc.res0, partial.auc=c(1,0.9), partial.auc.focus=c("specificity"))
		tmp_pAUC = data.frame(res0=p.auc.res0, stringsAsFactors=FALSE)
		pAUC = rbind(pAUC, tmp_pAUC)

		# Get opti Sensi and specif
		best_pt_0 = coords(roc.res0, x = "best", ret=c("specificity", "sensitivity"), best.method = "closest.topleft")
		tmp_specif = data.frame(res0=best_pt_0[1], stringsAsFactors=FALSE)
		tmp_sensi = data.frame(res0=best_pt_0[2], stringsAsFactors=FALSE)
		specif = rbind(specif, tmp_specif)
		sensi = rbind(sensi, tmp_sensi)
		
	}

	all_auc = cbind.fill(all_auc, AUC, fill = NA)
	all_pauc = cbind.fill(all_pauc, pAUC, fill = NA)
	all_specif = cbind.fill(all_specif, specif, fill = NA)
	all_sensi = cbind.fill(all_sensi, sensi, fill = NA)

	names(all_auc)[names(all_auc)=="res0"] = db_name
	names(all_pauc)[names(all_pauc)=="res0"] = db_name
	names(all_specif)[names(all_specif)=="res0"] = db_name
	names(all_sensi)[names(all_sensi)=="res0"] = db_name
}
all_auc$init = NULL
all_pauc$init = NULL
all_specif$init = NULL
all_sensi$init = NULL

compute_stats = function(all_auc)
{
	sqrt_nb_sample = sqrt(nrow(all_auc))
	mean_db_all = "Mean:"
	sem_db_all = "SEM:"
	for (i in 1:ncol(all_auc))
	{
		mean_db = mean(all_auc[,i])
		sem_db = sd(all_auc[,i])/sqrt_nb_sample
		mean_db_all = paste(mean_db_all, mean_db)
		sem_db_all = paste(sem_db_all, sem_db)
	}

	print(mean_db_all)
	print(sem_db_all)

	stat_results = list()
	for (i in 2:ncol(all_auc))
	{
		stat_results[[i]] = t.test(all_auc[,1], all_auc[,i])
	}
	print(stat_results)
}

result_file = paste("resources/", db_name_list[1], "_", db_name_list[2], "_stats_results.txt", sep = "")
sink(result_file)
compute_stats(all_auc)
# compute_stats(all_pauc)
compute_stats(all_specif)
compute_stats(all_sensi)
sink()
print("I am done. Random rocker out.")

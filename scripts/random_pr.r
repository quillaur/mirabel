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
InsPack("flux")
InsPack("rowr")

library("flux")
library("rowr")

print("I am random_pr.py !")

tmp_files_list = list.files("resources/tmp_roc_data/random_sets")

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

all_pr_auc = data.frame() 
increasing = c("Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel")
decreasing = c("Svmicro", "Comir", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget")

for (db_name in db_name_list)
{
	AUC = data.frame()
	for (i in 1:10) {
		file_name = paste(db_name, "_tmp_random_set_", i, ".txt", sep="")
		file_0 = file.path("resources/tmp_roc_data/random_sets", file_name)
		print(file_0)
		res0 = read.table(file_0, header = TRUE, sep = ";")
		# print(head(res0))

		# Precision versus Recall
		# pr_df_0 = compute_pr(res0)
		pr_df_0 = data.frame(precision = res0$precision, recall = res0$recall, f_score = res0$f_score)
		auc.pr_df_0 = auc(pr_df_0$recall, pr_df_0$precision)
		tmp_AUC = data.frame(res0=auc.pr_df_0, stringsAsFactors=FALSE)
		AUC = rbind(AUC, tmp_AUC)
	}
	all_pr_auc = cbind.fill(all_pr_auc, AUC, fill = NA)
	# Rename column
	names(all_pr_auc)[names(all_pr_auc)=="res0"] = db_name
}
all_pr_auc$init = NULL

sqrt_nb_sample = sqrt(nrow(all_pr_auc))
mean_pr_db_all = "Mean:"
sem_pr_db_all = "SEM:"
for (i in 1:ncol(all_pr_auc))
{
	mean_pr_db = mean(all_pr_auc[,i])
	sem_pr_db = sd(all_pr_auc[,i])/sqrt_nb_sample
	mean_pr_db_all = paste(mean_pr_db_all, mean_pr_db)
	sem_pr_db_all = paste(sem_pr_db_all, sem_pr_db)
}

result_file = paste("resources/", db_name_list[1], "_", db_name_list[2], "_stats_pr_results.txt", sep = "")
sink(result_file)
print(all_pr_auc)
print(mean_pr_db_all)
print(sem_pr_db_all)
stat_results = list()
for (i in 2:ncol(all_pr_auc))
{
	stat_results[[i]] = t.test(all_pr_auc[,1], all_pr_auc[,i])
}
print(stat_results)
sink()
print("I am done. Random PR out.")
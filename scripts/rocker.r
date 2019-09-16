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
InsPack("gplots")
InsPack("pROC")
InsPack("rowr")
library("gplots")
library("pROC")
library("rowr")

print("I am rocker.py !")
ori_files_list = list.files("resources/tmp_roc_data")
tmp_files_list = c()
db_name_list = c()
for (file in ori_files_list) 
{	
	file = file.path("resources/tmp_roc_data", file)
	if (file_test("-f", file)) 
	{
		tmp_files_list = c(tmp_files_list, file)

		# db_name = strsplit(file, "_tmp")[[1]][1]
		# db_name = strsplit(db_name, "_data/")[[1]][2]
		# if (!(db_name %in% db_name_list)) 
		# {
		# 	db_name_list = c(db_name_list, db_name)
		# }
	}
}

# print(tmp_files_list)
all_auc = data.frame()
all_pauc = data.frame()
# increasing = c("Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel", "Rna22")
# decreasing = c("Svmicro", "Comir", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget")
colors = c("darkgreen", "black", "blue", "orange", "red")
auc_print_int = c(0.5, 0.4, 0.3, 0.2, 0.1)

print("ROC curve plot initiated...")
jpeg(paste("static/", db_name_list[1], "_", db_name_list[2], "_roc.jpg", sep = ""), width = 8, height = 8, units = 'in', res = 300)
db_number = 1

for (file in tmp_files_list) {
	db = strsplit(file, "/")[[1]][3]
	db_name = gsub("_tmp_roc_data.txt","", db)
	if (!(db_name %in% db_name_list)) 
	{
		db_name_list = c(db_name_list, db_name)
	}
	print(file)
	res0 = read.table(file, header = TRUE, sep = ";")

	# if (db_name %in% decreasing) {
	# 	res0 = res0[order(res0$score, decreasing = TRUE),]
	# } else {
	# 	res0 = res0[order(res0$score, decreasing = FALSE),]
	# }

	# print(head(res0))

	# roc.res0 is a list
	roc.res0 = roc(label~score, res0)
	
	if (db_number > 1) {
		par(fig = c(0,1,0,1), new = TRUE)
		plot(roc.res0, type="l", col= colors[db_number])
		roc2 = roc.res0
	} else {
		plot(roc.res0, type="l", col= colors[db_number])
		roc1 = roc.res0
	}
	
	db_number = db_number + 1
	
	auc.res0 = auc(roc.res0)
	AUC = data.frame(res0 = auc.res0)
	all_auc = cbind.fill(all_auc, AUC, fill = NA)
	# Rename column
	names(all_auc)[names(all_auc)=="res0"] = db_name

	# Partial AUC
	p.auc.res0 = auc(roc.res0, partial.auc=c(1,0.9), partial.auc.focus=c("specificity"))
	pAUC = data.frame(res0 = p.auc.res0)
	all_pauc = cbind.fill(all_pauc, pAUC, fill = NA)
	# Rename column
	names(all_pauc)[names(all_pauc)=="res0"] = db_name
}
interaction_number = nrow(res0)
title(paste(interaction_number, "common interactions"), col = "black", font = 5, line = -1)
legend("topright", inset=.05, fill=colors[1:3], horiz=FALSE, legend = c(db_name_list), text.col = colors[1:3])
dev.off()
print("ROC curve plot done.")
all_auc$init = NULL
all_pauc$init = NULL
result_file = paste("resources/", db_name_list[1], "_", db_name_list[2], "_roc_results.txt", sep = "")
sink(result_file)
print(all_auc)
print(all_pauc)
sink()

print(all_auc)
print(all_pauc)

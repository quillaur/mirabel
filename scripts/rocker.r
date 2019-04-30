#! /usr/bin/Rscript

## Statistic analysis

library("gplots")
library("pROC")
library("rowr")

tmp_files_list = list.files("resources/tmp_roc_data")
all_auc = data.frame()
all_pauc = data.frame()
increasing = c("Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel")
colors = c("darkgreen", "black", "blue", "orange", "red")
auc_print_int = c(0.5, 0.4, 0.3, 0.2, 0.1)

db_name_list = c()
for (file in tmp_files_list) {
	file = file.path("resources/tmp_roc_data", file)
	db = strsplit(file, "/")[[1]][3]
	db_name = strsplit(db, "_")[[1]][1]
	db_name_list = c(db_name_list, db_name)
}

print("ROC curve plot initiated...")
jpeg(paste(db_name_list[1], "_", db_name_list[2], "_roc.jpg"), width = 8, height = 8, units = 'in', res = 300)
i = 1

for (file in tmp_files_list) {
	file = file.path("resources/tmp_roc_data", file)
	db = strsplit(file, "/")[[1]][3]
	db_name = strsplit(db, "_")[[1]][1]
	res0 = read.table(file, header = TRUE, sep = ";")
	# res0 = head(res0, 50000)
	
	if (db_name %in% increasing) {
		res0 = res0[order(res0$score, decreasing = FALSE),]
	} else {
		res0 = res0[order(res0$score, decreasing = TRUE),]
	}

	# roc.res0 is a list
	roc.res0 = roc(label~score, res0)
	
	if (i > 1) {
		par(fig = c(0,1,0,1), new = TRUE)
		plot(roc.res0, type="l", col= colors[i], print.auc=TRUE, print.auc.y=auc_print_int[i], print.auc.pattern=paste(db_name, ": AUC = %.3f"))
		roc2 = roc.res0
	} else {
		plot(roc.res0, type="l", col= colors[i], print.auc=TRUE, print.auc.y=auc_print_int[i], print.auc.pattern=paste(db_name, ": AUC = %.3f"))
		roc1 = roc.res0
	}
	
	i = i + 1
	
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
dev.off()
print("ROC curve plot done.")
all_auc$init = NULL
all_pauc$init = NULL
print(head(all_auc))
print(head(all_pauc))

# Test 2 ROC
test.roc.0 = roc.test(roc1, roc2, method=c("bootstrap"), boot.n = 100, boot.stratified = TRUE)
print(test.roc.0)
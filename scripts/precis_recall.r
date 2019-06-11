#! /usr/bin/Rscript
library("flux")
library("rowr")

print("I am preci_recall.r !")
ori_files_list = list.files("resources/tmp_roc_data")
tmp_files_list = c()
db_name_list = c()
for (file in ori_files_list) 
{	
	file = file.path("resources/tmp_roc_data", file)
	if (file_test("-f", file)) 
	{
		tmp_files_list = c(tmp_files_list, file)

		db_name = strsplit(file, "_tmp")[[1]][1]
		db_name = strsplit(db_name, "_data/")[[1]][2]
		if (!(db_name %in% db_name_list)) 
		{
			db_name_list = c(db_name_list, db_name)
		}
	}
}

# print(tmp_files_list)
all_auc = data.frame()
all_pauc = data.frame()
increasing = c("Targetscan", "Miranda", "Pita", "Mirmap", "Mirabel")
decreasing = c("Svmicro", "Comir", "Mirdb", "Mirwalk")
colors = c("darkgreen", "black", "blue", "orange", "red")
auc_print_int = c(0.5, 0.4, 0.3, 0.2, 0.1)

print("PR curve plot initiated...")
jpeg(paste("static/", db_name_list[1], "_", db_name_list[2], "_pr.jpg", sep = ""), width = 8, height = 8, units = 'in', res = 300)
db_number = 1
f_score_df = data.frame()

for (file in tmp_files_list) 
{
	db = strsplit(file, "/")[[1]][3]
	db_name = gsub("_tmp_roc_data.txt","", db)
	print(file)
	res0 = read.table(file, header = TRUE, sep = ";")
	
	pr_df = data.frame(precision = res0$precision, recall = res0$recall, f_score = res0$f_score)

	tmp_f_score = data.frame(res0 = pr_df$f_score)
	f_score_df = cbind.fill(f_score_df, tmp_f_score, fill = NA)
	names(f_score_df)[names(f_score_df)=="res0"] = db_name
	
    if (db_number > 1) {
		par(fig = c(0,1,0,1), new = TRUE)
		plot(x = pr_df$recall, y = pr_df$precision, type="l", col= colors[db_number], xlim = c(0, 1), ylim = c(0, 1), xlab="Recall", ylab="Precision")
	} else {
		plot(x = pr_df$recall, y = pr_df$precision, type="l", col= colors[db_number], xlim = c(0, 1), ylim = c(0, 1), xlab="Recall", ylab="Precision")
	}
	db_number = db_number + 1

	auc.pr_df= auc(pr_df$recall, pr_df$precision)
	AUC = data.frame(res0 = auc.pr_df)
	all_auc = cbind.fill(all_auc, AUC, fill = NA)
	# Rename column
	names(all_auc)[names(all_auc)=="res0"] = db_name
}
interaction_number = nrow(res0)
title(paste(interaction_number, "common interactions"), col = "black", font = 5, line = -1)
legend("topright", inset=.05, fill=colors[1:3], horiz=FALSE, legend = c(db_name_list), text.col = colors[1:3])
dev.off()
print("PR curve plot done.")
all_auc$init = NULL
f_score_df$init = NULL

jpeg(paste("static/", db_name_list[1], "_", db_name_list[2], "_f_score.jpg", sep = ""), width = 8, height = 8, units = 'in', res = 300)
plot(x = seq(1, interaction_number), y = f_score_df[,1], type="l", col= colors[1], ylim = c(0, 1), xlab="Rank of targets", ylab="F-score")
par(fig = c(0,1,0,1), new = TRUE)
plot(x = seq(1, interaction_number), y = f_score_df[,2], type="l", col= colors[2], ylim = c(0, 1), xlab="Rank of targets", ylab="F-score")
title(paste(interaction_number, "common interactions"), col = "black", font = 5, line = -1)
legend("topright", inset=.05, fill=colors[1:3], horiz=FALSE, legend = c(db_name_list), text.col = colors[1:3])
dev.off()

all_f_scores = data.frame(top_predictions = c('10%','20%','40%','100%'))
for (i in 1:ncol(f_score_df))
{
	f_vector = c()
	for (val in c(10,20,40,100))
	{
		interactions = (interaction_number*val)/100
		f_sum_score = sum(f_score_df[1:interactions,i])/interactions
		f_vector = c(f_vector, f_sum_score)
	}
	tmp_f_score = data.frame(res0 = f_vector)
	all_f_scores = cbind.fill(all_f_scores, tmp_f_score, fill = NA)
	names(f_score_df)[names(f_score_df)=="res0"] = colnames(f_score_df)[i]
}

print(head(all_auc))
print(head(f_score_df))
print(head(all_f_scores))

result_file = paste("resources/", db_name_list[1], "_", db_name_list[2], "_pr_results.txt", sep = "")
sink(result_file)
print(head(all_auc))
print(head(f_score_df))
print(head(all_f_scores))
sink()

#! /usr/bin/Rscript
library("methods")
library(RobustRankAggreg)

data = read.csv("/home/quillaur/github_projects/mirabel/resources/tmp_predictions_lists.csv", header = TRUE, sep = ";")
headers = colnames(data, do.NULL = TRUE, prefix = "col")

glist = list()
for (x in 1:ncol(data)) {
	# Predictions need to be a list of strings
	predictions = as.character(data[,x][!is.na(data[,x])])

	# Make a list of lists for aggregation input
	glist[x] = list(predictions)
}

res0 = aggregateRanks(glist, method = "mean")
colnames(res0) = c("gene","mean")
row.names(res0) = NULL

write.table(res0, "resources/tmp_aggregation.txt", sep = "\t", quote=FALSE, row.names=FALSE)
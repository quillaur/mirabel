from flask import Flask, render_template, request, Response, url_for, redirect
import os
import sys
import mysql.connector
# import pandas
from ast import literal_eval
import shutil

# My specific imports
from scripts import utilities
from scripts.aggregater import Aggregator
from scripts.rocker import Rocker
# dir_path = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(os.path.join(dir_path, "core"))

app = Flask(__name__)


@app.route('/main_page', methods=["GET", "POST"])
def main_page():
    if request.method == "POST":
        if request.form["submit_button"] == "Delete":
            db_names = request.form.getlist("db_name")
            for db_name in db_names:
                db_name = db_name.split(":")[0]
                utilities.delete_table(db_name)

            # existing_mirabels is a list of lists
            mirabels = utilities.get_existing_mirabels()
            # Reformat for html purpose
            existing_mirabels = reformat_list_for_html(mirabels)

            return render_template("main_page.html", existing_mirabels = existing_mirabels)

        if request.form["submit_button"] == "View metrics":
            db_names = request.form.getlist("db_name")
            db_name = db_names[0].split(":")[0]
            databases = [db for db in db_names[0].split(":")[1].split(" ") if db != ""]

            return redirect(url_for("aggregate_results", db_name = db_name, databases = databases))

        if request.form["submit_button"] == "Create a miRabel":
            return redirect(url_for("create_mirabel"))

        if request.form["submit_button"] == "Compare performances":
            return redirect(url_for("compare_performances"))

    # existing_mirabels is a list of lists
    mirabels = utilities.get_existing_mirabels()
    # Reformat for html purpose
    existing_mirabels = reformat_list_for_html(mirabels)

    return render_template("main_page.html", existing_mirabels = existing_mirabels)

@app.route('/create_mirabel', methods=["GET", "POST"])
def create_mirabel():
    if request.method == "POST":
        if request.form["submit_button"] == "Submit":
            databases = request.form.getlist("database")
            db_name = request.form.get("db_name")

            # Create new miRabel table
            utilities.create_mirabel_table(db_name)

            # Make aggregation
            aggregator = Aggregator(databases)
            aggregator.run(db_name)

            return redirect(url_for("aggregate_results", db_name = db_name, databases = databases))

    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget", "Rna22", "Mirdip"]
    return render_template("create_mirabel.html", db_list = db_list)

@app.route('/aggregate_results/<db_name>/<databases>', methods=["GET", "POST"])
def aggregate_results(db_name, databases):
    # existing_mirabels is a list of lists
    mirabels = utilities.get_existing_mirabels()
    # Reformat for html purpose
    existing_mirabels = reformat_list_for_html(mirabels)

    if request.method == "POST":
        if request.form["submit_button"] == "Return to main page":
            return render_template("main_page.html", existing_mirabels = existing_mirabels)
    
    # Get metrics
    interaction_number, mir_number, gene_number, validated_number = utilities.get_mirabel_metrics(db_name)

    return render_template("aggregation_page.html", existing_mirabels = existing_mirabels, name = db_name, databases = databases, interaction_number = interaction_number, mir_number = mir_number, gene_number = gene_number, validated_number = validated_number)

@app.route('/compare_performances', methods=["GET", "POST"])
def compare_performances():
    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget", "Rna22", "Mirdip"]
    # existing_mirabels is a list of lists
    mirabels = utilities.get_existing_mirabels()

    for mirabel in mirabels:
        db_list.append(mirabel[0])

    # Get existing comparisons
    comparisons = get_existing_comparisons()

    if request.method == "POST":
        # if request.form["submit_button"] == "Return to perf comparisons":
        #     return render_template("compare_performances.html", db_list = db_list)

        if request.form["submit_button"] == "Compare":
            db_main = request.form.get("miRabel")
            db_comp = request.form.getlist("compare")

            # Clean tmp roc data
            clean_tmp_roc_data("resources/tmp_roc_data")
            clean_tmp_roc_data("resources/tmp_roc_data/random_sets")

            # Check that ROC image does not already exists
            for db in db_comp:
                file = "static/{}_{}_roc.jpg".format(db_main, db) 
                if os.path.isfile(file):
                    os.remove(file)

            # Make ROC analysis
            rocker = Rocker(db_main, db_comp)
            success = rocker.run()

            # Print results only for successful analysis
            if success:
                return redirect(url_for("performances_results", db_name = db_main, db_comp = db_comp))
            else:
                print("WARNING: No common interaction between {} and {}!".format(db_main, db_comp))
                return render_template("performances_failed.html")

        elif request.form["submit_button"] == "View":
            comparison = request.form.get("comparisons")
            db_list = comparison.split(" vs ")
            db_main = db_list[0]
            db_comp = db_list[1].split(" and ")

            return redirect(url_for("performances_results", db_name = db_main, db_comp = db_comp))

        elif request.form["submit_button"] == "Delete":
            db_names = request.form.getlist("comparisons")

            for db_name in db_names:
                db_list = db_name.split(" vs ")
                db_main = db_list[0]
                db_comp = db_list[1].split(" and ")

                dir_path = "{}_vs_{}".format(db_main, "_".join(db_comp))
                paths_to_del = [os.path.join("resources/already_done_comparisons", dir_path), os.path.join("static/already_done_comparisons", dir_path)]

                for path in paths_to_del:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)

            return redirect(url_for("compare_performances"))

    return render_template("compare_performances.html", db_list = db_list, comparisons = comparisons)

@app.route('/performances_results/<db_name>/<db_comp>', methods=["GET", "POST"])
def performances_results(db_name, db_comp):
    db_comp = literal_eval(db_comp)
    formated_comp_db = "_".join(db_comp)
    perm_data_dir = os.path.join("resources/already_done_comparisons", "{}_vs_{}".format(db_name, formated_comp_db))
    perm_img_dir = os.path.join("static/already_done_comparisons", "{}_vs_{}".format(db_name, formated_comp_db))
    crop_perm_img_dir = perm_img_dir.replace("static/", "")

    img_list = [os.path.join(crop_perm_img_dir, file) for root, dirs, files in os.walk(perm_img_dir) for file in files]

    # ROC stats
    db = db_comp[0]
    stats_files_list = [os.path.join(perm_data_dir, file) for root, dirs, files in os.walk(perm_data_dir) for file in files]
    
    for file in stats_files_list:
        if "_roc_results" in file:
            stats_file = file
            break

    if os.path.isfile(stats_file):
        with open(stats_file, "r") as my_file:
            handle = my_file.read()
            lines = handle.split("\n")
            for i, line in enumerate(lines):
                if i == 0:
                    header = [x for x in line.split(" ") if x != ""]
                    # Need to order properly results according to comparisons made
                    ordered_indices = [header.index(db_name)]
                    ordered_indices.extend(header.index(db) for db in db_comp)
                elif i == 1:
                    elems = [x for x in line.split(" ") if x != ""]
                    del elems[0]
                    roc_auc = " // ".join(reordering_list(elems, ordered_indices))

                elif i == 3:
                    elems = [x for x in line.split(" ") if x != ""]
                    del elems[0]
                    p_roc_auc = " // ".join(reordering_list(elems, ordered_indices))

    for file in stats_files_list:
        if "_pr_results" in file and "stats" not in file:
            stats_file = file
            break

    f_score_res = {
        10: None,
        20: None,
        40: None,
        100: None
    }
    if os.path.isfile(stats_file):
        with open(stats_file, "r") as my_file:
            handle = my_file.read()
            lines = handle.split("\n")
            for i, line in enumerate(lines):
                if i == 1:
                    elems = [x for x in line.split(" ") if x != ""]
                    del elems[0]
                    pr_auc = " // ".join(reordering_list(elems, ordered_indices))

                elif i > 9:
                    elems = [item for item in line.split(" ") if item != ""]
                    if elems:
                        percent = int(elems[1].replace("%", ""))
                        f_score_res[percent] = " // ".join(reordering_list(elems[2:], ordered_indices))

    auc_stats = []
    auc_stats.append("##################################")
    auc_stats.append("####### {} VS {} #######".format(db_name, " and ".join(db_comp)))
    auc_stats.append("##################################")
    auc_stats.append("ROC_AUC: {}".format(roc_auc))
    auc_stats.append("----------------------------------")
    auc_stats.append("ROC_pAUC: {}".format(p_roc_auc))
    auc_stats.append("----------------------------------")
    auc_stats.append("PR_AUC: {}".format(pr_auc))
    auc_stats.append("----------------------------------")
    auc_stats.append("F_scores:")
    auc_stats.append("\t - 10%: {}".format(f_score_res[10]))
    auc_stats.append("\t - 20%: {}".format(f_score_res[20]))
    auc_stats.append("\t - 40%: {}".format(f_score_res[40]))
    auc_stats.append("\t - 100%: {}".format(f_score_res[100]))

    # Random set statistics
    for file in stats_files_list:
        if "_stats_results" in file:
            stats_file = file
            break

    values_dict = {
        "mean": {
            "auc": None,
            "spe": None,
            "sen": None
        },
        "sem": {
            "auc": None,
            "spe": None,
            "sen": None
        },
        "p_val": {
            "auc": [],
            "spe": [],
            "sen": []
        }
    }
    if os.path.isfile(stats_file):
        with open(stats_file, "r") as my_file:
            handle = my_file.read()
            lines = handle.split("\n")
            for i, line in enumerate(lines):
                if "Mean" in line:
                    line = line.replace('"', '')
                    elems = [item for item in line.split(" ") if item != ""]
                    del elems[:2]
                    if not values_dict["mean"]["auc"]:
                        values_dict["mean"]["auc"] = " // ".join(reordering_list(elems, ordered_indices))
                    elif not values_dict["mean"]["spe"]:
                        values_dict["mean"]["spe"] = " // ".join(reordering_list(elems, ordered_indices))
                    elif not values_dict["mean"]["sen"]:
                        values_dict["mean"]["sen"] = " // ".join(reordering_list(elems, ordered_indices))
                elif "SEM" in line:
                    line = line.replace('"', '')
                    elems = [item for item in line.split(" ") if item != ""]
                    del elems[:2]
                    if not values_dict["sem"]["auc"]:
                        values_dict["sem"]["auc"] = " // ".join(reordering_list(elems, ordered_indices))
                    elif not values_dict["sem"]["spe"]:
                        values_dict["sem"]["spe"] = " // ".join(reordering_list(elems, ordered_indices))
                    elif not values_dict["sem"]["sen"]:
                        values_dict["sem"]["sen"] = " // ".join(reordering_list(elems, ordered_indices))
                elif "p-value" in line:
                    if len(values_dict["p_val"]["auc"]) < len(db_comp):
                        values_dict["p_val"]["auc"].append([item for item in line.split(" ") if item != ""][-1])
                    elif len(values_dict["p_val"]["spe"]) < len(db_comp):
                        values_dict["p_val"]["spe"].append([item for item in line.split(" ") if item != ""][-1])
                    elif len(values_dict["p_val"]["sen"]) < len(db_comp):
                        values_dict["p_val"]["sen"].append([item for item in line.split(" ") if item != ""][-1])

    auc_stats.append("##################################")
    auc_stats.append("###### STATSTICS ON RANDOM SETS #######")
    auc_stats.append("##################################")
    auc_stats.append("####### {} VS {} #######".format(db_name, " and ".join(db_comp)))
    auc_stats.append("##################################")
    auc_stats.append("Mean AUC: {}".format(values_dict["mean"]["auc"]))
    auc_stats.append("SEM: {}".format(values_dict["sem"]["auc"]))
    auc_stats.append("p-value: {}".format(" // ".join(values_dict["p_val"]["auc"])))
    auc_stats.append("----------------------------------")
    auc_stats.append("Mean specificity: {}".format(values_dict["mean"]["spe"]))
    auc_stats.append("SEM: {}".format(values_dict["sem"]["spe"]))
    auc_stats.append("p-value: {}".format(" // ".join(values_dict["p_val"]["spe"])))
    auc_stats.append("----------------------------------")
    auc_stats.append("Mean sensibility: {}".format(values_dict["mean"]["sen"]))
    auc_stats.append("SEM: {}".format(values_dict["sem"]["sen"]))
    auc_stats.append("p-value: {}".format(" // ".join(values_dict["p_val"]["sen"])))

    return render_template("performances_results.html", img_list = img_list, auc_stats = auc_stats)


# Other functions
def reformat_list_for_html(db_list):
    result_list = []
    for row in db_list:
        tmp_str = str(row[0]) + ": "
        for db in row[1:]:
            tmp_str = tmp_str + db + " "

        result_list.append(tmp_str)

    return result_list


def clean_tmp_roc_data(mypath):
    files_list = [os.path.join(mypath, file) for file in os.listdir(mypath)]

    for file in files_list:
        if os.path.isfile(file):
            os.remove(file)


def get_existing_comparisons():
    directories_list = [directory for root, directories, files in os.walk("resources/already_done_comparisons") for directory in directories]
    comparisons = []
    for directory in directories_list:
        db_list = directory.split("_vs_")
        db_compared = db_list[1].split("_")
        if len(db_compared) > 1:
            db_compared = " and ".join(db_compared)
            comparisons.append("{} vs {}".format(db_list[0], db_compared))
        else:
            comparisons.append("{} vs {}".format(db_list[0], db_compared[0]))

    return comparisons

def reordering_list(unordered_list: list, index_list: list):
    return [unordered_list[i] for i in index_list]


if __name__ == '__main__':
    app.run(debug=True)
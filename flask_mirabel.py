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

            # Add this new miRabel to tracking table
            utilities.insert_to_existing_mirabels(db_name, databases)

            return redirect(url_for("aggregate_results", db_name = db_name, databases = databases))

    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget"]
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
    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirdb", "Mirwalk", "Mbstar", "Exprtarget"]
    # existing_mirabels is a list of lists
    mirabels = utilities.get_existing_mirabels()

    for mirabel in mirabels:
        db_list.append(mirabel[0])

    # Get existing comparisons
    comparisons = get_existing_comparisons()

    if request.method == "POST":
        # if request.form["submit_button"] == "Return to perf comparisons":
        #     return render_template("compare_performances.html", db_list = db_list)

        if request.form["submit_button"] == "One by one" or request.form["submit_button"] == "All in one":
            all_in_one = False if request.form["submit_button"] == "One by one" else True
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
            rocker = Rocker(db_main, db_comp, all_in_one)
            success = rocker.run()

            # Print results only for successful analysis
            if success:
                return redirect(url_for("performances_results", db_name = db_main, db_comp = db_comp, all_in_one=all_in_one))
            else:
                print("WARNING: No common interaction between {} and {}!".format(db_main, db_comp))
                return render_template("performances_failed.html")

        elif request.form["submit_button"] == "View":
            comparison = request.form.get("comparisons")
            db_list = comparison.split(" vs ")
            db_main = db_list[0]
            db_comp = db_list[1].split(" and ")
            del db_comp[-1]
            all_in_one = comparison.split("all in one = ")[-1]

            return redirect(url_for("performances_results", db_name = db_main, db_comp = db_comp, all_in_one=all_in_one))

        elif request.form["submit_button"] == "Delete":
            db_names = request.form.getlist("comparisons")

            for db_name in db_names:
                db_list = db_name.split(" vs ")
                db_main = db_list[0]
                db_comp = db_list[1].split(" and ")
                del db_comp[-1]
                all_in_one = db_name.split("all in one = ")[-1]

                dir_path = "{}_vs_{}_{}".format(db_main, "_".join(db_comp), all_in_one)
                paths_to_del = [os.path.join("resources/already_done_comparisons", dir_path), os.path.join("static/already_done_comparisons", dir_path)]

                for path in paths_to_del:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)

            return redirect(url_for("compare_performances"))

    return render_template("compare_performances.html", db_list = db_list, comparisons = comparisons)

@app.route('/performances_results/<db_name>/<db_comp>/<all_in_one>', methods=["GET", "POST"])
def performances_results(db_name, db_comp, all_in_one):
    db_comp = literal_eval(db_comp)
    formated_comp_db = "_".join(db_comp)
    perm_data_dir = os.path.join("resources/already_done_comparisons", "{}_vs_{}_{}".format(db_name, formated_comp_db, all_in_one))
    perm_img_dir = os.path.join("static/already_done_comparisons", "{}_vs_{}_{}".format(db_name, formated_comp_db, all_in_one))
    crop_perm_img_dir = perm_img_dir.replace("static/", "")

    all_in_one = True if all_in_one == "True" else False
    if not all_in_one:
        img_list = [os.path.join(crop_perm_img_dir, "{}_{}_roc.jpg".format(db_name, db_compared)) for db_compared in db_comp]
        for db_compared in db_comp:
            img_list.append(os.path.join(crop_perm_img_dir, "{}_{}_pr.jpg".format(db_name, db_compared)))
            img_list.append(os.path.join(crop_perm_img_dir, "{}_{}_f_score.jpg".format(db_name, db_compared)))

        auc_stats = []
        auc_stats.append("##################################")
        auc_stats.append("##### RESULTS ON ALL COMMON DATA ######")
        auc_res = {}
        p_auc_res = {}
        pr_auc_res = {}
        f_score_res = {
            db_name: {
                10: None,
                20: None,
                40: None,
                100: None
            }
        }
        for db in db_comp:
            auc_res[db_name] = ""
            auc_res[db] = ""
            p_auc_res[db_name] = ""
            p_auc_res[db] = ""
            pr_auc_res[db_name] = ""
            pr_auc_res[db] = ""
            stats_file = os.path.join(perm_data_dir, "{}_{}_roc_results.txt".format(db_name, db))
            if os.path.isfile(stats_file):
                with open(stats_file, "r") as my_file:
                    handle = my_file.read()
                    lines = handle.split("\n")
                    for i, line in enumerate(lines):
                        if i == 1:
                            line_elems = [x for x in line.split(" ") if x != ""]
                            auc_res[db_name] = round(float(line_elems[1]), 3)
                            auc_res[db] = round(float(line_elems[2]), 3)
                        elif i == 3:
                            line_elems = [x for x in line.split(" ") if x != ""]
                            p_auc_res[db_name] = round(float(line_elems[1]), 3)
                            p_auc_res[db] = round(float(line_elems[2]), 3)

            stats_file = os.path.join(perm_data_dir, "{}_{}_pr_results.txt".format(db_name, db))
            f_score_res[db] = {
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
                            line_elems = [x for x in line.split(" ") if x != ""]
                            pr_auc_res[db_name] = round(float(line_elems[1]), 3)
                            pr_auc_res[db] = round(float(line_elems[2]), 3)
                        elif i > 9:
                            possibilities = [item for item in line.split(" ") if item != ""]
                            if possibilities:
                                percent = int(possibilities[1].replace("%", ""))
                                f_score_res[db_name][percent] = round(float(possibilities[2]), 3)
                                f_score_res[db][percent] = round(float(possibilities[3]), 3)
                        
            else:
                print("File NOT found: {} ".format(stats_file))

            auc_stats.append("##################################")
            auc_stats.append("####### {} VS {} #######".format(db_name, db))
            auc_stats.append("##################################")
            auc_stats.append("ROC_AUC: {} {}".format(auc_res[db_name], auc_res[db]))
            auc_stats.append("----------------------------------")
            auc_stats.append("ROC_pAUC: {} {}".format(p_auc_res[db_name], p_auc_res[db]))
            auc_stats.append("----------------------------------")
            auc_stats.append("PR_AUC: {} {}".format(pr_auc_res[db_name], pr_auc_res[db]))
            auc_stats.append("----------------------------------")
            auc_stats.append("F_scores:")
            auc_stats.append("\t - 10%: {} {}".format(f_score_res[db_name][10], f_score_res[db][10]))
            auc_stats.append("\t - 20%: {} {}".format(f_score_res[db_name][20], f_score_res[db][20]))
            auc_stats.append("\t - 40%: {} {}".format(f_score_res[db_name][40], f_score_res[db][40]))
            auc_stats.append("\t - 100%: {} {}".format(f_score_res[db_name][100], f_score_res[db][100]))

        # Get statistics
        auc_stats.append("##################################")
        auc_stats.append("###### STATSTICS ON RANDOM SETS #######")
        db_results = {
            db_name: {
                "roc_auc": "",
                "sem_auc": "",
                "p_val": "",
                "specificity": "",
                "sem_spe": "",
                "p_val_spe": "",
                "sensibility": "",
                "sem_sensi": "",
                "p_val_sen": ""
            }
        }
        for db in db_comp:
            db_results[db] = {
                "roc_auc": "",
                "sem_auc": "",
                "p_val": "",
                "specificity": "",
                "sem_spe": "",
                "p_val_spe": "",
                "sensibility": "",
                "sem_sensi": "",
                "p_val_sen": ""
            }
            stats_file = os.path.join(perm_data_dir, "{}_{}_stats_results.txt".format(db_name, db))
            if os.path.isfile(stats_file):
                with open(stats_file, "r") as my_file:
                    handle = my_file.read()
                    lines = handle.split("\n")
                    for i, line in enumerate(lines):
                        line = line.replace('"', '')
                        if i < 18:
                            if "Mean" in line:
                                db_results[db_name]["roc_auc"] = round(float(line.split(" ")[2]), 3)
                                db_results[db]["roc_auc"] = round(float(line.split(" ")[3]), 3)
                            elif "SEM" in line:
                                db_results[db_name]["sem_auc"] = round(float(line.split(" ")[2]), 4)
                                db_results[db]["sem_auc"] = round(float(line.split(" ")[3].replace('"', '')), 4)
                            elif "p-value" in line:
                                try:
                                    db_results[db_name]["p_val"] = float(line.split("p-value = ")[1])
                                    db_results[db]["p_val"] = float(line.split("p-value = ")[1])
                                except:
                                    db_results[db_name]["p_val"] = float(line.split("p-value < ")[1])
                                    db_results[db]["p_val"] = float(line.split("p-value < ")[1])
                        elif i < 37:
                            if "Mean" in line:
                                db_results[db_name]["specificity"] = round(float(line.split(" ")[2]), 3)
                                db_results[db]["specificity"] = round(float(line.split(" ")[3]), 3)
                            elif "SEM" in line:
                                db_results[db_name]["sem_spe"] = round(float(line.split(" ")[2]), 4)
                                db_results[db]["sem_spe"] = round(float(line.split(" ")[3].replace('"', '')), 4)
                            elif "p-value" in line:
                                try:
                                    db_results[db_name]["p_val_spe"] = float(line.split("p-value = ")[1])
                                    db_results[db]["p_val_spe"] = float(line.split("p-value = ")[1])
                                except:
                                    db_results[db_name]["p_val_spe"] = float(line.split("p-value < ")[1])
                                    db_results[db]["p_val_spe"] = float(line.split("p-value < ")[1])
                        elif i > 37:
                            if "Mean" in line:
                                db_results[db_name]["sensibility"] = round(float(line.split(" ")[2]), 3)
                                db_results[db]["sensibility"] = round(float(line.split(" ")[3]), 3)
                            elif "SEM" in line:
                                db_results[db_name]["sem_sensi"] = round(float(line.split(" ")[2]), 4)
                                db_results[db]["sem_sensi"] = round(float(line.split(" ")[3].replace('"', '')), 4)
                            elif "p-value" in line:
                                try:
                                    db_results[db_name]["p_val_sen"] = float(line.split("p-value = ")[1])
                                    db_results[db]["p_val_sen"] = float(line.split("p-value = ")[1])
                                except:
                                    db_results[db_name]["p_val_sen"] = float(line.split("p-value < ")[1])
                                    db_results[db]["p_val_sen"] = float(line.split("p-value < ")[1])

            auc_stats.append("##################################")
            auc_stats.append("####### {} VS {} #######".format(db_name, db))
            auc_stats.append("##################################")
            auc_stats.append("Mean AUC: {} {}".format(db_results[db_name]["roc_auc"], db_results[db]["roc_auc"]))
            auc_stats.append("SEM: {} {}".format(db_results[db_name]["sem_auc"], db_results[db]["sem_auc"]))
            auc_stats.append("p-value: {}".format(db_results[db_name]["p_val"]))
            auc_stats.append("----------------------------------")
            auc_stats.append("Mean specificity: {} {}".format(db_results[db_name]["specificity"], db_results[db]["specificity"]))
            auc_stats.append("SEM: {} {}".format(db_results[db_name]["sem_spe"], db_results[db]["sem_spe"]))
            auc_stats.append("p-value: {}".format(db_results[db_name]["p_val_spe"]))
            auc_stats.append("----------------------------------")
            auc_stats.append("Mean sensibility: {} {}".format(db_results[db_name]["sensibility"], db_results[db]["sensibility"]))
            auc_stats.append("SEM: {} {}".format(db_results[db_name]["sem_sensi"], db_results[db]["sem_sensi"]))
            auc_stats.append("p-value: {}".format(db_results[db_name]["p_val_sen"]))

        return render_template("performances_results.html", img_list = img_list, auc_stats = auc_stats)
    else:
        img_list = []
        for db_compared in db_comp:
            img_list.append(os.path.join(crop_perm_img_dir, "{}_{}_roc.jpg".format(db_name, db_compared)))
            img_list.append(os.path.join(crop_perm_img_dir, "{}_{}_pr.jpg".format(db_name, db_compared)))
            img_list.append(os.path.join(crop_perm_img_dir, "{}_{}_f_score.jpg".format(db_name, db_compared)))
            break

        # ROC stats
        db = db_comp[0]
        stats_file = os.path.join(perm_data_dir, "{}_{}_roc_results.txt".format(db_name, db))
        if os.path.isfile(stats_file):
            with open(stats_file, "r") as my_file:
                handle = my_file.read()
                lines = handle.split("\n")
                for i, line in enumerate(lines):
                    if i == 1:
                        elems = [x for x in line.split(" ") if x != ""]
                        del elems[0]
                        roc_auc = " // ".join(elems)

                    elif i == 3:
                        elems = [x for x in line.split(" ") if x != ""]
                        del elems[0]
                        p_roc_auc = " // ".join(elems)

        stats_file = os.path.join(perm_data_dir, "{}_{}_pr_results.txt".format(db_name, db))
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
                        pr_auc = " // ".join(elems)

                    elif i > 9:
                        elems = [item for item in line.split(" ") if item != ""]
                        if elems:
                            percent = int(elems[1].replace("%", ""))
                            f_score_res[percent] = " // ".join(elems[2:])

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
        stats_file = os.path.join(perm_data_dir, "{}_{}_stats_results.txt".format(db_name, db))
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
                            values_dict["mean"]["auc"] = " // ".join(elems)
                        elif not values_dict["mean"]["spe"]:
                            values_dict["mean"]["spe"] = " // ".join(elems)
                        elif not values_dict["mean"]["sen"]:
                            values_dict["mean"]["sen"] = " // ".join(elems)
                    elif "SEM" in line:
                        line = line.replace('"', '')
                        elems = [item for item in line.split(" ") if item != ""]
                        del elems[:2]
                        if not values_dict["sem"]["auc"]:
                            values_dict["sem"]["auc"] = " // ".join(elems)
                        elif not values_dict["sem"]["spe"]:
                            values_dict["sem"]["spe"] = " // ".join(elems)
                        elif not values_dict["sem"]["sen"]:
                            values_dict["sem"]["sen"] = " // ".join(elems)
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
        all_in_one = db_compared[-1]
        del db_compared[-1]
        if len(db_compared) > 1:
            db_compared = " and ".join(db_compared)
        comparisons.append("{} vs {} and all in one = {}".format(db_list[0], db_compared, all_in_one))

    return comparisons

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, Response, url_for, redirect
import os
import sys
import mysql.connector
# import pandas
from ast import literal_eval

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
            db_name = request.form.get("db_name")
            utilities.delete_table(db_name)

            # existing_mirabels is a list of lists
            mirabels = utilities.get_existing_mirabels()
            # Reformat for html purpose
            existing_mirabels = reformat_list_for_html(mirabels)

            return render_template("main_page.html", existing_mirabels = existing_mirabels)

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

    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirdb", "Mirwalk"]
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
    db_list = ["Targetscan", "Miranda", "Pita", "Svmicro", "Comir", "Mirmap", "Mirdb", "Mirwalk"]
    # existing_mirabels is a list of lists
    mirabels = utilities.get_existing_mirabels()

    for mirabel in mirabels:
        db_list.append(mirabel[0])

    if request.method == "POST":
        if request.form["submit_button"] == "Return to perf comparisons":
            return render_template("compare_performances.html", db_list = db_list)

        if request.form["submit_button"] == "Submit":
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

    return render_template("compare_performances.html", db_list = db_list)

@app.route('/performances_results/<db_name>/<db_comp>', methods=["GET", "POST"])
def performances_results(db_name, db_comp):
    db_comp = literal_eval(db_comp)
    img_list = ["{}_{}_roc.jpg".format(db_name, db_compared) for db_compared in db_comp]

    auc_stats = []
    p_value = "computational error"
    for db in db_comp:
        stats_file = "resources/{}_{}_roc_stats.txt".format(db_name, db)
        if os.path.isfile(stats_file):
            with open(stats_file, "r") as my_file:
                handle = my_file.read()
                lines = handle.split("\n")
                for i, line in enumerate(lines):
                    if i == 7:
                        p_value = float(line)

        auc_stats.append("{} VS {} p-value = {}".format(db_name, db, p_value))

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


if __name__ == '__main__':
    app.run(debug=True)
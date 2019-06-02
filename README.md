# mirabel
Tool built to improve microRNA target predictions by aggregation method.
Coded mostly in Python3 with some R implementations as well (aggregation and ROC curve).

# TO DO
- Update public databases:
    - ~~TargetScan~~
    - ~~miRanda~~
    - ~~SVMicro~~
    - ~~PITA~~
    - ~~miRTarBase~~
    - ~~miRecord~~ (3k interactions, useless and unsupported...)
    - ~~ComiR~~ (Bug on download of the tar.gz, so taking data from crihan)
    - ~~miRmap~~
    - ~~miRDB~~
    - ~~miRWalk~~
    - ~~MBSTAR~~ (DL from crihan)
    - ~~exprtarget~~ (DL from crihan)
- ~~Aggregate newly updated data~~
- ~~Add validated labels to all data upon update~~
- Compare aggregated data to miRmap / MBStar and miRDB

# How to work on it
Pull your own branch
```shell
git clone https://github.com/quillaur/mirabel.git
cd mirabel/
git checkout develop
git pull
git checkout -b feat/<name_of_your_feat>
git push -u origin feat/<name_of_your_feat>
```
Do your work and create a merge request please.

# How to run it

## Clone repo
```shell
git clone https://github.com/quillaur/mirabel.git
cd mirabel/
```

## Install requirements
```shell
virtualenv venv -p <path_of_your_python>
source venv/bin/activate
pip install -r requirements.txt
```

## Run the program
If this is your first run:
```shell
sudo chmod +x scripts/aggregation.r
sudo chmod +x scripts/rocker.r
sudo chmod +x scripts/random_rocker.r
sudo chmod +x scripts/random_pr.r
sudo chmod +x scripts/precis_recall.r
python flask_mirabel.py
```
Otherwise:
```shell
cd <your_path_to>/mirabel/
source venv/bin/activate
python flask_mirabel.py
```
Open your favorite web browser and go to the following URL: localhost:5000/main_page


# How does it work
1. Update public databases:
    1. File URLs need to be specified in the config.
    2. Each file is being downloaded, reformated and inserted in MYSQL.
    3. Would be better to create a method which converts source files to an intermediate common file format and then to insert data into MYSQL but no time for that...

2. Aggregation: to be described...

3. Statistical analysis: to be described...
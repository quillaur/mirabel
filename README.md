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
- ~~Aggregate newly updated data~~
- Compare aggregated data to miRmap / MBStar and miRDB

# How does it work
1. Update public databases:
    1. File URLs need to be specified in the config.
    2. Each file is being downloaded, reformated and inserted in MYSQL.

2. Aggregation: to be described...

3. Statistical analysis: to be described...

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

## Run the databases update
```shell
python main.py -options
```
options:
> * -d : download files from public database website. Default is False.
> * -l or --list <db_name_1> <db_name_2> <db_name_x> : allows you to specify which databases to update. Default is all of them.
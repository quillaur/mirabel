# mirabel
Tool built to improve microRNA target predictions by aggregation method.
Coded mostly in Python3 with some R implementations as well (aggregation and ROC curve).

# TO DO
- Update public databases:
    - ~~TargetScan~~
    - miRanda
    - SVMicro
    - PITA
    - miRTarBase
    - ComiR
    - miRmap
    - miRDB
- Aggregate newly updated data
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

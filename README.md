# web-drone-project
This repository is a clone of [Webmushra](https://github.com/audiolabs/webMUSHRA) with [Pymushra](https://github.com/nils-werner/pymushra) which provides a python based backend to store results.

This project has modifications from above repository to accomodate it for our AB testing experiments. 

To generate yaml files which are need to create meta data for pages - 

First run 

`meta_data.ipynb`

followed by 

`generate_yaml.ipynb`

Add -


- [ ] Check if csv database exsists else: create one
- [ ] Better csv results file - df creation code -> `service.py` 
- [ ] Pass data config files already done to avoid copies 


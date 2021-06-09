# web-drone-project
This repository is inspired from [Webmushra](https://github.com/audiolabs/webMUSHRA) with [Pymushra](https://github.com/nils-werner/pymushra) which provides a python based backend to store results. 

This project has following key modifications from above repository to accomodate it for our AB testing experiments. 
 * Completely port to Flask based development. 
 * No need for separate WebMushra directory -  Javascript dependencies have been added to `static` folder
 * Key entry point for web app assuming `web-drone-project/pymushra/pymushra` as root is  is -> `service.py -> templates/index.html -> static/startup.js` 

Key Experiment details - 
* SNRs - `['0', '-5', '-10', '-15', '-20', '-25', '-30']`
* Number of unique noisy utturances for each model and each SNR - 15
* Number of pairs / pages each participant will see - 20 [controlled by `window` param in `generate_yaml_full.ipynb` and `generate_yaml_full-noisy_baseline_combinations.ipynb`]
* Total number of pairs - 
    * Baseline vs Input  - 105
    * Remaining algorithms - 630


 
 Audio files for this experiment are in  -
 ```
 configs/resources/Drone_Noise_Test_Data/drone_noise_out/
.
├── Clean
├── DCUNet
├── DPTNet
├── Noisy
├── RegressionFCNN
├── SMoLnet
└── WaveUNet
 ```

##  Setup steps

Please skip to bullet point 2 as I have aleady generated these meta data files. 


<h3>1.  Meta data Genration </h3> 
    If you want to generate your own meta data you will need to change paths accordingly. The current paths are based on paths from Jade and my personal PC

    `meta_data.ipynb` - Generate CSV paths for audio files for various SNRs and mdoels



    `generate_yaml_full.ipynb` - Yaml files for remaining 4 algoritms `['DCUNet', 'DPTNet', 'SMoLnet', 'WaveUNet']` 

    `generate_yaml_full-noisy_baseline_combinations.ipynb` - Yaml files for Baseline model which will be compared to Input only. 

    
        
<h3>2. Run the server locally </h3> 

    ```
    git clone https://github.com/ashish10alex/web-drone-project.git
    cd web-drone-project
    python3 -m venv .
    source bin/activate
    pip install -e pymushra
    pymushra server 

    ```
    Then open `http://localhost:5000`

<h3>3.  Database </h3>

* But the main database which we will use for evaulating results is in the root of the repository -  `database_baseline_vs_noisy.csv` and `database_other_model_combinations.csv`

* To view the results for each subset can be viewed by switching btw dropdown menus - [Error handling TBD]
   * `http://localhost:5000/result` 
 

*  To see all the results for both sets of experiments go to -  `http://localhost:5000/admin` and click on `preview`


<h2>4.  Monitor Experiments </h2>

* You can monitor the finished and remaining experiments at - `http://localhost:5000/finished`





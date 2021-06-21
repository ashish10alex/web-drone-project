import os
import os.path
import argparse
import librosa
import pandas as pd
import yaml
import random
import itertools

models = ['Clean', 'Noisy', 'DCUNet', 'DPTNet', 'RegressionFCNN', 'SMoLnet', 'WaveUNet']
snrs = ['-10', '-15', '-20', '-25']

def test_paths(root_dir, df_final=None, website=False):
    if website: 
        path_prefix = os.path.join(root_dir, 'pymushra/pymushra')
        for column in list(df_final):
            for p in df_final[str(column)]:
                _, sr = librosa.load(os.path.join(path_prefix, p), sr=8000)
    else:
        for column in list(df_final):
            for p in df_final[str(column)]:
                _, sr = librosa.load(p, sr=8000)
                
    print("Tests:  passed metadata was correctly created")

def website_specific_metadata(root_dir, snr):
    base_path_website = 'static/configs/resources/Drone_Noise_Test_Data/drone_noise_out'
    clean_files_dir = os.path.join(root_dir, 'pymushra/pymushra', base_path_website, 'Clean')
    clean_files_list = os.listdir(clean_files_dir)
    path_dict_website = {m: [] for m in models}
    
    for audio_file_clean in clean_files_list:
        basename = audio_file_clean.split('_')[-1]
        for model_name in models:
            if model_name == 'Clean':
                path = f'{base_path_website}/{model_name}/{audio_file_clean}'
            else:
                path = f'{base_path_website}/{model_name}/{snr}dB/{model_name}_{basename}'
            path_dict_website[model_name].append(path)
                
    return path_dict_website


def make_yaml_file(yaml_dir, combinations, idx_meta='0_20'):
    print(f'''
    {len(combinations)} pages will be created for subjective evalutation
    ''')
    
    final_dict_template = {
    'testname': 'AB Test',
     'testId': 'ab_noloop',
     'bufferSize': 2048,
     'stopOnErrors': True,
     'showButtonPreviousPage': True,
     'remoteService': 'service/write.php',
     'pages': []
    }
    #final page which sends results
    final_page_template =  {'type': 'finish',
       'name': 'Thank you',
       'content': 'Thank you for attending',
       'showResults': False,
       'writeResults': True,
       'questionnaire':[
           {
               'type':'text',
               'label': 'Name',
               'name': 'name'
           },
           {
               'type':'text',
               'label': 'Email',
               'name': 'email'
           },
           {
               'type':'likert',
               'name':'age',
               'label':'Age',
               'response':[
                   {'value': '0-20',
                   'label':'0 to 20',},
                    {'value': '20-40',
                   'label':'20 to 40',},
                    {'value': '20-40',
                   'label':'40 to 60',},
                    {'value': '40-60',
                   'label':'40 to 60',}
                   
               ]
           },
           {
               'type':'likert',
               'name':'gender',
               'label':'Gender',
               'response':[
                   {'value': 'female',
                   'label':'Female',},
                    {'value': 'male',
                   'label':'Male',},
                    {'value': 'other',
                   'label':'Other',},
               ]
           },
               {
               'type':'likert',
               'name':'subjective_eval_ever',
               'label':'Have you participated in audio subjective evailation before',
               'response':[
                   {'value': 'yes',
                   'label':'Yes',},
                    {'value': 'no',
                   'label':'No',},
               ]
           }
       ]
    }
    
    
    welcome_page_template = {
        'type': 'generic',
        'id': 'first_page',
        'name': 'Welcome',
        'content': '<h1>Subjective evaluation</h1><b>Welcome to AB testing framework for DRONE ego noise ehancement. You will be presented a reference audio clip and denoised audio clip from two separate algorithms. You will be required to select one of the two clips which sounds the closest to the reference audio clip. </b>'
    }
    pages=[]
    pages.append(welcome_page_template)
    for i in range(1, len(combinations)):
        pages_dict_template = {'type': 'paired_comparison',
         'id': 'trialAB2',
         'name': None,
         'unforced': None,
         'content': '',
         'showWaveform': True,
         'enableLooping': False,
         'reference': '',
         'stimuli': {'C1': '',
          'C2': ''}}
        pages.append(pages_dict_template)
        pages[i]['reference'] = combinations[i][0]
        pages[i]['stimuli']['C1'] = combinations[i][1]
        pages[i]['stimuli']['C2'] = combinations[i][2]
    
    pages.append(final_page_template)
    final_dict_template['pages'] = pages
    
    # dict to yaml
    file_name = f'idx_{idx_meta}.yaml'
#     if is_baseline:
#         file_name = 'baseline_'+file_name
    yaml_file_path = os.path.join(yaml_dir, file_name)
    with open(yaml_file_path, 'w') as f:
        yaml.dump(final_dict_template, f)
    print('Created yaml file at: ', yaml_file_path)
    
    return final_dict_template

def generate_common(root_dir):
    meta_dir = os.path.join(root_dir, 'meta_data_for_yaml')
    os.makedirs(meta_dir, exist_ok=True)
    
    for snr in snrs:
        df_dict = website_specific_metadata(root_dir, snr)
        df = pd.DataFrame.from_dict(df_dict)
        test_paths(root_dir, df, website=True)
        df.to_csv(os.path.join(meta_dir, f'website_meta_data_snr_{snr}dB.csv'))
    
    print('Metadata generated successfully')

    
def get_combinations_of_index(df, idx):
    #all wavs except for the input to create combinations
    #Input will be our reference
    denoised_list = list(df.iloc[idx])[1:]
    #create pairs of twos
    #e.g. - (WaveUNet_SX139.WAV.n121.wav, RegressionFCNN_SX139.WAV.n121.wav) ...
    combinations = list(itertools.combinations(denoised_list, 2))

    # Final combination list with input appended to all 
    #e.g. - (input.wav, WaveUNet_SX139.WAV.n121.wav, RegressionFCNN_SX139.WAV.n121.wav) ...
    final_combination_list = []
    for c in combinations:
        #trick to append to tuple 
        c = (df.iloc[idx][0], *c)
        final_combination_list.append(c)
    return final_combination_list 

    
def generate_combinations(root_dir, yaml_folder='pages', selected_models=None):
    yaml.Dumper.ignore_aliases = lambda *args : True
    meta_dir = os.path.join(root_dir, 'meta_data_for_yaml')
    out_yaml_dir = os.path.join(root_dir, f'pymushra/pymushra/static/yamls/{yaml_folder}')
    os.makedirs(out_yaml_dir, exist_ok=True)
    
    selected_models=[
        ['Noisy', 'RegressionFCNN'],
        ['DCUNet', 'DPTNet', 'SMoLnet', 'WaveUNet'],
    ]
    
    final_list = []
    
    for model_group in selected_models:
        
        df_all_snr_dict = {}
        for snr in snrs:
            df_all_snr_dict[str(snr)] = pd.read_csv(os.path.join(meta_dir, f'website_meta_data_snr_{snr}dB.csv'),
                                                    usecols=['Clean']+model_group)

        # get big dict
        df = pd.concat([df_all_snr_dict[snr] for snr in snrs], ignore_index=True)

        final_list += [r for i in range(len(df)) for r in get_combinations_of_index(df, i)]
    
    random.seed(42)
    random.shuffle(final_list)
    print(f'Total number of pairs: {len(final_list)}')
    
    window = 40
    start  = 0
    ranges = []
    while start < len(final_list):
        if start + window > len(final_list):
            ranges.append([start, len(final_list)])
            start+=window
        else:
            ranges.append([start, start+ window])
            start +=window
            
    for start, end in ranges:
        make_yaml_file(out_yaml_dir, combinations=final_list[start:end], idx_meta=f'{start}_{end}')
    
def generate_baseline_noisy(root_dir):
    print('Generating baseline vs noisy pairs')
    generate_combinations(root_dir, ['Noisy', 'RegressionFCNN'], 'baseline_vs_noisy')
    
def generate_others(root_dir):
    print('Generation other model combinations')
    generate_combinations(root_dir, ['DCUNet', 'DPTNet', 'SMoLnet', 'WaveUNet'], 'other_model_combinations')
    
def generate_all(root_dir):
    print('Generate all of them')
    generate_combinations(root_dir)
    
def main(action_type, root_dir):
    if action_type == 'common':
        generate_common(root_dir)
    elif action_type == 'baseline_noisy':
        generate_baseline_noisy(root_dir)
    elif action_type == 'all':
        generate_all(root_dir)
    elif action_type == 'others':
        generate_others(root_dir)
    else:
        raise ValueError('Unknown action: ' + action_type)
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate metadata CSVs for subjective evaluation webapp')
    parser.add_argument('type', choices=['common', 'baseline_noisy', 'all', 'others'], help='Generation step')
    parser.add_argument('--root_dir', metavar='PATH', type=str, help='Project root directory', default=os.getcwd())
    args = parser.parse_args()
    main(args.type, args.root_dir)

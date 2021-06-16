from __future__ import division, absolute_import, print_function

import os
import sys
import json
import pickle
import pandas as pd
import random
from flask import Flask, request, jsonify, send_from_directory, send_file, \
    render_template, redirect, url_for, abort
from tinyrecord import transaction
from functools import wraps

from . import stats, casting, utils

from io import BytesIO
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

app = Flask(__name__)
os.makedirs('db', exist_ok=True)


def get_user_ip():
    headers_list = request.headers.getlist("X-Forwarded-For")
    user_ip = headers_list[0] if headers_list else request.remote_addr
    return user_ip

def only_admin_allowlist(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        print(get_user_ip(), file=sys.stderr)
        if get_user_ip() in app.config['admin_allowlist']:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return wrapped


def get_seen_yaml_files(csv_database):
    if csv_database in os.listdir():
        df_og = pd.read_csv(csv_database)
        seen_files = list(df_og['configs'].unique())
    else: seen_files = []
    return seen_files

def select_unique_yaml_files(experiment_name, csv_database):
    all_files = os.listdir(f'pymushra/pymushra/static/yamls/{experiment_name}')

    #get seen files and remove them off the the list off all files
    seen_files = get_seen_yaml_files(csv_database)

    for file in seen_files:
        if file in all_files:
            all_files.remove(file)

    return all_files, seen_files

experiment_names = ['baseline_vs_noisy', 'other_model_combinations']
database_names = [f'database_{experiment_names[0]}.csv', f'database_{experiment_names[1]}.csv']

@app.route('/')
@app.route('/<path:url>')
def home(url='index.html'):
    #Old version
    # return send_from_directory(app.config['webmushra_dir'], url )

    #New version
    # experiment_name = app.config['experiment_name']
 
    all_conf_files = []
    all_seen_files = []
    for exp_name, db_name in zip(experiment_names, database_names):
        conf_files, seen_files = select_unique_yaml_files(experiment_name=exp_name, csv_database=db_name)
        all_conf_files += conf_files
        all_seen_files += seen_files
    if len(all_conf_files) == 0: return  render_template('finished.html', seen_files=all_seen_files)

    # select a random config file which has not yet been done so far 
    conf_file = all_conf_files[random.randint(0, len(all_conf_files)-1)]
    if conf_file.split('_')[0] == 'baseline':
        conf_file_path = f'static/yamls/{experiment_names[0]}/{conf_file}'
        return render_template(url, conf_file_path=conf_file_path)
    conf_file_path = f'static/yamls/{experiment_names[1]}/{conf_file}'
    return render_template(url, conf_file_path=conf_file_path)

@app.route('/finished')
@only_admin_allowlist
def finishedExperiments():
    baseline_left_files, baseline_done_files = select_unique_yaml_files(experiment_name='baseline_vs_noisy', csv_database=f'database_{experiment_names[0]}.csv')
    others_left_files, others_done_files = select_unique_yaml_files(experiment_name='other_model_combinations', csv_database=f'database_{experiment_names[1]}.csv')
    return render_template('finished.html', baseline_left_files=baseline_left_files, baseline_done_files=baseline_done_files, others_left_files=others_left_files, others_done_files=others_done_files)

@app.route('/results', methods=['GET', 'POST'])
@only_admin_allowlist
def results():
    if request.method == 'POST':
        try:
            experiment_name = request.values.get('exp_name')
            csv_database = f'database_{experiment_name}.csv'
            df_html = pd.read_csv(csv_database).to_html()
            return render_template('results.html', df_html=df_html, experiment_name=experiment_name)
        except:
            print('Somethings wrong')
    return render_template('results.html')
    

@app.route('/service/write.php', methods=['POST'])
@app.route('/<testid>/collect', methods=['POST'])
@app.route('/collect', methods=['POST'])
def collect(testid=''):
    # csv_database = f'database_{experiment_name}.csv'
    if request.headers['Content-Type'].startswith(
            'application/x-www-form-urlencoded'
    ):
        try:
            db = app.config['db']
            payload = json.loads(request.form['sessionJSON'])
            print(payload)
            payload = casting.cast_recursively(payload)
            insert = casting.json_to_dict(payload)

            #add db here

            columns = [k for k in payload['trials'][0]['responses'][0].keys()] + ['ip']
            #contains attributes - ['name', 'email', 'age', 'gender', 'subject_eval_ever']
            for i in payload['participant']['name']:
                columns.append(i)
            participant_metadata = payload['participant']['response']

            columns.append('uuid')
            columns.append('configs')
            
            uuid = payload['trials'][0]['questionaire']['uuid']
            config = payload['config'].split('/')[-1]
            
            if config.split('_')[0] == 'baseline':
                csv_database = f'database_{experiment_names[0]}.csv'
            else: csv_database = f'database_{experiment_names[1]}.csv'
            
            uuids = []
            ips = []
            clean_references = []
            denoised_1 = []
            denoised_2 = []
            preffered_utterance = []
            snrs = []
            time = []
            configs = []
            # participant metadata
            name = []
            email = []
            age = []
            gender = []
            subjective_eval_ever = []
            confidence = []
            for i in range(len(payload['trials'][0]['responses'])):
                uuids.append(uuid)
                ips.append(get_user_ip())
                configs.append(config)
                name.append(participant_metadata[0])
                email.append(participant_metadata[1])
                age.append(participant_metadata[2])
                gender.append(participant_metadata[3])
                subjective_eval_ever.append(participant_metadata[4])
                clean_references.append(
                      payload['trials'][0]['responses'][i]['clean_reference'])
                denoised_1.append(
                     payload['trials'][0]['responses'][i]['denoised_1'])
                denoised_2.append(
                     payload['trials'][0]['responses'][i]['denoised_2'])
                snrs.append(
                     payload['trials'][0]['responses'][i]['snr'].split('/')[6])
                preffered_utterance.append(
                     payload['trials'][0]['responses'][i]['preffered_utterance'])
                confidence.append(
                     payload['trials'][0]['responses'][i]['confidence'])
                time.append(
                     payload['trials'][0]['responses'][i]['time'])

            df = pd.DataFrame(columns=columns)
            df['clean_reference'] = pd.Series(clean_references)
            df['denoised_1'] = pd.Series(denoised_1)
            df['denoised_2'] = pd.Series(denoised_2)
            df['preffered_utterance'] = pd.Series(preffered_utterance)
            df['uuid'] = pd.Series(uuids)
            df['ip'] = pd.Series(ips)
            df['time'] = pd.Series(time)
            df['configs'] = pd.Series(configs)
            df['snr'] = pd.Series(snrs)
            df['name'] = pd.Series(name)
            df['email'] = pd.Series(email)
            df['age'] = pd.Series(age)
            df['gender'] = pd.Series(gender)
            df['subjective_eval_ever'] = pd.Series(subjective_eval_ever)
            df['confidence'] = pd.Series(confidence)
            
            if csv_database in os.listdir():
                df_og = pd.read_csv(csv_database, index_col=False)
                df_og = df_og.append(df)
                df_og.to_csv(csv_database, index=False)
            else: df.to_csv(csv_database, index=False)

            collection = db.table(payload['trials'][0]['testId'])
            with transaction(collection):
                inserted_ids = collection.insert_multiple(insert)
            # print(inserted_ids)

            return jsonify({
                'error': False,
                'message': "Saved as ids %s" % ','.join(map(str, inserted_ids))
            })
        except Exception as e:
            return jsonify({
                'error': True,
                'message': "An error occurred: %s" % str(e)
            })
    else:
        return "415 Unsupported Media Type", 415


@app.route('/admin/')
@app.route('/admin/list')
@only_admin_allowlist
def admin_list():

    db = app.config['db']
    collection_names = db.tables()

    collection_dfs = [
        casting.collection_to_df(db.table(name)) for name in collection_names
    ]

    # print(collection_dfs)

    collections = [
        {
            'id': name,
            'participants': len(df['questionaire', 'uuid'].unique()),
            'last_submission': df['wm', 'date'].max(),
        } for name, df in zip(collection_names, collection_dfs)
        if len(df) > 0
    ]

#     configs = utils.get_configs(
#         os.path.join(app.config['webmushra_dir'], "configs")
#     )

    return render_template(
        "admin/list.html",
        collections=collections,
        # configs=configs
    )


@app.route('/admin/delete/<testid>')
@only_admin_allowlist
def admin_delete(testid):
    collection = app.config['db'].table(testid)
    collection.drop()

    return redirect(url_for('admin_list'))


@app.route('/admin/info/<testid>/')
@only_admin_allowlist
def admin_info(testid):
    collection = app.config['db'].table(testid)
    df = casting.collection_to_df(collection)
    try:
        configs = df['wm']['config'].unique().tolist()
    except KeyError:
        configs = []

    configs = map(os.path.basename, configs)

    return render_template(
        "admin/info.html",
        testId=testid,
        configs=configs
    )


@app.route('/admin/latest/<testid>/')
@only_admin_allowlist
def admin_latest(testid):
    collection = app.config['db'].table(testid)
    latest = sorted(collection.all(), key=lambda x: x['date'], reverse=True)[0]
    return json.dumps(latest)


@app.route('/admin/stats/<testid>/<stats_type>')
@only_admin_allowlist
def admin_stats(testid, stats_type='mushra'):
    collection = app.config['db'].table(testid)
    df = casting.collection_to_df(collection)
    df.columns = utils.flatten_columns(df.columns)
    # analyse mushra experiment
    try:
        if stats_type == "mushra":
            return stats.render_mushra(testid, df)
    except ValueError as e:
        return render_template(
            'error/error.html', type="Value", message=str(e)
        )
    return render_template('error/404.html'), 404


@app.route(
    '/admin/download/<testid>.<filetype>',
    defaults={'show_as': 'download'})
@app.route(
    '/admin/download/<testid>/<statstype>.<filetype>',
    defaults={'show_as': 'download'})
@app.route(
    '/download/<testid>/<statstype>.<filetype>',
    defaults={'show_as': 'download'})
@app.route(
    '/download/<testid>.<filetype>',
    defaults={'show_as': 'download'})
@app.route(
    '/admin/show/<testid>.<filetype>',
    defaults={'show_as': 'text'})
@app.route(
    '/admin/show/<testid>/<statstype>.<filetype>',
    defaults={'show_as': 'text'})
@only_admin_allowlist
def download(testid, show_as, statstype=None, filetype='csv'):
    allowed_types = ('csv', 'pickle', 'json', 'html')

    if show_as == 'download':
        as_attachment = True
    else:
        as_attachment = False

    if filetype not in allowed_types:
        return render_template(
            'error/error.html',
            type="Value",
            message="File type must be in %s" % ','.join(allowed_types)
        )

    if filetype == "pickle" and not as_attachment:
        return render_template(
            'error/error.html',
            type="Value",
            message="Pickle data cannot be viewed"
        )

    collection = app.config['db'].table(testid)
    df = casting.collection_to_df(collection)

    if statstype is not None:
        # subset by statstype
        df = df[df[('wm', 'type')] == statstype]

    # Merge hierarchical columns
    if filetype not in ("pickle", "html"):
        df.columns = utils.flatten_columns(df.columns.values)

    if len(df) == 0:
        return render_template(
            'error/error.html',
            type="Value",
            message="Data Frame was empty"
        )

    if filetype == "csv":
        # We need to escape certain objects in the DF to prevent Segfaults
        mem = StringIO()
        casting.escape_objects(df).to_csv(
            mem,
            sep=";",
            index=False,
            encoding='utf-8'
        )

    elif filetype == "html":
        mem = StringIO()
        df.sort_index(axis=1).to_html(mem, classes="table table-striped")

    elif filetype == "pickle":
        mem = BytesIO()
        pickle.dump(df, mem)

    elif filetype == "json":
        mem = StringIO()
        # We need to escape certain objects in the DF to prevent Segfaults
        casting.escape_objects(df).to_json(mem, orient='records')

    mem.seek(0)

    if (as_attachment or filetype != "html") and not isinstance(mem, BytesIO):
        mem2 = BytesIO()
        mem2.write(mem.getvalue().encode('utf-8'))
        mem2.seek(0)
        mem = mem2

    if as_attachment:
        return send_file(
            mem,
            attachment_filename="%s.%s" % (testid, filetype),
            as_attachment=True,
            cache_timeout=-1
        )
    else:
        if filetype == "html":
            return render_template('admin/table.html', table=mem.getvalue())
        else:
            return send_file(
                mem,
                mimetype="text/plain",
                cache_timeout=-1
            )


@app.context_processor
def utility_processor():
    def significance_stars(p, alpha=0.05):
        return ''.join(
            [
                '<span class="glyphicon glyphicon-star small"'
                'aria-hidden="true"></span>'
            ] * stats.significance_class(p, alpha)
        )

    return dict(significance_stars=significance_stars)


@app.template_filter('datetime')
def datetime_filter(value, format='%x %X'):
    return value.strftime(format)

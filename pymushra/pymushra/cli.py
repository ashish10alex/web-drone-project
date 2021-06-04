import os
import click
import IPython
from tinydb import TinyDB
from . import service, casting


@click.group()
@click.option('--webmushra-path', '-w', default="webmushra")
@click.option('--db-path', '-d', default="db/webmushra.json")
@click.pass_context
def cli(ctx, webmushra_path, db_path):
    ctx.obj = {
        'webmushra_path': webmushra_path,
        'db_path': db_path
    }


@cli.command()
@click.option('--port', '-p', default=5000)
@click.option('--admin-allow', '-a', default=["127.0.0.1"], multiple=True, show_default=True)
@click.option('--experiment_name', '-exp', default="baseline_vs_noisy", show_default=True, help='Choose between - baseline_vs_noisy and other_model_combinations')
@click.pass_context
def server(ctx, port, admin_allow, experiment_name):
    service.app.config['webmushra_dir'] = os.path.join(
        os.getcwd(), ctx.obj['webmushra_path']
    )

    service.app.config['admin_allowlist'] = admin_allow
    service.app.config['experiment_name'] = experiment_name

    with TinyDB(ctx.obj['db_path']) as service.app.config['db']:
        service.app.run(debug=True, host='0.0.0.0', port=port)


@cli.command()
@click.pass_context
def db(ctx):
    with TinyDB(ctx.obj['db_path']) as db:
        collections = db.tables()  # noqa: F841

        click.echo("""
Available variables:

db : TinyDB database
    The database you selected using the --db-path switch
collections : list
    The list of all available collections
""")

        IPython.embed()


@cli.command()
@click.argument('collection_name')
@click.pass_context
def df(ctx, collection_name):
    with TinyDB(ctx.obj['db_path']) as db:
        collection = db.table(collection_name)
        df = casting.collection_to_df(collection)  # noqa: F841

        click.echo("""
Available variables:

db : TinyDB database
    The database you selected using the --db_name switch
collection : TinyDB collection
    The collection you selected using the command line argument
df : DataFrame
    The dataframe generated from the collection
""")

        IPython.embed()

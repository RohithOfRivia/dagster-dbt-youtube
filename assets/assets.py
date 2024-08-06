from dagster import asset, AssetExecutionContext, ScheduleDefinition, define_asset_job, AssetSelection
from dagster_dbt import dbt_assets, DbtProject, DbtCliResource
from .constants import POSTGRES_URI, API_URL_VIDEOS, API_KEY, API_URL_CHANNELS
from pathlib import Path
from elt_scripts import crawlers, sql_operations
import psycopg2

RELATIVE_PATH_TO_MY_DBT_PROJECT = "../dbt_dagster"

my_project = DbtProject(
    project_dir=Path(__file__)
    .joinpath("..", RELATIVE_PATH_TO_MY_DBT_PROJECT)
    .resolve(),
)

my_project.prepare_if_dev()


@dbt_assets(manifest=my_project.manifest_path)
def dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["run"], context=context).stream()

@asset
def testing_env():
    my_var = POSTGRES_URI 
    if my_var is None:
        raise ValueError("Environment variable 'POSTGRES_URI' is not set")
    return f"The value of MY_ENV_VAR is: {my_var}"

def get_connection():
    connection = psycopg2.connect(POSTGRES_URI)
    return connection

@asset
def daily_videos(context):
    context.log.info("fetching videos...")
    responses = crawlers.results_crawler(API_URL_VIDEOS, API_KEY)
    return responses

@asset 
def uploaded_videos(context, daily_videos):
    connection = get_connection()
    context.log.info("inserting API response to db...")
    sql_operations.insert_videos(responses=daily_videos, connection=connection)

@asset
def channel_details(context, daily_videos):
    connection = get_connection()
    channels_from_db = sql_operations.get_channels(connection=connection)
    context.log.info("fetching channels...")

    if len(channels_from_db) == 0:
        context.log.info("no channels in database")
        return []
    
    context.log.info("fetching API responses for the channels...")
    response = crawlers.channels_crawler(API_URL_CHANNELS, API_KEY, channels_from_db)
    
    return response

@asset
def updated_channels(context, channel_details):
    if len(channel_details) == 0:
        context.log.info("no channels to update.")
        return
    
    connection = get_connection()
    context.log.info(f"Inserting channels to db...")
    result = sql_operations.insert_channels(connection=connection, channels=channel_details)
    context.log.info(f"Inserted channels to db.")

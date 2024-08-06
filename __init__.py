from dagster import Definitions, ScheduleDefinition, define_asset_job, AssetSelection
from dagster_dbt import DbtCliResource
from assets.assets import (
    daily_videos,
    uploaded_videos,
    channel_details,
    updated_channels,
    dbt_models,
    testing_env,
    my_project
)

update_db_job = define_asset_job("update_db_job", selection=AssetSelection.assets(daily_videos, uploaded_videos, channel_details, updated_channels))

update_db_job_schedule = ScheduleDefinition(
    job=update_db_job,
    cron_schedule="0 * * * *",  # every hour
)

defs = Definitions(
    assets=[daily_videos, uploaded_videos, channel_details, updated_channels, dbt_models, testing_env],
    jobs=[update_db_job],
    schedules=[update_db_job_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=my_project),
    },
)
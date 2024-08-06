{{ config(materialized='view') }}

WITH source_channels AS (

    SELECT * FROM channels

)

SELECT *
FROM source_channels
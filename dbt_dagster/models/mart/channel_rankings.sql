--  depends_on: {{ ref('source_channels') }}
{{ config(materialized='view') }}



WITH channel_rankings AS  (
    SELECT 
        source_channels.channel_name, COUNT(source_channels.channel_name), rank() 
            OVER 
                (ORDER BY COUNT(*) DESC) as rank, source_channels.channel_id
            FROM 
                source_videos INNER JOIN source_channels ON source_channels.channel_id = source_videos.channel_id
            GROUP BY
                source_channels.channel_name, source_channels.channel_id
)

SELECT * FROM channel_rankings
import psycopg2
from datetime import datetime, timezone

# Method that inserts fetched videos from results_crawler into the db
def insert_videos(responses, connection):
    
    # Counts the no. of videos fetched. Used for testing only
    videos_uploaded_count = 0

    # Mention cols and query for the insert into postgres
    COLS =  'req_date, daily_rank, title, video_id, publish_date, channel_id, descr, thumbnail_link, dimension, views, likes, comments, favourite_count, category'

    insert_query = f"INSERT INTO videos ({COLS}) "+ """VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                    """
    
    cursor = connection.cursor()

    # Fetching today's date 
    now_utc = datetime.now(timezone.utc)

    # Format the time string with timezone offset
    formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%S")

    ''' The API responses does not indicate where the video is positioned in the top 200. It is also unclear whether
        there is an actual "rank" associated with them either. Nonetheless, the position of the video in the top 200 
        is calculated with the page variable and the following loop.'''
    
    page = 0

    # The responses will almost always have exactly four pages. So splitting that up with a loop to keep track of the rank 
    for j in range(len(responses)):

        # Rank calculation
        rank_start = 50 * page
        response = responses[j] 

        # Going through each video to execute the insert statement 
        for i in range(len(response['items'])):
            
            # Rank calculation
            rank = rank_start + i + 1

            # Fetch video details
            current_video = response['items'][i]
        
            try:
                # Insert query
                cursor.execute(insert_query, (formatted_time, rank, current_video['snippet']['title'], current_video['id'], current_video['snippet']['publishedAt'], current_video['snippet']['channelId'], current_video['snippet']['description'], current_video['snippet']['thumbnails'].get('maxres', current_video['snippet']['thumbnails'].get('default', {'url': ''}))['url'], current_video['contentDetails']['dimension'], current_video['statistics']['viewCount'], current_video['statistics'].get('likeCount', 0), current_video['statistics'].get('commentCount', -1), current_video['statistics']['favoriteCount'], current_video['snippet']['categoryId']))

            except psycopg2.Error as e:
                print(f"Error inserting data: {e}")

            # Commit all inserts
            connection.commit()

            videos_uploaded_count += 1
        page += 1
    
    # Close db connections
    cursor.close()
    connection.close()

    # Uncomment this if needed 
    # print('No. of inserts attempted: ', videos_uploaded_count)

    return

# Method that gets channels that does not exist in the channels table 
def get_channels(connection, update=False):
    channels = []

    # Select all channels from the videos table where we do not have channel data for, in the Channels table
    select_query = '''SELECT videos.channel_id
                FROM videos
                LEFT JOIN channels ON videos.channel_id = channels.channel_id
                WHERE channels.channel_id IS NULL'''
                
    # if update == True:
    #     select_query = '''SELECT channel_id FROM videos'''

    cursor = connection.cursor()

    # Fetch all results from the executed SELECT statement
    cursor.execute(select_query)
    records = cursor.fetchall()

    # Append everything to the channels variable to send to the channels_crawler method
    for record in records:
        channels.append(record[0])
    
    # Close db connections
    cursor.close()
    connection.close()

    return channels 

# Method to insert channel details into the db
def insert_channels(connection, channels, update=False):
    # Mention columns and insert query
    cols =  'channel_id, channel_name, channel_username, descr, channel_start_date, subs, views, video_count, kids_channel, profile_picture_url'

    query = f"INSERT INTO channels ({cols}) "+ """VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                    """
    # if update == True:
    #     query = '''UPDATE channels SET subs = %s, views = %s, video_count=%s WHERE channel_id=%s'''

    cursor = connection.cursor()
    count = 0
    for channel in channels:
    # Execute the insert statement
        try:
            cursor.execute(query, (channel['channel_id'], channel['channel_name'], channel['custom_url'], channel['description'], channel['channel_start_date'], channel['subs'], channel['views'], channel['video_count'], channel['kids'], channel['thumnail_url']['url']))
            connection.commit() 
            count += 1

        except psycopg2.Error as e:
            raise Exception(f'count:{count}{e}')
            print(f"Error inserting data: {e}")   

        # Close db connections
    cursor.close()
    connection.close()

    return "complete"

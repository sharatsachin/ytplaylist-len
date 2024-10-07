from datetime import timedelta
from flask import Flask, Response, request, render_template
import datetime
import isodate
import json
import re
import requests
import os

APIS = os.environ['APIS'].strip('][').split(',')
URL1 = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='
URL2 = 'https://www.googleapis.com/youtube/v3/videos?&part=contentDetails&id={}&key={}&fields=items/contentDetails/duration'


# To get the playlistId from the link
def get_id(playlist_link):
    p = re.compile('^([\S]+list=)?([\w_-]+)[\S]*$')
    m = p.match(playlist_link)
    if m:
        return m.group(2)
    else:
        return 'invalid_playlist_link'


# To parse the datetime object into readable time
def parse(a):
    ts, td = a.seconds, a.days
    th, tr = divmod(ts, 3600)
    tm, ts = divmod(tr, 60)
    ds = ''
    if td:
        ds += ' {} day{},'.format(td, 's' if td != 1 else '')
    if th:
        ds += ' {} hour{},'.format(th, 's' if th != 1 else '')
    if tm:
        ds += ' {} minute{},'.format(tm, 's' if tm != 1 else '')
    if ts:
        ds += ' {} second{}'.format(ts, 's' if ts != 1 else '')
    if ds == '':
        ds = '0 seconds'
    return ds.strip().strip(',')


# find if a time lies between two other times
def todayAt(hr, min=0, sec=0, micros=0):
    now = datetime.datetime.now()
    return now.replace(hour=hr, minute=min, second=sec, microsecond=micros)


# find out which time slice an time lies in, to decide which API key to use
def find_time_slice():
    timeNow = datetime.datetime.now()
    time_slice = 0
    if todayAt(0) <= timeNow < todayAt(4):
        time_slice = 1
    elif todayAt(4) <= timeNow < todayAt(8):
        time_slice = 2
    if todayAt(8) <= timeNow < todayAt(12):
        time_slice = 3
    if todayAt(12) <= timeNow < todayAt(16):
        time_slice = 4
    if todayAt(16) <= timeNow < todayAt(20):
        time_slice = 5
    return time_slice


app = Flask(__name__, static_url_path='/static')


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template("home.html")
    else:
        # Get playlist link/id as input from the form
        playlist_link = request.form.get('search_string', '').strip()
        playlist_id = get_id(playlist_link)
        
        # Get starting video number from the form
        start_video_input = request.form.get('start_video', '').strip()
        try:
            start_video = int(start_video_input)
            if start_video < 1:
                start_video = 1
        except ValueError:
            start_video = 1  # Default to 1 if input is invalid or empty
        
        # Initialize variables
        next_page = ''  # To hold next_page token, empty for first page
        total_videos = 0  # Total number of videos processed
        cnt = 0  # Number of videos counted (from start_video onwards)
        a = timedelta(0)  # To store total length of playlist
        # tsl = find_time_slice()
        tsl = find_time_slice() % len(APIS)
        display_text = []  # List to contain final text to be displayed
        
        print(APIS[tsl])
        
        # Process the playlist items page by page
        while True:
            adjusted_vid_list = []
            try:
                # Make request to get list of video IDs for one page
                print(URL1.format(APIS[tsl].strip("'"), playlist_id))
                response = requests.get(URL1.format(APIS[tsl].strip("'"), playlist_id) + next_page)
                results = response.json()
                
                # Process each item and check if it should be included
                for x in results.get('items', []):
                    total_videos += 1
                    if total_videos >= start_video:
                        adjusted_vid_list.append(x['contentDetails']['videoId'])
            except KeyError as e:
                display_text = [f"Error retrieving playlist items: {e}"]
                break
            
            # If there are videos to process, fetch their durations
            if adjusted_vid_list:
                url_list = ','.join(adjusted_vid_list)
                cnt += len(adjusted_vid_list)
                try:
                    # Get the durations of all videos in adjusted_vid_list
                    op_response = requests.get(URL2.format(url_list, APIS[tsl].strip("'")))
                    op = op_response.json()
                    
                    # Add all the durations to 'a'
                    for x in op.get('items', []):
                        a += isodate.parse_duration(x['contentDetails']['duration'])
                except KeyError as e:
                    display_text = [f"Error retrieving video durations: {e}"]
                    break
            
            # Check if there is a next page or if we've reached the limit
            if 'nextPageToken' in results and cnt < 500:
                next_page = results['nextPageToken']
            else:
                if cnt >= 500:
                    display_text.append('Number of videos limited to 500.')
                
                if cnt > 0:
                    # Calculate and display the results
                    display_text += [
                        f'Number of videos: {cnt}',
                        f'Average length of video: {parse(a / cnt)}',
                        f'Total length of playlist: {parse(a)}',
                        f'At 1.25x speed: {parse(a / 1.25)}',
                        f'At 1.50x speed: {parse(a / 1.5)}',
                        f'At 1.75x speed: {parse(a / 1.75)}',
                        f'At 2.00x speed: {parse(a / 2)}',
                    ]
                else:
                    display_text.append(f'No videos found starting from video number {start_video}.')
                break
        
        return render_template("home.html", display_text=display_text)

@app.route("/healthz", methods=['GET', 'POST'])
def healthz():
    return "Success", 200    
    
    
@app.route('/.well-known/brave-rewards-verification.txt')
def static_from_root_brave():
    return Response(
        'This is a Brave Rewards publisher verification file.\n\nDomain: ytplaylist-len.herokuapp.com\nToken: aae68b8a5242a8e5f0505ee6eaa406bd51edf0dc9a05294be196495df223385c',
        mimetype='text/plain')


@app.route('/ads.txt')
def static_from_root_google():
    return Response(
        'google.com, pub-8874895270666721, DIRECT, f08c47fec0942fa0',
        mimetype='text/plain')


if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)
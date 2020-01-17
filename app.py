from flask import Flask, request, render_template
import json, requests
import requests, json
import isodate
import re
from datetime import timedelta

url1 = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken,pageInfo/totalResults'
url1 += '&key=AIzaSyDyBjqjA49e1Xj5mm9utbIdTf8Hr8_NN3s&playlistId={}&pageToken='

url2 = 'https://www.googleapis.com/youtube/v3/videos?&part=contentDetails&id={}'
url2 += '&key=AIzaSyA15XfBwfB-gfPuLpm1tbl1p5lciN6DOII&fields=items/id,items/contentDetails/duration'

def parse(a):
    ts, td = a.seconds, a.days
    th, tr = divmod(ts, 3600)
    tm, ts = divmod(tr, 60)

    ds = ''
    if td:
        ds += ' {} day{},'.format(td, 's' if td!=1 else '')
    if th:
        ds += ' {} hour{},'.format(th, 's' if th!=1 else '')
    if tm:
        ds += ' {} minute{},'.format(tm, 's' if tm!=1 else '')
    if ts:
        ds += ' {} second{}'.format(ts, 's' if ts!=1 else '')
    if ds == '':
        ds = '0 seconds'
    return ds.strip().strip(',')

app = Flask(__name__)
app._static_folder = '/static/'

@app.route("/", methods=['GET', 'POST'])
def home():
    if(request.method == 'GET'):
        return render_template("home.html")

    else :
        playlist_id = request.form.get('search_string').strip()
        next_page = ''
        cnt = 0
        a = timedelta(0)
        display_text = []
        while True:
            vid_list = []
            try:
                results = json.loads(requests.get(url1.format(playlist_id) + next_page).text)
                for x in results['items']:
                    vid_list.append(x['contentDetails']['videoId'])
            except KeyError:
                display_text = [results['error']['message']]
                break
                
            url_list = ','.join(vid_list)
            cnt += len(vid_list)
            try:
                op = json.loads(requests.get(url2.format(url_list)).text)
                for x in op['items']:
                    a += isodate.parse_duration(x['contentDetails']['duration'])
            except KeyError:
                display_text = [results['error']['message']]
                break
            
            if 'nextPageToken' in results and cnt < 500:
                next_page = results['nextPageToken']
            else:
                if cnt >= 500:
                    display_text = ['No of videos limited to 500.']
                display_text += ['No of videos : ' + str(cnt), 'Average length of video : ' + parse(a/cnt), 'Total length of playlist : ' + parse(a), 'At 1.25x : ' + parse(a/1.25), 'At 1.50x : ' + parse(a/1.5), 'At 1.75x : ' + parse(a/1.75), 'At 2.00x : ' + parse(a/2)]
                break

        return render_template("home.html", display_text = display_text)

if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.youtube_api_key')

def load_key():
    if not os.path.exists(KEY_FILE):
        print 'BLAD: Brak pliku', KEY_FILE
        sys.exit(1)
    with open(KEY_FILE, 'r') as f:
        key = f.read().strip()
    if not key:
        print 'BLAD: Plik klucza jest pusty'
        sys.exit(1)
    return key

def fetch_trending(api_key, max_results=50, region='PL'):
    url = (
        'https://www.googleapis.com/youtube/v3/videos'
        '?part=snippet,contentDetails'
        '&chart=mostPopular'
        '&regionCode=' + region +
        '&maxResults=' + str(max_results) +
        '&key=' + api_key
    )
    print 'Odpytuję:', url[:80] + '...'
    try:
        response = urllib2.urlopen(url, timeout=10)
        data = json.loads(response.read())
        return data
    except urllib2.HTTPError as e:
        print 'HTTP ERROR:', e.code, e.read()
        sys.exit(1)
    except Exception as e:
        print 'BLAD:', e
        sys.exit(1)

def main():
    print '=== Test YouTube Data API v3 ==='
    key = load_key()
    print 'Klucz zaladowany OK (', key[:8], '...)'

    data = fetch_trending(key)

    items = data.get('items', [])
    print '\nPobrano', len(items), 'filmow:\n'

    urls = []
    for i, item in enumerate(items):
        video_id = item['id']
        title = item['snippet']['title'].encode('utf-8')
        duration = item['contentDetails']['duration']
        url = 'https://www.youtube.com/watch?v=' + video_id
        urls.append(url)
        print '%2d. [%s] %s' % (i+1, duration, title)

    print '\n=== URL-e do odtwarzania ==='
    for url in urls[:5]:
        print url

    print '\nWYNIK: OK - API dziala, pobrano', len(urls), 'URL-i'

if __name__ == '__main__':
    main()
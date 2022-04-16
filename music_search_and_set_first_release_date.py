#!/usr/bin/env python3

import musicbrainzngs
import acoustid
import taglib
import argparse
import base64
import glob

import os
import time
from datetime import datetime


API_KEY = 'GETAPIKEYFROMACUSTICID'
AC_API_KEY = b'GETAPIKEYFROMACUSTICID2'
SCORE_THRESH = 0.5
_matches = {}


def acoustid_find(path):
    try:
        duration, fp = acoustid.fingerprint_file(path)
    except acoustid.FingerprintGenerationError as exc:
        print(u'acoustid fingerprint failed: {1}', exc)
        return None

    try:
        res = acoustid.lookup(API_KEY, fp, duration, meta='recordings releases')
    except acoustid.AcoustidError as exc:
        print(u'acoustid lookup failed: {1}', exc)
        return None

    if res['status'] != 'ok' or not res.get('results'):
        print(u'acoustid no match found')
        return None
    
    result = res['results'][0]
    if result['score'] < SCORE_THRESH:
        print(u'acoustid result below threshold')
        return None

    if not result.get('recordings'):
        print(u'acoustid recording not found')
        return None
    
    recording_ids = []
    release_ids = []
    for recording in result['recordings']:
        recording_ids.append(recording['id'])
        if 'releases' in recording:
            release_ids += [rel['id'] for rel in recording['releases']]

    _matches[path] = recording_ids, release_ids


def rate_limit(min_interval):
    try:
        sleep_duration = min_interval - (time.time() - rate_limit.last_timestamp)
    except AttributeError:
        sleep_duration = 0

    sleep_duration = int(sleep_duration)
    if sleep_duration > 0:
        time.sleep(sleep_duration)

    rate_limit.last_timestamp = time.time()

def calc_date(release_date, release_year):
    year = None
    dt = None
    rdt = release_date
    if len(rdt) == 4:
        dt = datetime.strptime(rdt, '%Y')
    elif len(rdt) == 7:
        dt = datetime.strptime(rdt, '%Y-%m')
    elif len(rdt) == 10:
        dt = datetime.strptime(rdt, '%Y-%m-%d')
    else:
        try:
            dt = datetime.strptime(rdt, '%Y-%m-%d')
        except:
            pass
    if dt:
        year = dt.year
        if year < release_year:
            release_year = year
            dt = dt.replace(year = year)
            #dt.year = release_year
            print("found release date: ", dt.year, dt.month)
    return dt, release_year


def calc_older_date_from_acoustid(id, release_year):
    release = None
    release_date = None
    try:
        result = musicbrainzngs.get_recording_by_id(id, includes=["releases"])
        if result:
            recording = result.get('recording')
            if recording:
                if 'release-list' in recording and len(recording['release-list']) > 0:
                    release = recording['release-list'][0]

    except musicbrainzngs.ResponseError as err:
        if err.cause.code == 404:
            print("musicbrainzngs: disc not found ", err)
        else:
            print("musicbrainzngs: server error ", err)

    if release and 'date' in release:
        (release_date, release_year) = calc_date(release['date'], release_year)
    return release_date, release_year
    
    
def identify_and_update(path):
    
    print("___________________________________________________")
    print("PROCESSING : " + path)
    release_date = None
    dt = datetime.strptime('2200', '%Y')
    release_year = dt.year
    final_release_date = None

    acoustid_find(path)
    
    musicbrainzngs.set_useragent(
    "python-musicbrainz-ngs-example",
    "0.1",
    "https://github.com/alastair/python-musicbrainz-ngs/",)
    
    acoustIDs = None
    if path in _matches and len(_matches[path]) > 0 and len(_matches[path][0]) > 0:
        try:
            acoustIDs = _matches[path][0]
        except:
            pass
            
        if len(acoustIDs) == 0:
            print('acoust id NOT FOUND!!!')
            return False
            
        for id in acoustIDs:
            (final_release_date, release_year) = calc_older_date_from_acoustid(id, release_year)
    
        release_year = str(release_year)
        final_release_date = str(final_release_date)
        final_release_date = final_release_date[0:10]
    
    rate_limit(1.0/3.0)
    
    try:
        results = acoustid.match(base64.b64decode(AC_API_KEY), path)
    except acoustid.NoBackendError:
        print("ERROR : backend library not found")
        return False
    except acoustid.FingerprintGenerationError:
        print("ERROR : fingerprint generation error")
        return False
    except acoustid.WebServiceError as exc:
        print("ERROR : web service error: " + exc.message)
        return False

    for score, rid, title, artist in results:
        song = taglib.File(path)
        if release_year and release_year != '2200':
            if "DATE" in song.tags:
                if song.tags["DATE"][0] != final_release_date:
                    try:
                        print("Seting to release date: ", final_release_date)
                        song.tags["DATE"] = final_release_date
                    except:
                        pass

        try:
            song.save()
        except:
            pass

    if final_release_date:
        print("OK release date: ", final_release_date)
    else:
        print("ERROR : no matches found")


def main():
    parser = argparse.ArgumentParser(prog="idntag", description=
                                     "Find oldest release year and update track. "
                                     "This is so we can make play lists such as: "
                                     "60s, 70s, 80s, etc... ")
    parser.add_argument("-v", "--version", action='version', version='%(prog)s v1.03')
    parser.add_argument('path', nargs='+', help='path of a file or directory')
    args = parser.parse_args()

    abs_paths = [os.path.join(os.getcwd(), path) for path in args.path]
    paths = set()
    for path in abs_paths:
        if os.path.isfile(path):
            paths.add(path)
        elif os.path.isdir(path):
            abs_paths += glob.glob(path + '/*')

    for path in paths:
        identify_and_update(path)


if __name__ == "__main__":
    main()

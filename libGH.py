#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import string
import requests
import re
import os
import sys
import pprint
import tarfile
import datetime

pp = pprint.PrettyPrinter(indent=4)

class GH_Template( string.Template ):
    delimiter = ":"

api_call_count = 0

API = {

    "ISSUES-REPO" : {
        "URL"  : "https://api.github.com/repos/:owner/:repo/issues",
        "TYPE" : "GET"
    },

    "SEARCH-REPO" : {
        "URL"  : "https://api.github.com/search/repositories?q=:q&sort=:sort&order=:order",
        "TYPE" : "GET"
    },

    "SEARCH-ISSUE" : {
        "URL"  : "https://api.github.com/search/issues?q=:q",
        "TYPE" : "GET"
    },

    "SEARCH-COMMIT" : {
        "URL"  : "https://api.github.com/search/commits?q=:q",
        "TYPE" : "GET"
    },

    "RELEASES-REPO" : {
        "URL"  : "https://api.github.com/repos/:owner/:repo/releases",
        "TYPE" : "GET"
    },

    "TAGS-REPO" : {
        "URL"  : "https://api.github.com/repos/:owner/:repo/tags",
        "TYPE" : "GET"
    },

    "CONTRIBUTORS-REPO" : {
        "URL"  : "https://api.github.com/repos/:owner/:repo/contributors",
        "TYPE" : "GET"
    },

    "GET-REPO" : {
        "URL"  : "https://api.github.com/repos/:owner/:repo",
        "TYPE" : "GET"
    },

    "RATE-LIMIT" : {
        "URL"  : "https://api.github.com/rate_limit",
        "TYPE" : "GET"
    }
}


TEMP_CFG = {

    "GH-CONTENTS-URL" : "https://raw.githubusercontent.com/:owner/:repo/:branch/README.md",

    # TOKEN 값이 없으면 연속으로 10번 이상 API 던지면 바로 아래와 같은 메시지 출력
    #{   u'documentation_url': u'https://developer.github.com/v3/#rate-limiting',
    #    u'message': u"API rate limit exceeded for 110.12.220.235. (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.)"}

    "TOKEN" : "",

    "PATH" : {
        "DATA" : "./data"
    }
}






def getAPI( API, TEMPLATE, HEADERS=None ):

    (flag, msg, result) = (True, {}, "")

    URL = GH_Template( API['URL'] ).safe_substitute( TEMPLATE )
    URL += "&" if ( "?" in URL ) else "?"

    if( ("page" in TEMPLATE.keys()) and (TEMPLATE['page'] > 1) ):
        URL = "%s&page=%s" % (URL, TEMPLATE['page'])

    if( "per_page" in TEMPLATE.keys() ):
        URL = "%s&per_page=%s" % (URL, TEMPLATE['per_page'])

    msg['URL'] = URL
    results = None


    try:

        if( API['TYPE'] == "GET" ):
            results = requests.get( URL, headers=HEADERS ) if( HEADERS ) else requests.get( URL )

        elif( API['TYPE'] == "POST" ):
            results = requests.post( URL, data=json.dumps(TEMPLATE['DATA']) )

        elif( API['TYPE'] == "PUT" ):
            results = requests.put( URL, data=json.dumps(TEMPLATE['DATA']) )

        elif( API['TYPE'] == "DELETE" ):
            results = requests.delete( URL )

        else:
            pass


        # status_code를 위의 if문에서 물고 여기까지 오는 것이 깔끔할 듯
        if( not results.status_code in [ 200, 201, 204 ] ):

            flag = False
            msg['ERROR'] = "Recieved %s response : %s" % (results.status_code, URL)
            msg['CODE'] = results.status_code

            #print "Error : %s" % results.status_code
            #print results.text

        result = json.loads( results.text ) if (results.text != "") else ""


    except requests.exceptions.RequestException as e:

        if( results != None ):
            print( results.text )
        print( e )
        exit()

        flag = False
        msg['ERROR'] = "Error: Exception in GH_API"


    return (flag, msg, result)






def search( API, template, header ):

    # API 호출 횟수를 파악하기 위해서
    global api_call_count

    # Timeouts and incomplete results 이슈가 종종 발생하여 (GitHub API 제약) retry 로직을 넣음
    # 5번 이상 재시도를 해도 안된다면 에러 상황이라 판단했다.
    MAX_TRY = 5
    while (MAX_TRY > 0):

        api_call_count += 1
        (flag, msg, results) = getAPI( API, template, header )

        if( type(results) != type({}) ):
            break

        if( 'incomplete_results' not in results.keys() ):
            break

        if( not results['incomplete_results'] ):
            break

        if( (not flag) and (msg['CODE'] in [422]) ):
            break

        MAX_TRY -= 1

    if( flag and (MAX_TRY == 0) ):
        print("MAX_TRY = %s" % MAX_TRY)
        print(flag)
        print(msg)
        print(results)
        exit()

    msg['api_call_count'] = api_call_count

    return (flag, msg, results)



def getPages( API, template, header ):

    results = []
    while True:

        (flag, msg, result) = search( API, template, header )
        if( not flag ):
            break

        results.extend( result )

        if( len(result) < template['per_page'] ):
            break

        template['page'] += 1

    return (flag, msg, results)





def tarEncode( target, source ):

    if( os.path.isfile(target) ):
        os.remove( target )
        print( "[%s] remove file: %s" % ("main", target) )

    tar = tarfile.open( target, "w:gz")
    tar.add( source )
    tar.close()

    return True



# 일반적인 용도는 아니고, 여기의 특수한 상황에 맞춘 함수로 구성
def tarDecode( filepath ):

    if( not os.path.isfile( filepath ) ):
        print( "[%s] can not find file: %s" % ("main", filepath) )
        exit()

    DATADIR = os.path.dirname(filepath)
    DATAPATH = None
    with tarfile.open( filepath, "r:gz") as tar:

        for tarinfo in tar:
            if not (tarinfo.isreg() and tarinfo.name.endswith('.json')): continue

            tarinfo.name = os.path.basename(tarinfo.name)
            DATAPATH = os.path.join( DATADIR, tarinfo.name )

            if( os.path.isfile(DATAPATH) ):
                continue

            tar.extract(tarinfo, DATADIR)

    return DATAPATH




# RateLimit 값을 얻기 위한 함수 (API Call 소비하지 않는다)
def getRateLimit( header ):

    (flag, msg, result) = getAPI( API['RATE-LIMIT'], {}, header )

    if( flag ):
        result['rate']['reset_str'] = datetime.datetime.fromtimestamp(result['rate']['reset']).strftime('%Y-%m-%d %H:%M:%S')
        result['resources']['search']['reset_str'] = datetime.datetime.fromtimestamp(result['resources']['search']['reset']).strftime('%Y-%m-%d %H:%M:%S')

    return (flag, msg, result)




def percent( part, whole ):
    return 100*float(part)/float(whole)






def getReadme( template ):

    readme_files = [
        "README.MD",  "README.md",  "readme.MD",  "readme.md",  "Readme.MD",  "Readme.md",
        "README.TXT", "README.txt", "readme.TXT", "readme.txt", "Readme.TXT", "Readme.txt",
        "README.RST", "README.rst", "readme.RST", "readme.rst", "Readme.RST", "Readme.rst"
    ]

    URL_BASE = "https://raw.githubusercontent.com/:owner/:repo/:branch/"

    results = None

    try:

        (flag, msg, result) = (True, "", "")
        for readme_file in readme_files:

            url = URL_BASE + readme_file

            url = GH_Template( url ).safe_substitute( template )
            url += "&" if ( "?" in url ) else "?"

            results = requests.get( url )
            if( results.status_code == 200 ): break


        result = ""
        if( results.status_code == 200 ):

            result = re.sub('<.+?>', '', results.text, 0).strip()
            result = result.replace("\n", " ")
            result = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', " ", result)

            # 숫자와 영문만 남기기 위한 로직
            #result = re.sub('[^0-9a-zA-Zㄱ-힗]', '', result)
            result = re.sub('[^0-9a-zA-Z\s]', '', result)
            result = " ".join(result.split())

    except requests.exceptions.RequestException as e:

        if( results != None ):
            print( results.text )
        print( e )
        exit()

        flag = False
        msg = "Error: Exception in getREADME"

    return (flag, msg, result)




if __name__ == '__main__':


    CFG = {
        'TOKEN' : ""
    }

    template = {
        "owner"    : "stanfordnlp",
        "repo"     : "mac-network",
        "branch"   : "master"
    }

    (flag, msg, result) = getReadme( template, CFG['TOKEN'] )

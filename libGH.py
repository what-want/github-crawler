#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import string
import requests
import re
import os
import pprint


class GH_Template( string.Template ):
    delimiter = ":"


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






def getAPI( API, TEMPLATE, TOKEN, HEADERS=None ):

    (flag, msg, result) = (True, {}, "")

    URL = GH_Template( API['URL'] ).safe_substitute( TEMPLATE )
    URL += "&" if ( "?" in URL ) else "?"
    if( TOKEN != "" ):
        URL = "%saccess_token=%s" % (URL, TOKEN)

    if( ("page" in TEMPLATE.keys()) and (TEMPLATE['page'] > 1) ):
        URL = "%s&page=%s" % (URL, TEMPLATE['page'])

    if( "per_page" in TEMPLATE.keys() ):
        URL = "%s&per_page=%s" % (URL, TEMPLATE['per_page'])

    msg['URL'] = URL


    # params 사용하는 것으로 고민 필요
    #requests.request('GET', url, params=params, headers=headers)

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
            msg['ERROR'] = "Recieved non 200 response : %s" % URL

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




def getREADME( TEMPLATE, TOKEN ):

    URL = "https://raw.githubusercontent.com/:owner/:repo/:branch/README.md"
    (flag, msg, result) = (True, "", "")

    URL = GH_Template( URL ).safe_substitute( TEMPLATE )
    URL += "&" if ( "?" in URL ) else "?"
    if( TOKEN != "" ):
        URL = "%saccess_token=%s" % (URL, TOKEN)

    results = None

    try:

        results = requests.get( URL )

        result = re.sub('<.+?>', '', results.text, 0).strip()
        result = result.replace("\n", " ")
        result = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', " ", result)
        result = " ".join(result.split())


    except requests.exceptions.RequestException as e:

        if( results != None ):
            print( results.text )
        print( e )
        exit()

        flag = False
        msg = "Error: Exception in getREADME"


    return (flag, msg, result)

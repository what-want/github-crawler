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




def getREADME( URL, TEMPLATE, TOKEN ):

    (flag, msg, result) = (True, "", "")

    URL = GH_Template( URL ).safe_substitute( TEMPLATE )
    URL += "&" if ( "?" in URL ) else "?"
    if( TOKEN != "" ):
        URL = "%saccess_token=%s" % (URL, TOKEN)

    if( WW_DEBUG ):
        print( "[DEBUG] (GH_README) URL = %s" % URL )


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
        msg = "Error: Exception in GH_README"


    return (flag, msg, result)





"""
if __name__ == "__main__":

    pp = pprint.PrettyPrinter(indent=4)

    if( "WW_TOKEN" in os.environ.keys() ):
        CFG['TOKEN'] = os.environ["WW_TOKEN"]

    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    print( "TOKEN = %s" % CFG['TOKEN'] )



    ###
    # 이슈 검색하는 것 테스트 코드

    template = {
        "owner" : "whatwant",
        "repo"  : "whatwant"
    }

    #(flag, msg, result) = GH_API( CFG['GH-API']['ISSUES-REPO'], template, CFG['TOKEN'] )






    ###
    # Search API 테스트 코드


    # 일단 star 많은 순서 위주로 검색을 해봤음
    template = {
        "q"        : "",
        "sort"     : "stars",
        "order"    : "desc",
        "page"     : 1,
        "per_page" : 100
    }


    topics = [
        "Artificial Intelligence",
        "Deep Learning",
        "Machine Learning",
        "Natural Language Processing",
        "Computer Vision",
        "Machine Reasoning"
    ]


    DATAPATH = os.path.join( CFG['PATH']['DATA'], "data.csv" )
    if( os.path.isfile( DATAPATH ) ):
        os.remove( DATAPATH )

    contents_order = [
        'owner', 'repo',
        'topics',
        'readme',
        'created_at', 'updated_at',
        'language',
        'owner', 'owner_type',
        'watchers_count', 'stargazers_count', 'forks_count',
        'commits_count',
        'default_branch',
        'contributors',
        'releases_count', 'tags_count',
        'open_issues_count', 'closed_issues_count',
        'open_pr_count', 'closed_pr_count'
    ]

    with open(DATAPATH, "w") as f:
        f.write( ",".join(contents_order) + "\n" )







    for topic in topics:

        # topic으로 검색을 할 것인지, 그냥 검색어로 검색을 할 것인지에 대한 선택
        #template['q'] = "topic:%s" % topic.replace(" ", "%20")
        template['q'] = "%s" % topic.replace(" ", "%20")

        # 한 번의 API에 30(per_page)개 결과밖에 안들어오기에, page에 대한 처리 로직 추가
        template['page'] = 1


        while True:

            HEADER = { "Accept" : "application/vnd.github.mercy-preview+json" }
            (flag, msg, result) = GH_API( CFG['GH-API']['SEARCH-REPO'], template, CFG['TOKEN'], HEADER )

            if( template['page'] == 1 ):
                print( "topic : %s" % topic )
                print( "total_count: %s" % result['total_count'] )
                print( "incomplete results: %s" % "True" if( result['incomplete_results'] ) else "False" )

            if( not "items" in result.keys() ):
                pp.pprint( result )
                exit()

            for idx, item in enumerate(result['items']):

                print( "    [%s/%s] : (%s) %s" % ( ((idx+1)+((template['page']-1)*template['per_page'])), result['total_count'], item['stargazers_count'], item['html_url'] ) )
                write_contents = {}

                temps = item['full_name'].split("/")
                write_contents['owner'] = temps[0]
                write_contents['repo'] = temps[1]

                write_contents['topics'] = "#".join( item['topics'] )

                temp = {
                    "owner"    : write_contents['owner'],
                    "repo"     : write_contents['repo'],
                    "branch"   : item['default_branch']
                }
                (flag1, msg1, result1) = GH_README( CFG['GH-CONTENTS-URL'], temp, CFG['TOKEN'] )
                write_contents['readme'] = result1

                write_contents['created_at'] = item['created_at']
                write_contents['updated_at'] = item['updated_at']

                write_contents['language'] = item['language'] if( item['language'] != None ) else ""

                write_contents['owner'] = item['owner']['login']
                write_contents['owner_type'] = item['owner']['type']

                write_contents['watchers_count'] = item['watchers_count']
                write_contents['stargazers_count'] = item['stargazers_count']
                write_contents['forks_count'] = item['forks_count']


                temp = {
                    "owner"    : write_contents['owner'],
                    "repo"     : write_contents['repo'],
                    "per_page" : 100,
                    "page"     : 1
                }
                contributors = []
                write_contents['commits_count'] = 0
                while True:
                    (flag2, msg2, result2) = GH_API( CFG['GH-API']['CONTRIBUTORS-REPO'], temp, CFG['TOKEN'] )

                    for tmp in result2:
                        contributors.append(  tmp['login'] )
                        write_contents['commits_count'] += tmp['contributions']

                    if( len(result2) < temp['per_page'] ): break
                    temp['page'] += 1

                write_contents['default_branch'] = item['default_branch']
                write_contents['contributors'] = "#".join( contributors )


                temp = {
                    "owner"    : write_contents['owner'],
                    "repo"     : write_contents['repo'],
                    "per_page" : 100,
                    "page"     : 1
                }
                releases = []
                while True:
                    (flag3, msg3, result3) = GH_API( CFG['GH-API']['RELEASES-REPO'], temp, CFG['TOKEN'] )
                    releases.extend( result3 )

                    if( len(result3) < temp['per_page'] ): break
                    temp['page'] += 1
                write_contents['releases_count'] = len(releases)


                write_contents['open_issues_count'] = item['open_issues_count']
                temp = {
                    "q"        : "repo:%s+type:issue+state:closed" % item['full_name'],
                    "per_page" : 1
                }
                (flag4, msg4, result4) = GH_API( CFG['GH-API']['SEARCH-ISSUE'], temp, CFG['TOKEN'] )
                write_contents['closed_issues_count'] = result4['total_count']




                temp = {
                    "q"        : "repo:%s+type:pr+state:closed" % item['full_name'],
                    "per_page" : 1
                }
                (flag5, msg5, result5) = GH_API( CFG['GH-API']['SEARCH-ISSUE'], temp, CFG['TOKEN'] )
                write_contents['open_pr_count'] = result5['total_count']

                temp = {
                    "q"        : "repo:%s+type:pr+state:open" % item['full_name'],
                    "per_page" : 1
                }
                (flag6, msg6, result6) = GH_API( CFG['GH-API']['SEARCH-ISSUE'], temp, CFG['TOKEN'] )
                write_contents['closed_pr_count'] = result6['total_count']


                temp = {
                    "owner"    : write_contents['owner'],
                    "repo"     : write_contents['repo'],
                    "per_page" : 100,
                    "page"     : 1
                }
                tags = []
                while True:
                    (flag7, msg7, result7) = GH_API( CFG['GH-API']['TAGS-REPO'], temp, CFG['TOKEN'] )
                    tags.extend( result7 )

                    if( len(result7) < temp['per_page'] ): break
                    temp['page'] += 1

                write_contents['tags_count'] = len(tags)


                write_content = []
                for key in contents_order:
                    if( type(write_contents[key]) == type(1) ):
                        write_contents[key] = str(write_contents[key])
                    elif( type(write_contents[key]) == type(None) ):
                        print key
                        print write_contents[key]
                        exit()

                    write_content.append( write_contents[key].encode("utf-8") )

                with open(DATAPATH, "a") as f:
                    f.write( ",".join(write_content) + "\n" )



                #pp.pprint( write_contents )
                #exit()




            if( len(result['items']) < template['per_page'] ): break
            template['page'] += 1
            #if( template['page'] > 5 ): break




    #pp.pprint( result )

    exit()
"""

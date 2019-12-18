#!/usr/bin/python
#-*-coding:utf-8-*-

import logging.config
import json
import os
import sys
import datetime
import tarfile

# GitHub 관련된 모듈을 넣어 놓은 모듈
import libGH as GH

import pprint


pp = pprint.PrettyPrinter(indent=4)


if __name__ == '__main__':


    # Debugging을 위한 logging 모듈 환경 설정 값 읽어오기
    with open('logging.json', 'rt') as f:
        config = json.load(f)

    logging.config.dictConfig(config)
    logger = logging.getLogger()


    # 불러올 파일을 argv 변수로 받아들이기
    if len (sys.argv) != 2 :
        print( "Usage: %s 'filepath'" % sys.argv[0])
        sys.exit (1)


    # 기본적인 설정값들을 담기 위한 변수 선언
    CFG = {
        'NAME'    : sys.argv[0],
        'TARPATH' : sys.argv[1]
    }




    logger.info( "Start %s .................................................." % CFG['NAME'] )

    logger.info( "[%s] script name: %s" % ("main", CFG['NAME']) )
    logger.info( "[%s] parsing filepath: %s" % ("main", CFG['TARPATH']) )




    if( not os.path.isfile( CFG['TARPATH'] ) ):
        logger.error( "[%s] can not find file: %s" % ("main", CFG['TARPATH']) )
        sys.exit()



    DATADIR = "./data"
    DATAPATH = None
    with tarfile.open( CFG['TARPATH'], "r:gz") as tar:

        for tarinfo in tar:
            if not (tarinfo.isreg() and tarinfo.name.endswith('.json')): continue

            tarinfo.name = os.path.basename(tarinfo.name)

            DATAPATH = os.path.join( DATADIR, tarinfo.name )
            logger.info( "[%s] json filename: %s" % ("main", DATAPATH) )

            if( os.path.isfile(DATAPATH) ):
                logger.info( "[%s] there is already json filename: %s" % ("main", DATAPATH) )
                continue

            tar.extract(tarinfo, DATADIR)


    if( not DATAPATH ):
        logger.error( "[%s] can not make jsonfile" % ("main") )
        sys.exit()



    with open( DATAPATH ) as f:
        infos = json.load(f)

    infos_count = len(infos)
    logger.info( "[%s] loaded total counts: %s" % ("main", infos_count) )











    # GitHub Action을 사용함에 따라 token 값을 환경 변수로 받아들이기 위한 로직

    # TOKEN 값이 없으면 연속으로 10번 이상 API 던지면 바로 아래와 같은 메시지 출력
    #{   u'documentation_url': u'https://developer.github.com/v3/#rate-limiting',
    #    u'message': u"API rate limit exceeded for 110.12.220.235. (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.)"}
    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    if( CFG['TOKEN'] == "" ):
        logger.warning( "[%s] token is empty" % "main" )






    # CSV 파일에서 표시될 각 열의 순서를 정해주기 위해서 미리 선언
    csv_order = [
        'owner', 'repo',
        'topics',
        'readme',
        'created_at', 'updated_at',
        'language',
        'owner', 'owner_type',
        'watchers_count', 'stargazers_count', 'forks_count',
        'commits_count',
        'default_branch',
        'contributors', 'contributors_count',
        'releases_count', 'tags_count',
        'open_issues_count', 'closed_issues_count',
        'open_pr_count', 'closed_pr_count'
    ]

    CSVPATH = DATAPATH.replace(".json", ".csv")

    CSV_keys = []
    if( os.path.isfile(CSVPATH) ):

        with open(CSVPATH, "r") as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                if( idx == 0 ): continue
                temps = line.split(",")
                CSV_keys.append( "%s/%s" % (temps[0], temps[1]) )

    else:

        with open(CSVPATH, "w") as f:
            f.write( ",".join(csv_order) + "\n" )

    logger.info( "[%s] loaded exists contents: %s" % ("main", len(CSV_keys)) )




    api_calls = 0
    for idx, info in enumerate(infos):

        #if( idx < 175 ): continue

        if( info['full_name'] in CSV_keys ):
            logger.info( "[%s] (%s/%s) pass exists content: %s" % ("main", (idx+1), infos_count, info['full_name']) )
            continue

        logger.info( "[%s] (%s/%s) generate content: %s" % ("main", (idx+1), infos_count, info['full_name']) )



        content = {}

        temps = info['full_name'].split("/")
        content['owner'] = temps[0]
        content['repo']  = temps[1]


        # topic 구분자를 '#'으로 했음
        content['topics'] = "#".join( info['topics'] ) if( len(info['topics']) > 0 ) else "n/a"


        # Readme.md 파일을 얻어오기 위해서 구현
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "branch"   : info['default_branch']
        }
        (flag, msg, result) = GH.getREADME( template, CFG['TOKEN'] )
        # 32760 글자 넘어가면 csv에서 컬럼 넘어가버림
        content['readme'] = result[:15000] if (flag) else "n/a"


        content['created_at'] = info['created_at']
        content['updated_at'] = info['updated_at']

        content['language'] = info['language'] if( info['language'] != None ) else "n/a"

        content['owner'] = info['owner']['login']
        content['owner_type'] = info['owner']['type']

        content['watchers_count'] = info['watchers_count']
        content['stargazers_count'] = info['stargazers_count']
        content['forks_count'] = info['forks_count']



        # watches_count 값이 우리가 원하는 watch 값이 아니다. 그래서 별도로 구해야 한다.
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo']
        }

        (flag, msg, result) = GH.getAPI( GH.API['GET-REPO'], template, CFG['TOKEN'] )
        api_calls += 1
        logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
        if( not flag ):
            logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
            pp.pprint( result )
            exit()

        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint( result )
        #exit()

        content['subscribers_count'] = result['subscribers_count']
        content['watchers_count'] = result['subscribers_count']





        # 전체 commit을 확인하기 위해서 contributor들이 기여한 commit수를 얻어서 모두 더한다
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }
        contributors = []
        content['commits_count'] = 0

        while True:

            (flag, msg, results) = GH.getAPI( GH.API['CONTRIBUTORS-REPO'], template, CFG['TOKEN'] )
            api_calls += 1
            logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
            if( not flag ):
                logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
                pp.pprint( result )
                exit()

            for result in results:
                contributors.append( result['login'] )
                content['commits_count'] += result['contributions']

            if( len(results) < template['per_page'] ): break
            template['page'] += 1

        content['default_branch'] = info['default_branch']
        content['contributors'] = "#".join( contributors )
        content['contributors_count'] = len(contributors)



        # release 수를 얻어오기 위한 API 호출
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }
        releases = []

        while True:

            (flag, msg, results) = GH.getAPI( GH.API['RELEASES-REPO'], template, CFG['TOKEN'] )
            api_calls += 1
            logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
            if( not flag ):
                logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
                pp.pprint( result )
                exit()

            releases.extend( results )

            if( len(results) < template['per_page'] ): break
            template['page'] += 1

        content['releases_count'] = len(releases)




        content['open_issues_count'] = info['open_issues_count']

        # closed issue 수를 얻어오기 위한 API 호출
        template = {
            "q"        : "repo:%s+type:issue+state:closed" % info['full_name'],
            "per_page" : 1
        }
        (flag, msg, result) = GH.getAPI( GH.API['SEARCH-ISSUE'], template, CFG['TOKEN'] )
        api_calls += 1
        logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
        if( not flag ):
            logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
            pp.pprint( result )
            exit()

        content['closed_issues_count'] = result['total_count']




        template = {
            "q"        : "repo:%s+type:pr+state:closed" % info['full_name'],
            "per_page" : 1
        }
        (flag, msg, result) = GH.getAPI( GH.API['SEARCH-ISSUE'], template, CFG['TOKEN'] )
        api_calls += 1
        logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
        if( not flag ):
            logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
            pp.pprint( result )
            exit()

        content['closed_pr_count'] = result['total_count']


        template = {
            "q"        : "repo:%s+type:pr+state:open" % info['full_name'],
            "per_page" : 1
        }
        (flag, msg, result) = GH.getAPI( GH.API['SEARCH-ISSUE'], template, CFG['TOKEN'] )
        api_calls += 1
        logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
        if( not flag ):
            logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
            pp.pprint( result )
            exit()

        content['open_pr_count'] = result['total_count']




        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }
        tags = []

        while True:
            (flag, msg, results) = GH.getAPI( GH.API['TAGS-REPO'], template, CFG['TOKEN'] )
            api_calls += 1
            logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
            if( not flag ):
                logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
                pp.pprint( result )
                exit()


            tags.extend( results )

            if( len(results) < template['per_page'] ): break
            template['page'] += 1

        content['tags_count'] = len(tags)


        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint( content )


        write_content = []
        for key in csv_order:

            if( type(content[key]) == type(1) ):
                content[key] = str(content[key])

            elif( type(content[key]) == type(None) ):
                print key
                print content[key]
                exit()

            write_content.append( content[key].encode("utf-8") )

        with open(CSVPATH, "a") as f:
            f.write( ",".join(write_content) + "\n" )

        CSV_keys.append( info['full_name'] )


    exit(0)

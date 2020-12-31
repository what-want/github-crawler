#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import os
import sys
import datetime
import time
import tarfile
import pprint

# GitHub 관련된 모듈을 넣어 놓은 모듈
import libGH as GH



def sleepRateLimit( resetTime ):

    while( True ):
        now = datetime.datetime.now()
        deltaTime = (resetTime - now).seconds

        sleepTime = (deltaTime // 5) + 1

        if( deltaTime > 80000 ):
            break

        print(". %s" % deltaTime),
        sys.stdout.flush()

        time.sleep( sleepTime )

    print("")

    return True




# contributor
def getContributors( template, header ):

    contributors = []
    commits_count = 0
    while True:

        (flag, msg, results) = GH.search( GH.API['CONTRIBUTORS-REPO'], template, header )

        if( not flag ):
            result = results
            break

        for result in results:
            contributors.append( result['login'] )
            commits_count += result['contributions']

        if( len(results) < template['per_page'] ):
            result = {
                'contributors'       : contributors,
                'contributors_count' : len(contributors),
                'commits_count'      : commits_count
            }
            break

        template['page'] += 1

    return (flag, msg, result)






if __name__ == '__main__':


    # Source 파일 경로를 argv 변수로 받아들이기
    if len (sys.argv) != 2 :
        print( "Usage: %s 'source.tar.gz'" % sys.argv[0])
        sys.exit (1)


    # 기본적인 설정값들을 담기 위한 변수 선언
    CFG = {
        'NAME'      : sys.argv[0],
        'DIRPATH'   : { 'DATA' : './data' },
        'FILEPATH'  : {
            'tar'   : sys.argv[1]
        },
        'TIME'      : {
            'now'   : datetime.datetime.now()
        },
        'CSV-ORDER' : []
    }


    # 환경변수 'WW_TOKEN'으로 GitHub Token 값을 선언해놓아야 한다.
    # 없으면 API 60개/hour 밖에 호출하지 못한다.
    #
    # $ export WW_TOKEN=xxxxxxxxxx
    #
    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    if( CFG['TOKEN'] == "" ):
        print( "[%s] token is empty" % "main" )


    # topic 값을 얻어오기 위해서는, Header 값을 잡아줘야 한다
    CFG['HEADER'] = { "Accept" : "application/vnd.github.mercy-preview+json" }
    if( CFG['TOKEN'] != "" ):
        CFG['HEADER']['Authorization'] = 'token ' + CFG['TOKEN']


    print("Start %s (%s).................................................." % (CFG['NAME'], CFG['TIME']['now']))
    print("[%s] script name: %s" % ("main", CFG['NAME']))
    print("[%s] source file: %s" % ("main", CFG['FILEPATH']['tar']))


    CONTENTS = {
        'RAW'         : {},
        'SUCCESS'     : [],
        'FAILURE'     : [],
        'total_count' : 0
    }

    CFG['FILEPATH']['json'] = GH.tarDecode( CFG['FILEPATH']['tar'] )
    with open( CFG['FILEPATH']['json'] ) as f:
        CONTENTS['RAW'] = json.load(f)

    CONTENTS['total_count'] = len(CONTENTS['RAW'])

    print( "[%s] json filename: %s" % ("main", CFG['FILEPATH']['json']) )
    print( "[%s] loaded total counts: %s" % ("main", CONTENTS['total_count']) )


    CFG['FILEPATH']['csv'] = CFG['FILEPATH']['json'].replace(".json", ".csv")
    CFG['FILEPATH']['fail'] = CFG['FILEPATH']['json'].replace(".json", "-fail.json")


    # CSV 파일에서 표시될 각 열의 순서를 정해주기 위해서 미리 선언
    CFG['CSV-ORDER'] = [
        'owner',
        'repo',
        'topics',
        'readme',
        'created_at',
        'updated_at',
        'language',
        'owner_type',
        'watchers_count',
        'stargazers_count',
        'forks_count',
        'commits_count',
        'default_branch',
        'contributors',
        'contributors_count',
        'releases_count',
        'tags_count',
        'open_issues_count',
        'closed_issues_count',
        'open_pr_count',
        'closed_pr_count'
    ]




    # 기존에 작업하던 내용이 있으면 이어서 진행할 수 있도록 정보를 읽어오는 부분
    if( os.path.isfile(CFG['FILEPATH']['csv']) ):

        with open( CFG['FILEPATH']['csv'] ) as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                line = line.strip()
                if( (line == "") or (idx == 0) ):
                    continue

                temps = line.split(",")
                full_name = "%s/%s" % (temps[0], temps[1])
                CONTENTS['SUCCESS'].append( full_name )

    else:
        with open( CFG['FILEPATH']['csv'], "w") as f:
            f.write( ",".join(CFG['CSV-ORDER']) + "\n" )

    print( "[%s] loaded exists contents: %s" % ("main", len(CONTENTS['SUCCESS'])) )





    for idx, info in enumerate(CONTENTS['RAW']):

        # 이미 처리된 내역이면 패스~
        if( (info['full_name'] in CONTENTS['SUCCESS']) or (info['full_name'] in CONTENTS['FAILURE']) ):
            print( "[%s] (%s/%s) pass exists content: %s" % ("main", (idx+1), CONTENTS['total_count'], info['full_name']) )
            continue

        print( "[%s] (%s/%s, %0.2f%%) generate content: %s" % ("main", (idx+1), CONTENTS['total_count'], GH.percent((idx+1), CONTENTS['total_count']), info['full_name']) )

        content = {
            'owner'             : info['owner']['login'],
            'repo'              : info['name'],
            'created_at'        : info['created_at'],
            'updated_at'        : info['updated_at'],
            'language'          : info['language'] if( info['language'] != None ) else "n/a",
            'owner_type'        : info['owner']['type'],
            'watchers_count'    : info['watchers_count'],
            'stargazers_count'  : info['stargazers_count'],
            'forks_count'       : info['forks_count'],
            'default_branch'    : info['default_branch'],
            'topics'            : "#".join( info['topics'] ) if( len(info['topics']) > 0 ) else "",
            'open_issues_count' : info['open_issues_count']
        }



        # RateLimit에 걸리게 되면 reset 되는 때까지 sleep을 하기 위해서
        (flag, msg, result) = GH.getRateLimit( CFG['HEADER'] )
        print("    [%s] core remaining = %s, reset = %s" % ("getRateLimit", result['rate']['remaining'], result['rate']['reset_str']))
        print("    [%s] search remaining = %s, reset = %s" % ("getRateLimit", result['resources']['search']['remaining'], result['resources']['search']['reset_str']))

        if( result['rate']['remaining'] < 4 ):
            print("    [%s] Normal RateLimit. Remain seconds = " % ("ratelimit")),
            sleepRateLimit( datetime.datetime.fromtimestamp(result['rate']['reset']) )

        if( result['resources']['search']['remaining'] < 3 ):
            print("    [%s] Search RateLimit. Remain seconds = " % ("ratelimit")),
            sleepRateLimit( datetime.datetime.fromtimestamp(result['resources']['search']['reset']) )





        # watches_count 값이 우리가 원하는 watch 값이 아니다. 그래서 별도로 구해야 한다.
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo']
        }

        (flag, msg, result) = GH.search( GH.API['GET-REPO'], template, CFG['HEADER'] )
        if( not flag ):
            CONTENTS['FAILURE'].append( info['full_name'] )
            print("    [fail] get Watchers")
            continue

        content['watchers_count'] = result['subscribers_count']
        print("    [%s] API(%s) get watchers_count: %s" % ("watchers_count", msg['api_call_count'], content['watchers_count']))





        # Readme.md 파일을 얻어오기 위한 부분
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "branch"   : content['default_branch']
        }
        (flag, msg, result) = GH.getReadme( template )

        # csv 제약에 따라 너무 많은 내용을 담지 못하기에 15000글자로 한정했음
        content['readme'] = result[:15000] if (flag) else "n/a"
        print("    [%s] readme length: %s" % ("readme", len(content['readme'])))





        # contributors 명단과 count를 구하고, 각 contributors들이 기여한 commits 수를 더하면 전체 commit 수가 된다.
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }

        (flag, msg, result) = getContributors( template, CFG['HEADER'] )

        if( not flag ):
            CONTENTS['FAILURE'].append( info['full_name'] )
            print("    [fail] get contributors")
            continue

        content['commits_count']      = result['commits_count']
        content['contributors']       = "#".join( result['contributors'] )
        content['contributors_count'] = result['contributors_count']
        print("    [%s] contributors_count: %s, commits_count: %s" % ("contributors", content['contributors_count'], content['commits_count']))




        # release 수를 얻어오기 위한 API 호출
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }

        (flag, msg, results) = GH.getPages( GH.API['RELEASES-REPO'], template, CFG['HEADER'] )
        if( not flag ):
            CONTENTS['FAILURE'].append( info['full_name'] )
            print("    [fail] get Releases")
            continue

        content['releases_count'] = len(results)
        print("    [%s] releases_count: %s" % ("releases", content['releases_count']))




        # tags 수를 얻어오기 위한 API 호출
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }

        (flag, msg, results) =GH.getPages( GH.API['TAGS-REPO'], template, CFG['HEADER'] )
        if( not flag ):
            CONTENTS['FAILURE'].append( info['full_name'] )
            print("    [fail] get Tags")
            continue

        content['tags_count'] = len(results)
        print("    [%s] tags_count: %s" % ("tags", content['tags_count']))




        # closed issue 수를 얻어오기 위한 API 호출
        template = {
            "q"        : "repo:%s+type:issue+state:closed" % info['full_name'],
            "per_page" : 1
        }

        (flag, msg, result) = GH.search( GH.API['SEARCH-ISSUE'], template, CFG['HEADER'] )
        if( not flag ):
            if( msg['CODE'] in [422] ):
                result['total_count'] = 0

            elif( msg['CODE'] in [404] ):
                CONTENTS['FAILURE'].append( info['full_name'] )
                print("    [fail] closed issues")
                continue

        content['closed_issues_count'] = result['total_count']
        print("    [%s] closed_issues_count: %s" % ("closed_issues", content['closed_issues_count']))




        # closed pr 수를 얻어오기 위한 API 호출
        template = {
            "q"        : "repo:%s+type:pr+state:closed" % info['full_name'],
            "per_page" : 1
        }
        (flag, msg, result) = GH.search( GH.API['SEARCH-ISSUE'], template, CFG['HEADER'] )
        if( not flag ):
            if( msg['CODE'] in [422] ):
                result['total_count'] = 0

            elif( msg['CODE'] in [404] ):
                CONTENTS['FAILURE'].append( info['full_name'] )
                print("    [fail] closed pr")
                continue

        content['closed_pr_count'] = result['total_count']
        print("    [%s] closed_pr_count: %s" % ("closed_pr", content['closed_pr_count']))





        # open pr 수를 얻어오기 위한 API 호출
        template = {
            "q"        : "repo:%s+type:pr+state:open" % info['full_name'],
            "per_page" : 1
        }
        (flag, msg, result) = GH.search( GH.API['SEARCH-ISSUE'], template, CFG['HEADER'] )
        if( not flag ):
            if( msg['CODE'] in [422] ):
                result['total_count'] = 0

            elif( msg['CODE'] in [404] ):
                CONTENTS['FAILURE'].append( info['full_name'] )
                print("    [fail] open pr")
                continue

        content['open_pr_count'] = result['total_count']
        print("    [%s] open_pr_count: %s" % ("open_pr", content['open_pr_count']))




        # 중간에 끊겼다가 재시작 할 때 이어서 할 수 있도록 1건마다 계속 file write 수행
        # csv_order에 있는 순서대로 쓰여지도록 처리
        write_content = []
        for key in CFG['CSV-ORDER']:

            # 숫자형 데이터를 CSV로 쓰려고 하면 오류가 발생해서, string 캐스팅
            if( type(content[key]) == type(1) ):
                content[key] = str(content[key])

            # 있으면 안되는 None 타입이 있으면 종료! (예외 처리 해줘야 함!)
            elif( type(content[key]) == type(None) ):
                print key
                print content[key]
                exit()

            write_content.append( content[key].encode("utf-8") )


        # 뒤에 계속 붙이는 방식으로 저장
        with open(CFG['FILEPATH']['csv'], "a") as f:
            f.write( ",".join(write_content) + "\n" )
        print("    [%s] update to file" % "main")

        CONTENTS['SUCCESS'].append( info['full_name'] )



    with open(CFG['FILEPATH']['fail'], "w") as f:
        f.write( "\n".join(CONTENTS['FAILURE']) )
    print("[finish] write to fail history : %s" % CFG['FILEPATH']['fail'])

    exit(0)

#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import os
import sys
import datetime
import tarfile
import pprint

# GitHub 관련된 모듈을 넣어 놓은 모듈
import libGH as GH

api_call_count = 0



# tar.gz 압축 풀기
def extractTarGz( filepath ):

    if( not os.path.isfile( filepath ) ):
        print( "[%s] can not find file: %s" % ("main", filepath) )
        exit()

    DATADIR = "./data"
    DATAPATH = None
    with tarfile.open( filepath, "r:gz") as tar:

        for tarinfo in tar:
            if not (tarinfo.isreg() and tarinfo.name.endswith('.json')): continue

            tarinfo.name = os.path.basename(tarinfo.name)

            DATAPATH = os.path.join( DATADIR, tarinfo.name )
            print( "[%s] json filename: %s" % ("main", DATAPATH) )

            if( os.path.isfile(DATAPATH) ):
                print( "[%s] there is already json filename: %s" % ("main", DATAPATH) )
                continue

            tar.extract(tarinfo, DATADIR)


    with open( DATAPATH ) as f:
        infos = json.load(f)

    infos_count = len(infos)

    return (infos, infos_count, DATAPATH)





# RateLimit 값을 얻기 위한 함수 (API Call 소비하지 않는다)
def getRateLimit( template, token ):

    # topic 값을 얻어오기 위해서는, Header 값을 잡아줘야 한다
    HEADER = { "Accept" : "application/vnd.github.mercy-preview+json" }

    (flag, msg, result) = GH.getAPI( GH.API['RATE-LIMIT'], template, token, HEADER )

    if( not flag ):
        print( "[%s] %s" % ("getRateLimit", msg['ERROR']) )
        exit()

    result['rate']['reset_str'] = datetime.datetime.fromtimestamp(result['rate']['reset']).strftime('%Y-%m-%d %H:%M:%S')

    print("    [%s] remaining = %s, reset = %s" % ("getRateLimit", result['rate']['remaining'], result['rate']['reset_str']))

    return (flag, msg, result)










def percent( part, whole ):
    return 100*float(part)/float(whole)



if __name__ == '__main__':


    # Source 파일 경로를 argv 변수로 받아들이기
    if len (sys.argv) != 2 :
        print( "Usage: %s 'source.tar.gz'" % sys.argv[0])
        sys.exit (1)


    # 기본적인 설정값들을 담기 위한 변수 선언
    CFG = {
        'NAME'   : sys.argv[0],
        'SOURCE' : sys.argv[1]
    }


    # 환경변수 'WW_TOKEN'으로 GitHub Token 값을 선언해놓아야 한다.
    # 없으면 API 60개/hour 밖에 호출하지 못한다.
    #
    # $ export WW_TOKEN=xxxxxxxxxx
    #
    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    if( CFG['TOKEN'] == "" ):
        print( "[%s] token is empty" % "main" )


    date_info = {
        'now'   : datetime.datetime.now()
    }


    # 검색을 위한 옵션 모음
    # stars 갯수가 1개 이상인 것들만 검색하기 위한 부분이 추가되어 있다.
    template = {
    #    "q"        : ("%s+created:%s..%s+stars:>0" % (CFG['KEYWORD'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d'))),
    #    "sort"     : "stars",
    #    "order"    : "desc",
    #    "page"     : 1,
    #    "per_page" : 100
    }



    print("Start %s (%s).................................................." % (CFG['NAME'], date_info['now']))

    print("[%s] script name: %s" % ("main", CFG['NAME']))
    print("[%s] source file: %s" % ("main", CFG['SOURCE']))


    (infos, infos_count, CFG['EXTRACTED_FILEPATH']) = extractTarGz( CFG['SOURCE'] )
    print( "[%s] loaded total counts: %s" % ("main", infos_count) )





    # CSV 파일에서 표시될 각 열의 순서를 정해주기 위해서 미리 선언
    csv_order = [
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

    CFG['TARGET'] = CFG['EXTRACTED_FILEPATH'].replace(".json", ".csv")

    #pprint.pprint( infos[0] )
    #exit()



    #CSV_keys = []
    #if( os.path.isfile(CSVPATH) ):

    #    write_contents = []
    #    with open(CSVPATH, "r") as f:
    #        lines = f.readlines()
    #        for idx, line in enumerate(lines):
    #            line = line.strip()
    #            if( line == "" ): continue
    #            if( idx == 0 ):
    #                write_contents.append( line )
    #                continue

    #            temps = line.split(",")
    #            fullname = "%s/%s" % (temps[0], temps[1])

    #            if( not fullname in CSV_keys ):
    #                write_contents.append( line )
    #                CSV_keys.append( "%s/%s" % (temps[0], temps[1]) )
    #            else:
    #                logger.info( "[%s] duplicated csv info: %s" % ("main", fullname) )

    #        with open(CSVPATH, "w") as f:
    #            f.write( "\n".join(write_contents) + "\n" )

    #else:

    #    with open(CSVPATH, "w") as f:
    #        f.write( ",".join(csv_order) + "\n" )

    #logger.info( "[%s] loaded exists contents: %s" % ("main", len(CSV_keys)) )





    #FAILPATH = DATAPATH.replace(".json", ".fail")

    #FAIL_keys = []
    #if( os.path.isfile(FAILPATH) ):

    #    with open( FAILPATH ) as f:
    #        FAIL_keys = json.load(f)

    #logger.info( "[%s] loaded failed contents: %s" % ("main", len(FAIL_keys)) )


    CONTENTS = {
        'SUCCESS' : [],
        'FAILURE' : []
    }

    for idx, info in enumerate(infos):

        # 이미 처리된 내역이면 패스~
        if( (info['full_name'] in CONTENTS['SUCCESS']) or (info['full_name'] in CONTENTS['FAILURE']) ):
            print( "[%s] (%s/%s) pass exists content: %s" % ("main", (idx+1), infos_count, info['full_name']) )
            continue

        print( "[%s] (%s/%s) generate content: %s" % ("main", (idx+1), infos_count, info['full_name']) )


        content = {
            'owner'            : info['owner']['login'],
            'repo'             : info['name'],
            'created_at'       : info['created_at'],
            'updated_at'       : info['updated_at'],
            'language'         : info['language'] if( info['language'] != None ) else "n/a",
            'owner_type'       : info['owner']['type'],
            'watchers_count'   : info['watchers_count'],
            'stargazers_count' : info['stargazers_count'],
            'forks_count'      : info['forks_count'],
            'default_branch'   : info['default_branch'],
            'topics'           : "#".join( info['topics'] ) if( len(info['topics']) > 0 ) else ""
        }




        # RateLimit에 걸리게 되면 reset 되는 때까지 sleep을 하기 위해서
        template = {}
        (flag, msg, result) = getRateLimit( template, CFG['TOKEN'] )

        #if( result['rate']['remaining'] < 5 ):
        #    time.sleep(5)
        #else:
        #    time.sleep(2.5)




        # Readme.md 파일을 얻어오기 위한 부분
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "branch"   : content['default_branch']
        }
        (flag, msg, result) = GH.getREADME( template, CFG['TOKEN'] )

        # csv 제약에 따라 너무 많은 내용을 담지 못하기에 15000글자로 한정했음
        content['readme'] = result[:15000] if (flag) else "n/a"




        pprint.pprint( result )
        exit()

        'commits_count',
        'contributors',
        'contributors_count',
        'releases_count',
        'tags_count',
        'open_issues_count',
        'closed_issues_count',
        'open_pr_count',
        'closed_pr_count'












        # watches_count 값이 우리가 원하는 watch 값이 아니다. 그래서 별도로 구해야 한다.
        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo']
        }


        (flag, msg, result, api_calls) = GH_API( GH.API['GET-REPO'], template, CFG['TOKEN'], api_calls )
        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

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

            (flag, msg, results, api_calls) = GH_API( GH.API['CONTRIBUTORS-REPO'], template, CFG['TOKEN'], api_calls )
            if( (not flag) and (msg['CODE'] in [404,422]) ):

                FAIL_keys.append( info['full_name'] )

                with open(FAILPATH, "w") as f:
                    f.write( json.dumps(FAIL_keys, indent=4) )

                break

            for result in results:
                contributors.append( result['login'] )
                content['commits_count'] += result['contributions']

            if( len(results) < template['per_page'] ): break
            template['page'] += 1

        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

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

            (flag, msg, results, api_calls) = GH_API( GH.API['RELEASES-REPO'], template, CFG['TOKEN'], api_calls )
            if( (not flag) and (msg['CODE'] in [404,422]) ):

                FAIL_keys.append( info['full_name'] )

                with open(FAILPATH, "w") as f:
                    f.write( json.dumps(FAIL_keys, indent=4) )

                break

            releases.extend( results )

            if( len(results) < template['per_page'] ): break
            template['page'] += 1

        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

        content['releases_count'] = len(releases)


        content['open_issues_count'] = info['open_issues_count']

        # closed issue 수를 얻어오기 위한 API 호출
        template = {
            "q"        : "repo:%s+type:issue+state:closed" % info['full_name'],
            "per_page" : 1
        }

        (flag, msg, result, api_calls) = GH_API( GH.API['SEARCH-ISSUE'], template, CFG['TOKEN'], api_calls )
        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

        content['closed_issues_count'] = result['total_count']


        template = {
            "q"        : "repo:%s+type:pr+state:closed" % info['full_name'],
            "per_page" : 1
        }

        (flag, msg, result, api_calls) = GH_API( GH.API['SEARCH-ISSUE'], template, CFG['TOKEN'], api_calls )
        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

        content['closed_pr_count'] = result['total_count']


        template = {
            "q"        : "repo:%s+type:pr+state:open" % info['full_name'],
            "per_page" : 1
        }

        (flag, msg, result, api_calls) = GH_API( GH.API['SEARCH-ISSUE'], template, CFG['TOKEN'], api_calls )
        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

        content['open_pr_count'] = result['total_count']


        template = {
            "owner"    : content['owner'],
            "repo"     : content['repo'],
            "per_page" : 100,
            "page"     : 1
        }
        tags = []

        while True:
            (flag, msg, results, api_calls) = GH_API( GH.API['TAGS-REPO'], template, CFG['TOKEN'], api_calls )
            if( (not flag) and (msg['CODE'] in [404,422]) ):

                FAIL_keys.append( info['full_name'] )

                with open(FAILPATH, "w") as f:
                    f.write( json.dumps(FAIL_keys, indent=4) )

                break

            tags.extend( results )

            if( len(results) < template['per_page'] ): break
            template['page'] += 1
        if( (not flag) and (msg['CODE'] in [404,422]) ):

            FAIL_keys.append( info['full_name'] )

            with open(FAILPATH, "w") as f:
                f.write( json.dumps(FAIL_keys, indent=4) )

            continue

        content['tags_count'] = len(tags)


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

























    # 검색어에 따른 전체 규모를 파악하기 위한 API 호출
    (flag, msg, result) = searchKeyword( template, CFG['TOKEN'] )
    #print("[searchKeyword] items = %s, total_count = %s" % (len(result['items']), result['total_count']))

    searched = {
        'total_count' : int(result['total_count']),
        'items'       : []
    }
    print("[%s] Total Count = %s" % ("main", searched['total_count']))


    # 결과가 1000개 이하면, paging 처리하고 마무리
    if( result['total_count'] < 1000 ):
        print("[%s] under 1000", "main")

        searched['items'] = result['items']

        if( len(searched['items']) == 100 ):
            searched['items'].extend( pagingSearch( template, CFG['TOKEN'] ) )


    # 결과가 1000개 이상이면, 기간을 이용해서 구간 나누어서 검색 처리
    else:

        while True:

            if( result['total_count'] < 1000 ):
                print("under 1000... total_count = %s, Searched = %s (%0.2f%%)" %
                                    (result['total_count'], len(searched['items']), percent(len(searched['items']), searched['total_count'])))

                searched['items'].extend(result['items'])

                temp_total_count = result['total_count']

                if( len(result['items']) == 100 ):
                    searched['items'].extend( pagingSearch( template, CFG['TOKEN'] ) )


            else:
                print("over 1000... total_count = %s, Searched = %s (%0.2f%%)" %
                                    (result['total_count'], len(searched['items']), percent(len(searched['items']), searched['total_count'])))

                print("    [before] delta = %s, start = %s, end = %s" %
                                    (created['delta'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d')))

                (created, template, result) = setCreated( template, CFG['TOKEN'], created, CFG['KEYWORD'], result['total_count'] )

                print("    [after] delta = %s, start = %s, end = %s" %
                                    (created['delta'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d')))

                searched['items'].extend( result['items'] )

                temp_total_count = result['total_count']

                if( len(result['items']) == 100 ):
                    searched['items'].extend( pagingSearch( template, CFG['TOKEN'] ) )


            if( searched['total_count'] <= len(searched['items']) ):
                break


            # 검색 결과가 적을 경우 검색 일정 범위를 넓히기 위한 부분
            # 뭔가 로직을 넣을 수도 있을 것 같은데, 그냥 급히~
            if( temp_total_count < 50 ):
                created['delta'] *= 20
            elif( temp_total_count < 100 ):
                created['delta'] *= 10
            elif( temp_total_count < 200 ):
                created['delta'] *= 5
            elif( temp_total_count < 300 ):
                created['delta'] *= 3
            elif( temp_total_count  < 500 ):
                created['delta'] *= 2

            #print("before total_count: %s, delta: %s" % (temp_total_count, created['delta']))
            print("[%s] Searched = %s (%0.2f%%), delta = %s (%s ~ %s)" %
                ("main", len(searched['items']), percent(len(searched['items']),searched['total_count']),
                    created['delta'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d')))


            created['end'] = created['start'] - datetime.timedelta(days=1)
            created['start'] = created['end'] - datetime.timedelta(days=created['delta'])
            template['page'] = 1

            if( int(created['end'].strftime('%Y')) < 2000 ):
                #created['end'] = date.fromisoformat('2000-01-01')
                #created['start'] = created['end'] - datetime.timedelta(days=created['delta'])
                # 1900년 이전 이슈로 인해서... 2000년 이전 데이터는 일단 무시하는 것으로...
                break

            if( int(created['start'].strftime('%Y')) < 2000 ):
                break


            template['q'] = ( "%s+created:%s..%s+stars:>0" % (CFG['KEYWORD'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d')))
            (flag, msg, result) = searchKeyword( template, CFG['TOKEN'] )


    print("[Finish] Total Count = %s, Searched Count = %s" % (searched['total_count'], len(searched['items'])))




    # 결과 저장하기
    DATADIR = "./data"
    DATAPATH = os.path.join( DATADIR, ("%s.json" % CFG['KEYWORD'].replace("+", "_")) )

    if( not os.path.isdir( DATADIR ) ):
        os.mkdir( DATADIR )
        print( "[%s] mkdir: %s" % ("main", DATADIR) )

    with open(DATAPATH, "w") as f:
        f.write( json.dumps(searched['items'], indent=4) )
    print( "[%s] write file: %s" % ("main", DATAPATH) )



    # 용량이 커서 tar.gz 압축을 해봤다.
    TARPATH = os.path.join( DATADIR, ("%s.tar.gz" % CFG['KEYWORD'].replace("+", "_")) )

    if( os.path.isfile( TARPATH ) ):
        os.remove( TARPATH )
        print( "[%s] remove file: %s" % ("main", TARPATH) )

    tar = tarfile.open( TARPATH, "w:gz")
    tar.add( DATAPATH )
    tar.close()
    print( "[%s] write tar.gz file: %s" % ("main", TARPATH) )

    exit(0)

#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import os
import sys
import datetime
import time
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




# 1page는 규모를 파악하기 위한 검색 결과를 이용해서 함수 호출 전에 저장을 하고
# 2page부터 page를 올려가면서 저장 처리
def pagingSearch( API, template, header ):

    searched = []
    while True:

        template['page'] += 1
        (flag, msg, result) = GH.search( API, template, header )

        print("    [%s] page = %s, items = %s, total_count = %s" % ("pagingSearch", template['page'], len(result['items']), result['total_count']))

        searched.extend( result['items'] )

        if( len(result['items']) < 100 ):
            break

    return searched




# 1000개 한계를 극복하기 위한 기간 조율
# 1000개 이내의 검색 결과를 나오게 하는 기간을 찾아서 리턴
def setCreated( template, header, period, keyword, total_count, stars ):

    result = { 'total_count' : total_count }

    while True:

        # 시작일과 종료을 사이의 간격을 조정
        divnum = (result['total_count'] // 1000) + 1
        period['delta'] = period['delta'] // divnum

        period['start'] = period['end'] - period['delta']

        print("    [%s] delta = %s, start = %s, end = %s" %
                ("setCreated", period['delta'], period['start'].strftime('%Y-%m-%d'), period['end'].strftime('%Y-%m-%d')))

        if( stars ):
            template['q'] = ( "%s+created:%s..%s+stars:>0" % (keyword, period['start'].strftime('%Y-%m-%d'), period['end'].strftime('%Y-%m-%d')))
        else:
            template['q'] = ( "%s+created:%s..%s" % (keyword, period['start'].strftime('%Y-%m-%d'), period['end'].strftime('%Y-%m-%d')))

        (flag, msg, result) = GH.search( GH.API['SEARCH-REPO'], template, header )

        print("    [searchKeyword] items = %s, total_count = %s" % (len(result['items']), result['total_count']))
        print("    [URL] %s" % msg['URL'])

        if( result['total_count'] < 1000 ):
            break

    return (period, template, result)







if __name__ == '__main__':


    # 검색어를 argv 변수로 받아들이기
    if len(sys.argv) == 1 :
        print( "Usage: %s 'keyword'" % sys.argv[0])
        sys.exit (1)


    # 기본적인 설정값들을 담기 위한 변수 선언
    CFG = {
        'NAME'     : sys.argv[0],
        'KEYWORD'  : sys.argv[1].replace(" ", "+"),
        'DIRPATH'  : { 'DATA' : './data' },
        'FILEPATH' : {},
        'STARS'     : True
    }

    CFG['FILEPATH']['JSON'] = os.path.join( CFG['DIRPATH']['DATA'], ("%s.json" % CFG['KEYWORD'].replace("+", "_")) )
    CFG['FILEPATH']['TAR']  = os.path.join( CFG['DIRPATH']['DATA'], ("%s.tar.gz" % CFG['KEYWORD'].replace("+", "_")) )

    if (len(sys.argv) == 3) and (sys.argv[2] == '--no-stars') :
        CFG['STARS'] = False
        print("[Info] No stars option")



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


    # github.com은 1000개 이상의 데이터를 보여주지 않는다.
    # 그래서 기간으로 처리하는 로직을 추가하였고, 우선 20년간 결과를 받아들이도록 하였다.
    #{
    #  "message": "Only the first 1000 search results are available",
    #  "documentation_url": "https://docs.github.com/v3/search/"
    #}
    CFG['PERIOD'] = {
        'start' : '',
        'end'   : '',
        'now'   : datetime.datetime.now(),
        'delta' : datetime.timedelta(days=7300)
    }

    CFG['PERIOD']['end'] = CFG['PERIOD']['now']
    CFG['PERIOD']['start'] = CFG['PERIOD']['end'] - CFG['PERIOD']['delta']


    # 검색을 위한 옵션 모음
    # stars 갯수가 1개 이상인 것들만 검색하기 위한 부분이 추가되어 있다.
    template = {
        "q"        : ("%s+created:%s..%s" % (CFG['KEYWORD'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d'))),
        "sort"     : "stars",
        "order"    : "desc",
        "page"     : 1,
        "per_page" : 100
    }



    print("Start %s (%s).................................................." % (CFG['NAME'], CFG['PERIOD']['now']))
    print("[%s] script name: %s" % ("main", CFG['NAME']))
    print("[%s] search keyword: %s" % ("main", CFG['KEYWORD']))

    if( CFG['STARS'] ):
        template['q'] = "%s+created:%s..%s+stars:>0" % (CFG['KEYWORD'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d'))


    # 검색어에 따른 전체 규모를 파악하기 위한 API 호출
    (flag, msg, result) = GH.search( GH.API['SEARCH-REPO'], template, CFG['HEADER'] )
    #print("    [%s] (%s) URL: %s" % ("searchKeyword", api_call_count, msg['URL']) )
    print("    [%s] API Call = %s, Query = %s" % ("searchKeyword", msg['api_call_count'], template['q']))

    searched = {
        'total_count' : int(result['total_count']),
        'items'       : []
    }
    print("[%s] Total Count = %s" % ("main", searched['total_count']))





    while True:

        if( 'total_count' not in result.keys() ):
            print("[Error] there is not 'total_count'")
            exit()

        if( result['total_count'] < 1000 ):
            print("under 1000... total_count = %s, Searched = %s (%0.2f%%)" %
                                (result['total_count'], len(searched['items']), GH.percent(len(searched['items']), searched['total_count'])))

            searched['items'].extend(result['items'])

            temp_total_count = result['total_count']

            if( len(result['items']) == 100 ):
                searched['items'].extend( pagingSearch(GH.API['SEARCH-REPO'], template, CFG['HEADER']) )


        else:
            print("over 1000... total_count = %s, Searched = %s (%0.2f%%)" %
                                (result['total_count'], len(searched['items']), GH.percent(len(searched['items']), searched['total_count'])))

            print("    [before] delta = %s, start = %s, end = %s" %
                                (CFG['PERIOD']['delta'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d')))

            (created, template, result) = setCreated( template, CFG['HEADER'], CFG['PERIOD'], CFG['KEYWORD'], result['total_count'], CFG['STARS'] )

            print("    [after] delta = %s, start = %s, end = %s" %
                                (CFG['PERIOD']['delta'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d')))

            searched['items'].extend( result['items'] )

            temp_total_count = result['total_count']

            if( len(result['items']) == 100 ):
                searched['items'].extend( pagingSearch(GH.API['SEARCH-REPO'], template, CFG['HEADER']) )


        if( searched['total_count'] <= len(searched['items']) ):
            break


        # RateLimit에 걸리게 되면 reset 되는 때까지 sleep을 하기 위해서
        (flag, msg, result) = GH.getRateLimit( CFG['HEADER'] )
        print("    [%s] core remaining = %s, reset = %s" % ("getRateLimit", result['rate']['remaining'], result['rate']['reset_str']))
        print("    [%s] search remaining = %s, reset = %s" % ("getRateLimit", result['resources']['search']['remaining'], result['resources']['search']['reset_str']))

        #if( result['rate']['remaining'] < 4 ):
        #    print("    [%s] Normal RateLimit. Remain seconds = " % ("ratelimit")),
        #    sleepRateLimit( datetime.datetime.fromtimestamp(result['rate']['reset']) )

        if( result['resources']['search']['remaining'] < 10 ):
            print("    [%s] Search RateLimit. Remain seconds = " % ("ratelimit")),
            sleepRateLimit( datetime.datetime.fromtimestamp(result['resources']['search']['reset']) )



        # 검색 결과가 적을 경우 검색 일정 범위를 넓히기 위한 부분
        # 뭔가 로직을 넣을 수도 있을 것 같은데, 그냥 급히~
        if( temp_total_count < 500 ):
            if( temp_total_count == 0 ):
                CFG['PERIOD']['delta'] *= 2
            else:
                CFG['PERIOD']['delta'] *= (1000 // temp_total_count)
                if( CFG['PERIOD']['delta'] > datetime.timedelta(days=7300) ):
                    CFG['PERIOD']['delta'] = datetime.timedelta(days=7300)



        #print("before total_count: %s, delta: %s" % (temp_total_count, created['delta']))
        print("[%s] Searched = %s (%0.2f%%), delta = %s (%s ~ %s)" %
            ("main", len(searched['items']), GH.percent(len(searched['items']),searched['total_count']),
                CFG['PERIOD']['delta'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d')))


        CFG['PERIOD']['end'] = CFG['PERIOD']['start'] - datetime.timedelta(days=1)
        CFG['PERIOD']['start'] = CFG['PERIOD']['end'] - CFG['PERIOD']['delta']
        template['page'] = 1


        if( int(CFG['PERIOD']['end'].strftime('%Y')) < 1970 ):
            break


        if( CFG['STARS'] ):
            template['q'] = ( "%s+created:%s..%s+stars:>0" %
                            (CFG['KEYWORD'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d')))
        else:
            template['q'] = ( "%s+created:%s..%s" %
                            (CFG['KEYWORD'], CFG['PERIOD']['start'].strftime('%Y-%m-%d'), CFG['PERIOD']['end'].strftime('%Y-%m-%d')))

        (flag, msg, result) = GH.search( GH.API['SEARCH-REPO'], template, CFG['HEADER'] )




    print("[Finish] Total Count = %s, Searched Count = %s" % (searched['total_count'], len(searched['items'])))







    # 결과 저장하기
    DATADIR = "./data"
    DATAPATH = os.path.join( DATADIR, ("%s.json" % CFG['KEYWORD'].replace("+", "_")) )

    if( not os.path.isdir(CFG['DIRPATH']['DATA']) ):
        os.mkdir( CFG['DIRPATH']['DATA'] )
        print( "[%s] mkdir: %s" % ("main", CFG['DIRPATH']['DATA']) )

    with open(CFG['FILEPATH']['JSON'], "w") as f:
        f.write( json.dumps(searched['items'], indent=4) )
    print( "[%s] write file: %s" % ("main", CFG['FILEPATH']['JSON']) )



    # 용량이 커서 tar.gz 압축을 해봤다.
    GH.tarEncode( CFG['FILEPATH']['TAR'], CFG['FILEPATH']['JSON'] )
    print( "[%s] write tar.gz file: %s" % ("main", CFG['FILEPATH']['TAR']) )

    exit(0)

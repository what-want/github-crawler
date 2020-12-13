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


# GitHub로 API를 던지기 위한 함수
def searchKeyword( template, token ):

    # API 호출 횟수를 파악하기 위해서
    global api_call_count

    # topic 값을 얻어오기 위해서는, Header 값을 잡아줘야 한다
    HEADER = { "Accept" : "application/vnd.github.mercy-preview+json" }


    # Timeouts and incomplete results 이슈가 종종 발생하여 (GitHub API 제약) retry 로직을 넣음
    # 5번 이상 재시도를 해도 안된다면 에러 상황이라 판단했다.
    MAX_TRY = 5
    while (MAX_TRY > 0):

        api_call_count += 1

        (flag, msg, result) = GH.getAPI( GH.API['SEARCH-REPO'], template, token, HEADER )

        #print("    [%s] (%s) URL: %s" % ("searchKeyword", api_call_count, msg['URL']) )
        print("    [%s] API Call = %s, Query = %s" % ("searchKeyword", api_call_count, template['q']))

        if( not flag ):
            print( "[%s] %s" % ("searchKeyword", msg['ERROR']) )
            exit()

        if( not result['incomplete_results'] ):
            break

    if( MAX_TRY == 0 ):
        print(msg)
        print(result)
        exit()

    return (flag, msg, result)




# 1page는 규모를 파악하기 위한 검색 결과를 이용해서 함수 호출 전에 저장을 하고
# 2page부터 page를 올려가면서 저장 처리
def pagingSearch( template, token ):

    searched = []

    while True:

        template['page'] += 1

        (flag, msg, result) = searchKeyword( template, token )
        print("    [%s] page = %s, items = %s, total_count = %s" % ("pagingSearch", template['page'], len(result['items']), result['total_count']))

        searched.extend( result['items'] )

        if( len(result['items']) < 100 ):
            break

    return searched




# 1000개 한계를 극복하기 위한 기간 조율
# 1000개 이내의 검색 결과를 나오게 하는 기간을 찾아서 리턴
def setCreated( template, token, created, keyword, total_count ):

    result = { 'total_count' : total_count }

    while True:

        # 시작일과 종료을 사이의 간격을 조정
        divnum = (result['total_count'] // 1000) + 1
        created['delta'] = created['delta'] // divnum

        created['start'] = created['end'] - datetime.timedelta(days=created['delta'])

        print("    [%s] delta = %s, start = %s, end = %s" %
                ("setCreated", created['delta'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d')))


        template['q'] = ( "%s+created:%s..%s+stars:>0" % (keyword, created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d')))
        (flag, msg, result) = searchKeyword( template, token )

        print("    [searchKeyword] items = %s, total_count = %s" % (len(result['items']), result['total_count']))

        if( result['total_count'] < 1000 ):
            break

    return (created, template, result)



def percent( part, whole ):
    return 100*float(part)/float(whole)




if __name__ == '__main__':


    # 검색어를 argv 변수로 받아들이기
    if len (sys.argv) != 2 :
        print( "Usage: %s 'keyword'" % sys.argv[0])
        sys.exit (1)


    # 기본적인 설정값들을 담기 위한 변수 선언
    CFG = {
        'NAME'    : sys.argv[0],
        'KEYWORD' : sys.argv[1].replace(" ", "+")
    }


    # 환경변수 'WW_TOKEN'으로 GitHub Token 값을 선언해놓아야 한다.
    # 없으면 API 60개/hour 밖에 호출하지 못한다.
    #
    # $ export WW_TOKEN=xxxxxxxxxx
    #
    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    if( CFG['TOKEN'] == "" ):
        print( "[%s] token is empty" % "main" )


    # github.com은 1000개 이상의 데이터를 보여주지 않는다.
    #
    #{
    #  "message": "Only the first 1000 search results are available",
    #  "documentation_url": "https://docs.github.com/v3/search/"
    #}
    #
    # 그래서 기간으로 처리하는 로직을 추가하였고, 우선 20년간 결과를 받아들이도록 하였다.
    created = {
        'start' : '',
        'end'   : '',
        'now'   : datetime.datetime.now(),
        'delta' : 7300
    }

    created['end'] = created['now']
    created['start'] = created['end'] - datetime.timedelta(days=created['delta'])


    # 검색을 위한 옵션 모음
    # stars 갯수가 1개 이상인 것들만 검색하기 위한 부분이 추가되어 있다.
    template = {
        "q"        : ("%s+created:%s..%s+stars:>0" % (CFG['KEYWORD'], created['start'].strftime('%Y-%m-%d'), created['end'].strftime('%Y-%m-%d'))),
        "sort"     : "stars",
        "order"    : "desc",
        "page"     : 1,
        "per_page" : 100
    }



    print("Start %s (%s).................................................." % (CFG['NAME'], created['now']))

    print("[%s] script name: %s" % ("main", CFG['NAME']))
    print("[%s] search keyword: %s" % ("main", CFG['KEYWORD'].replace('+',' ')))



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

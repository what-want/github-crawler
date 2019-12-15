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


if __name__ == '__main__':


    # Debugging을 위한 logging 모듈 환경 설정 값 읽어오기
    with open('logging.json', 'rt') as f:
        config = json.load(f)

    logging.config.dictConfig(config)
    logger = logging.getLogger()


    # 검색어를 argv 변수로 받아들이기
    if len (sys.argv) != 2 :
        print( "Usage: %s 'keyword'" % sys.argv[0])
        sys.exit (1)


    # 기본적인 설정값들을 담기 위한 변수 선언
    CFG = {
        'NAME'    : sys.argv[0],
        'KEYWORD' : sys.argv[1]
    }




    logger.info( "Start %s .................................................." % CFG['NAME'] )

    logger.info( "[%s] script name: %s" % ("main", CFG['NAME']) )
    logger.info( "[%s] search keyword: %s" % ("main", CFG['KEYWORD']) )




    # GitHub Action을 사용함에 따라 token 값을 환경 변수로 받아들이기 위한 로직

    # TOKEN 값이 없으면 연속으로 10번 이상 API 던지면 바로 아래와 같은 메시지 출력
    #{   u'documentation_url': u'https://developer.github.com/v3/#rate-limiting',
    #    u'message': u"API rate limit exceeded for 110.12.220.235. (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.)"}
    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    if( CFG['TOKEN'] == "" ):
        logger.warning( "[%s] token is empty" % "main" )



    # GitHub API 사용을 위한 template 설정
    template = {
        "q"        : CFG['KEYWORD'].replace(" ", "%20"),
        "sort"     : "stars",
        #"sort"     : "created",
        "order"    : "desc",
        "page"     : 1,
        "per_page" : 100
    }

    # topic 값을 얻어오기 위해서는, Header 값을 잡아줘야 한다
    HEADER = { "Accept" : "application/vnd.github.mercy-preview+json" }
    contents = []
    contents_keys = []

    # GitHub API 1000개 제한을 극복하고자 날짜를 기준으로 검색을 나누고자 구현한 로직
    created_date_end = datetime.datetime.now()
    days_delta = 90


    # API 횟수 제한을 확인해보기 위한 값
    api_calls = 0


    while True:
        LOOP1 = True
        template['page'] = 1



        # search result가 적절히 나오는지 확인해서 days_delta 값 보정해주기
        while True:
            LOOP2 = True


            # 2014년 이후 데이터만 취하는 것으로~
            if( created_date_end.strftime('%Y') < "2013" ):
                LOOP1 = False
                break


            # created_date_end 에서 하루를 더하는 것은 아래 query에서 between 표현을 할 때 경계값을 놓치지 않기 위해서
            created_date_end += datetime.timedelta(days=1)
            created_date_start = created_date_end - datetime.timedelta(days=days_delta)

            if( created_date_start.strftime('%Y') < "2013" ):
                created_date_start = datetime.datetime.strptime('2012-12-31 23:59:59', '%Y-%m-%d %H:%M:%S')


            # between을 표현하는 방법은 .. 이다. >= + < 방식을 이용하면 원하는 결과가 나오지 않는다.
            template['q'] = ( "%s+created:%s..%s+stars:>0" % (CFG['KEYWORD'].replace(" ", "%20"), created_date_start.strftime('%Y-%m-%d'), created_date_end.strftime('%Y-%m-%d')) )
            logger.info( "[%s] Query: %s" % ("main", template['q']) )

            # days_delta 값을 보정하기 위해서 search를 먼저 해보고 total_count 값으로 조정하기 위한 로직
            (flag, msg, result) = GH.getAPI( GH.API['SEARCH-REPO'], template, CFG['TOKEN'], HEADER )
            api_calls += 1
            logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
            if( not flag ):
                logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
                exit()

            logger.info( "[%s] days_delta: %s" % ("getAPI", days_delta) )
            logger.info( "[%s] total_count: %s" % ("getAPI", result['total_count']) )

            division = result['total_count'] // 1000
            if( division < 1 ):
                if( result['total_count'] < 500 ):
                    days_delta *= 2
                break

            days_delta = days_delta // (division+1)


        if( not LOOP1 ): break



        while True:


            if( template['page'] != 1 ):

                (flag, msg, result) = GH.getAPI( GH.API['SEARCH-REPO'], template, CFG['TOKEN'], HEADER )
                api_calls += 1
                logger.info( "[%s] (%s) URL: %s" % ("getAPI", api_calls, msg['URL']) )
                if( not flag ):
                    logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
                    exit()

            else:
                logger.info( "[%s] total count: %s" % ("getAPI", result['total_count']) )



            logger.info( "[%s] page: %s" % ("getAPI", template['page']) )

            items_count = len(result['items'])
            logger.info( "[%s] items count: %s" % ("getAPI", items_count) )



            # 검색 결과가 중복된 것이 나오는지 확인하기 위한 로직
            for idx, item in enumerate(result['items']):
                if( item['full_name'] in contents_keys ):
                    del result['items'][idx]
                else:
                    contents_keys.append( item['full_name'] )

            contents.extend( result['items'] )
            logger.info( "[%s] total items count: %s" % ("getAPI", len(contents)) )


            if( items_count < template['per_page'] ): break
            template['page'] += 1
            #if( template['page'] > 2 ): break

        logger.info( "[%s] loaded items count: %s" % ("main", len(contents)) )

        # 날짜를 이어서 검색할 수 있도록 하기 위해서
        created_date_end = created_date_start


    DATADIR = "./data"
    DATAPATH = os.path.join( DATADIR, ("%s.json" % CFG['KEYWORD'].replace(" ", "_")) )
    if( os.path.isfile( DATAPATH ) ):
        os.remove( DATAPATH )
        logger.info( "[%s] remove file: %s" % ("main", DATAPATH) )

    if( not os.path.isdir( DATADIR ) ):
        os.mkdir( DATADIR )
        logger.info( "[%s] mkdir: %s" % ("main", DATADIR) )


    with open(DATAPATH, "w") as f:
        f.write( json.dumps(contents, indent=4) )
    logger.info( "[%s] write file: %s" % ("main", DATAPATH) )



    TARPATH = os.path.join( "./data/", ("%s.tar.gz" % CFG['KEYWORD'].replace(" ", "_")) )

    if( os.path.isfile( TARPATH ) ):
        os.remove( TARPATH )
        logger.info( "[%s] remove file: %s" % ("main", TARPATH) )

    tar = tarfile.open( TARPATH, "w:gz")
    tar.add( DATAPATH )
    tar.close()
    logger.info( "[%s] write tar.gz file: %s" % ("main", TARPATH) )

    #os.remove( DATAPATH )
    #logger.info( "[%s] remove file: %s" % ("main", DATAPATH) )

    exit(0)

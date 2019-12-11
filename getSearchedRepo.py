#!/usr/bin/python
#-*-coding:utf-8-*-

import logging.config
import json
import os
import sys
import datetime

import libGH as GH


if __name__ == '__main__':

    with open('logging.json', 'rt') as f:
        config = json.load(f)

    logging.config.dictConfig(config)
    logger = logging.getLogger()



    if len (sys.argv) != 2 :
        print( "Usage: %s 'keyword'" % sys.argv[0])
        sys.exit (1)



    CFG = {
        'NAME'    : sys.argv[0],
        'KEYWORD' : sys.argv[1]
    }


    logger.info( "Start %s .................................................." % CFG['NAME'] )

    logger.info( "[%s] script name: %s" % ("main", CFG['NAME']) )
    logger.info( "[%s] search keyword: %s" % ("main", CFG['KEYWORD']) )



    # TOKEN 값이 없으면 연속으로 10번 이상 API 던지면 바로 아래와 같은 메시지 출력
    #{   u'documentation_url': u'https://developer.github.com/v3/#rate-limiting',
    #    u'message': u"API rate limit exceeded for 110.12.220.235. (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.)"}

    CFG['TOKEN'] = os.environ.get('WW_TOKEN', "")
    if( CFG['TOKEN'] == "" ):
        logger.warning( "[%s] token is empty" % "main" )



    template = {
        "q"        : CFG['KEYWORD'].replace(" ", "%20"),
        #"sort"     : "stars",
        "sort"     : "created",
        "order"    : "desc",
        "page"     : 1,
        "per_page" : 100
    }

    HEADER = { "Accept" : "application/vnd.github.mercy-preview+json" }
    contents = []
    contents_keys = []

    # GitHub API 1000개 제한을 극복하고자 날짜를 기준으로 검색을 나누고자 구현한 로직
    created_date = datetime.datetime.now()

    while True:
        template['page'] = 1

        # 일단 10일 단위로 검색을 분리
        created_date = created_date - datetime.timedelta(days=20)
        template['q'] = ( "%s+created:>%s" % (CFG['KEYWORD'].replace(" ", "%20"), created_date.strftime('%Y-%m-%d')) )
        logger.info( "[%s] Query: %s" % ("main", template['q']) )

        contents_count = len(contents)

        while True:

            (flag, msg, result) = GH.getAPI( GH.API['SEARCH-REPO'], template, CFG['TOKEN'], HEADER )
            logger.info( "[%s] URL: %s" % ("getAPI", msg['URL']) )

            if(not flag):
                logger.error( "[%s] %s" % ("getAPI", msg['ERROR']) )
                sys.exit(1)

            if( template['page'] == 1 ):
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


            if( len(result['items']) < template['per_page'] ): break
            if( len(result['items']) != items_count ): break
            template['page'] += 1
            #if( template['page'] > 2 ): break

        logger.info( "[%s] loaded items count: %s" % ("main", len(contents)) )
        if( contents_count == len(contents) ): break



    DATAPATH = os.path.join( "./", "data.csv" )
    if( os.path.isfile( DATAPATH ) ):
        os.remove( DATAPATH )
        logger.info( "[%s] remove file: %s" % ("main", DATAPATH) )

    with open(DATAPATH, "w") as f:
        f.write( json.dumps(contents, indent=4) )
    logger.info( "[%s] write file: %s" % ("main", DATAPATH) )

    exit(0)

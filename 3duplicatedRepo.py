#!/usr/bin/python
#-*-coding:utf-8-*-

import argparse
import os
import sys
import pandas as pd
from pprint import pprint


import json
import datetime
import time
import tarfile

# GitHub 관련된 모듈을 넣어 놓은 모듈
import libGH as GH



def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--keyword', required=True, help='keyword')
    parser.add_argument('--path', required=True, help='work directory path')

    return parser.parse_args()



def get_CSVFiles( path, excepted_filepath="" ):
    results = {
        'flag' : True,
        'msg'  : {},
        'data' : []
    }

    if os.path.isdir(path):

        excepted_file = os.path.basename( excepted_filepath )
        for file in os.listdir(path):
            if file.endswith('.csv') and (file != excepted_file):
                results['data'].append( os.path.join(path,file) )

    else:
        results['flag'] = False
        results['msg'] = '%s is not directory' % path

    return results


if __name__ == '__main__':

    args = parse_args()

    OPT = {
        'NAME'     : sys.argv[0],
        'keyword'  : args.keyword,
        'DIRPATH'  : {
            'data' : args.path
        },
        'FILEPATH' : {
            'tar'    : os.path.join(args.path,'%s.tar.gz' % args.keyword),
            'target' : os.path.join(args.path,'%s.csv' % args.keyword)
        },
        'TIME'     : {
            'now'  : datetime.datetime.now()
        }
    }


    CONTENTS = {
        'raws'        : "",
        'total_count' : 0,
        'target_df'   : "",
        'source_df'   : "",
        'add_count'   : 0
    }


    print("Start %s (%s).................................................." % (OPT['NAME'], OPT['TIME']['now']))
    print("[Info] script name: %s" % (OPT['NAME']))
    print("[Info] keyword : %s, data path : %s" % (OPT['keyword'], OPT['DIRPATH']['data']))
    print("[Info] target filepah : %s" % OPT['FILEPATH']['target'])


    results = get_CSVFiles(OPT['DIRPATH']['data'], OPT['FILEPATH']['target'])
    if(not results['flag']):
        sys.exit('[Error] %s' % results['msg'])
    OPT['FILEPATH']['CSVs'] = results['data']
    print('[Info] Loaded CSV Files : %s files' % len(OPT['FILEPATH']['CSVs']))


    OPT['FILEPATH']['json'] = GH.tarDecode( OPT['FILEPATH']['tar'] )
    with open( OPT['FILEPATH']['json'] ) as f:
        CONTENTS['raws'] = json.load(f)


    CONTENTS['total_count'] = len(CONTENTS['raws'])
    print( "[Info] json filename: %s" % (OPT['FILEPATH']['json']) )
    print( "[Info] loaded total counts: %s" % (CONTENTS['total_count']) )


    if( os.path.isfile(OPT['FILEPATH']['target']) ):
        CONTENTS['target_df'] = pd.read_csv(OPT['FILEPATH']['target'])
        print('[Info] loaded previous target data : %s' % CONTENTS['target_df'].shape[0])


    for file in OPT['FILEPATH']['CSVs']:
        csv_df = pd.read_csv(file)

        if( type(CONTENTS['source_df']) == type("") ):
            CONTENTS['source_df'] = csv_df

        else:
            CONTENTS['source_df'] = pd.concat( [CONTENTS['source_df'], csv_df], axis=0 )

        print("  source_df length = %s" % CONTENTS['source_df'].shape[0])


    for idx, raw in enumerate(CONTENTS['raws'], start=1):

        print('[%s/%s, %0.2f%%] %s : ' % (idx, CONTENTS['total_count'], GH.percent(idx, CONTENTS['total_count']), raw['full_name'])),
        sys.stdout.flush()

        searched = CONTENTS['target_df'][(CONTENTS['target_df']['repo'] == raw['name']) & (CONTENTS['target_df']['owner'] == raw['owner']['login'])]
        if( searched.shape[0] > 0 ):
            #print( '%s/%s - %s' % (searched.iloc[0]['owner'], searched.iloc[0]['repo'], searched.iloc[0]['created_at']) )
            print('pass')
            continue


        searched = CONTENTS['source_df'][(CONTENTS['source_df']['repo'] == raw['name']) & (CONTENTS['source_df']['owner'] == raw['owner']['login'])]
        if( searched.shape[0] > 0 ):

            CONTENTS['target_df'] = CONTENTS['target_df'].append( searched, ignore_index=True )
            CONTENTS['add_count'] += 1
            print('add info from previous data')
            continue

        print('have no info')



    CONTENTS['target_df'].to_csv(OPT['FILEPATH']['target'], header=True, index=False)
    print('[Info] Write contents : %s (added item = %s)' % (OPT['FILEPATH']['target'], CONTENTS['add_count']))
    exit(0)

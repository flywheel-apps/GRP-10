#!/usr/bin/env python

import os
import sys
import json
import argparse
import pandas as pd
import flywheel
import datetime

def search_with_query(return_type, query):
    search = fw.search({'return_type': return_type, 'structured_query': query}, size=10000)
    return search


def search_to_csv(search, filepath):
    df_list = []
    for result in search:
        tmp_dict = {}
        for key, value in result.items():
            tmp_dict[key] = [value]
        tmp_df = pd.DataFrame(data=tmp_dict)
        df_list.append(tmp_df)
    df = pd.concat(df_list, ignore_index=True)
    csv_path = filepath + '.csv'
    df.to_csv(csv_path,index=False)


def search_to_json(search, filepath):
    json_path = filepath + '.json'
    with open(json_path, 'w') as outfile:
        json.dump(search, outfile, separators=(', ', ': '), sort_keys=True, indent=4)

def get_keys(d, keystring=''):
    key_list = []
    for k,v in d.items():
        if isinstance(v, dict):
            newkeystring = keystring + k + '.'
            key_list += get_keys(v, newkeystring)
        elif isinstance(v, list):
            pass
        else:
            if keystring == '':
                string = k
            else:
                string = keystring+k
            key_list.append(string)
    return key_list


def filter_search(search, column_list):
    filtered_search = []
    for result in search:
        result_dict = {}
        for column in column_list:
            try:
                result_dict[column] = eval("result.{}".format(column))
            except AttributeError:
                result_dict[column] = ""
            if type(result_dict[column])==datetime.datetime:
                result_dict[column] = str(result_dict[column])
        filtered_search.append(result_dict)
    return filtered_search


if __name__ == '__main__':
    # Gear basics
    input_folder = '/flywheel/v0/input/file/'
    output_folder = '/flywheel/v0/output/'

    # Declare config file path
    config_file_path = '/flywheel/v0/config.json'

    # Load config file
    with open(config_file_path) as config_data:
        config = json.load(config_data)
    # Set config options
    for key, value in config['config'].items():
        exec(key + " = value")
    if return_type not in ['session', 'analysis', 'file', 'acquisition']:
        os.sys.exit(1)
    output_file_path = os.path.join(output_folder, return_type)
    # Get API key
    api_key = config['inputs']['api-key']['key']
    # Create client
    fw = flywheel.Client(api_key)

    search = search_with_query(return_type, query)
    if len(search) == 0:
        print("No search results - exiting...")
        os.sys.exit(1)

    column_list = get_keys(search[0].to_dict())


    search = filter_search(search, column_list)
    if file_name == "":
        file_name = return_type
    if create_csv_file:
        search_to_csv(search, output_file_path)
    if create_json_file:
        search_to_json(search, output_file_path)

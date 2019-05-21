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
    for k, v in d.items():
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
                result_dict[column] = None
            if type(result_dict[column]) not in [str, int, float]:

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
    config_options = config['config']
    # Get API key
    api_key = config['inputs']['api-key']['key']

    for return_type in ['session', 'acquisition', 'analysis', 'file']:
        print("searching {}".format(return_type))
        search_key = return_type + "_search"
        if config_options[search_key]:
            if config_options['file_name'] != "":
                file_name = config_options['file_name'] + "_" + return_type
            else:
                file_name = return_type
            output_file_path = os.path.join(output_folder, file_name)

            # Create client
            fw = flywheel.Client(api_key)

            search = search_with_query(return_type, config_options["query"])
            if len(search) == 0:
                print("No search results - exiting...")
                os.sys.exit(1)

            try:
                column_config_filepath = config['inputs']['column_config']['location']['path']
                with open(column_config_filepath) as config_data:
                    column_config = json.load(config_data)
                column_list = column_config[return_type]
            except KeyError:
                column_list = get_keys(search[0].to_dict())
            search = filter_search(search, column_list)

            file_name = config_options['file_name'] + return_type
            if config_options['create_csv_file']:
                search_to_csv(search, output_file_path)
            if config_options['create_json_file']:
                search_to_json(search, output_file_path)
        else:
            print('Skipping {}...'.format(return_type))

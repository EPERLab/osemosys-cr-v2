import os
import re
import csv
import pandas as pd
import sys

def test1():
    print( 'hello world' )
############################################################################################################################
def execute_local_dataset_creator_0_outputs ():
    file_aboslute_address = os.path.abspath("local_dataset_creator_0.py")
    file_adress = re.escape( file_aboslute_address.replace( 'local_dataset_creator_0.py', '' ) ).replace( '\:', ':' )
    file_adress+='\\Executables\\'
    #
    case_list_raw = os.listdir( file_adress )
    case_list =  [e for e in case_list_raw if ('.py' not in e ) and ('.csv' not in e ) and ('__pycache__' not in e) ]
    #
    li = []
    #
    for n in range( len( case_list ) ):
        filename = file_adress + case_list[n] + '\\' + case_list[n] + '_Output.csv'
        #
        line_count = 0
        with open( filename ) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                line_count += 1
        if line_count > 1:
            df = pd.read_csv(filename, index_col=None, header=0)
            li.append(df)
        else:
            pass
    #
    frame = pd.concat(li, axis=0, ignore_index=True)
    export_csv = frame.to_csv ( str(file_adress) + '\\output_dataset_0.csv', index = None, header=True)
    print( file_adress )
############################################################################################################################
def execute_local_dataset_creator_0_inputs ():
    file_aboslute_address = os.path.abspath("local_dataset_creator_0.py")
    file_adress = re.escape( file_aboslute_address.replace( 'local_dataset_creator_0.py', '' ) ).replace( '\:', ':' )
    file_adress+='\\Executables\\'
    #
    case_list_raw = os.listdir( file_adress )
    case_list =  [e for e in case_list_raw if ('.py' not in e ) and ('.csv' not in e ) and ('__pycache__' not in e) ]
    #
    li = []
    #
    for n in range( len( case_list ) ):
        filename = file_adress + case_list[n] + '\\' + case_list[n] + '_Input.csv'
        #
        line_count = 0
        with open( filename ) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                line_count += 1
        if line_count > 1:
            df = pd.read_csv(filename, index_col=None, header=0)
            li.append(df)
        else:
            pass
    #
    frame = pd.concat(li, axis=0, ignore_index=True)
    export_csv = frame.to_csv ( str(file_adress) + '\\input_dataset_0.csv', index = None, header=True)
############################################################################################################################
def execute_local_dataset_creator_0_prices ():
    file_aboslute_address = os.path.abspath("local_dataset_creator_0.py")
    file_adress = re.escape( file_aboslute_address.replace( 'local_dataset_creator_0.py', '' ) ).replace( '\:', ':' )
    file_adress+='\\Executables\\'
    #
    case_list_raw = os.listdir( file_adress )
    case_list =  [e for e in case_list_raw if ('.py' not in e ) and ('.csv' not in e ) and ('__pycache__' not in e) ]
    #
    li = []
    #
    for n in range( len( case_list ) ):
        filename = file_adress + case_list[n] + '\\' + case_list[n] + '_Prices.csv'
        #
        line_count = 0
        with open( filename ) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                line_count += 1
        if line_count > 1:
            df = pd.read_csv(filename, index_col=None, header=0)
            li.append(df)
        else:
            pass
    #
    frame = pd.concat(li, axis=0, ignore_index=True)
    export_csv = frame.to_csv ( str(file_adress) + '\\price_dataset_0.csv', index = None, header=True)
############################################################################################################################
def execute_local_dataset_creator_0_distribution ():
    file_aboslute_address = os.path.abspath("local_dataset_creator_0.py")
    file_adress = re.escape( file_aboslute_address.replace( 'local_dataset_creator_0.py', '' ) ).replace( '\:', ':' )
    file_adress+='\\Executables\\'
    #
    case_list_raw = os.listdir( file_adress )
    case_list =  [e for e in case_list_raw if ('.py' not in e ) and ('.csv' not in e ) and ('__pycache__' not in e) ]
    #
    li = []
    #
    for n in range( len( case_list ) ):
        filename = file_adress + case_list[n] + '\\' + case_list[n] + '_Distribution.csv'
        #
        line_count = 0
        with open( filename ) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                line_count += 1
        if line_count > 1:
            df = pd.read_csv(filename, index_col=None, header=0)
            li.append(df)
        else:
            pass
    #
    frame = pd.concat(li, axis=0, ignore_index=True)
    export_csv = frame.to_csv ( str(file_adress) + '\\distribution_dataset_0.csv', index = None, header=True)
############################################################################################################################

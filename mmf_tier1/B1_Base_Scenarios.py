# -*- coding: utf-8 -*-
"""
@author: Luis Victor-Gallardo // 2021
"""
import errno
import scipy
import pandas as pd
import numpy as np
import xlrd
import re
import csv
import os, os.path
import sys
import math
import linecache
from copy import deepcopy
import time
import gc
import shutil
import pickle
import multiprocessing as mp

'''
We implement OSEMOSYS-CR in a csv based system for semi-automatic manipulation of parameters.
'''
def intersection_2(lst1, lst2): 
    return list(set(lst1) & set(lst2))
#
def interp_max_cap( x ):
    x_change_known = []
    x_unknown = []
    last_big_known = 0
    x_pick = [ x[0] ]
    for n in range( 1, len( x ) ):
        if x[n] > x[n-1] and x[n-1] >= last_big_known:
            last_big_known = x[n-1]
            appender = x[n]
            x_change_known.append( x[n] )
            x_unknown.append( 'none' )
            x_pick.append( x[n] )
        else:
            if x[n] >= last_big_known and x[n] > x_change_known[0]:
                x_change_known.append( x[n] )
                x_unknown.append( 'none' )
                x_pick.append( x[n] )
            else:
                x_change_known.append( 'none' )
                x_unknown.append( x[n] )
                x_pick.append( appender )
    return x_pick
    #
#
def main_executer(n1, packaged_useful_elements, scenario_list_print):
    set_first_list(scenario_list_print)
    file_aboslute_address = os.path.abspath("B1_Base_Scenarios.py")
    file_adress = re.escape( file_aboslute_address.replace( 'B1_Base_Scenarios.py', '' ) ).replace( '\:', ':' )
    #
    case_address = file_adress + r'Executables\\' + str( first_list[n1] )
    this_case = [ e for e in os.listdir( case_address ) if '.txt' in e ]
    #
    str1 = "start /B start cmd.exe @cmd /k cd " + file_adress
    #
    data_file = case_address.replace('./','').replace('/','\\') + '\\' + str( this_case[0] )
    output_file = case_address.replace('./','').replace('/','\\') + '\\' + str( this_case[0] ).replace('.txt','') + '_output' + '.txt'
    #
    str2 = "glpsol -m OSeMOSYS_Model.txt -d " + str( data_file )  +  " -o " + str(output_file)
    os.system( str1 and str2 )
    time.sleep(1)
    #
    data_processor(n1,packaged_useful_elements)
    #
#
def set_first_list(scenario_list_print):
    #
    first_list_raw = os.listdir( './Executables' )
    #
    global first_list
    scenario_list_print_with_fut = [ e + '_0' for e in scenario_list_print ]
    first_list = [e for e in first_list_raw if ( '.csv' not in e ) and ( 'Table' not in e ) and ( '.py' not in e ) and ( '__pycache__' not in e ) and ( e in scenario_list_print_with_fut ) ]
    #
#
def data_processor( case, unpackaged_useful_elements ):
    #
    Reference_driven_distance =     unpackaged_useful_elements[0]
    Reference_occupancy_rate =      unpackaged_useful_elements[1]
    Reference_op_life =             unpackaged_useful_elements[2]
    Fleet_Groups_inv =              unpackaged_useful_elements[3]
    time_range_vector =             unpackaged_useful_elements[4]
    list_param_default_value_params = unpackaged_useful_elements[5]
    list_param_default_value_value = unpackaged_useful_elements[6]
    list_gdp_ref = unpackaged_useful_elements[7]

    # Extract the default (national) discount rate parameter
    dr_prm_idx = list_param_default_value_params.index('DiscountRate')
    dr_default = list_param_default_value_value[dr_prm_idx]

    # Briefly open up the system coding to use when processing for visualization:
    df_fuel_to_code = pd.read_excel( './A1_Inputs/A-I_Classifier_Modes_Transport.xlsx', sheet_name='Fuel_to_Code' )
    df_fuel_2_code_fuel_list        = df_fuel_to_code['Code'].tolist()
    df_fuel_2_code_plain_english    = df_fuel_to_code['Plain_English'].tolist()
    df_tech_to_code = pd.read_excel( './A1_Inputs/A-I_Classifier_Modes_Transport.xlsx', sheet_name='Tech_to_Code' )
    df_tech_2_code_fuel_list        = df_tech_to_code['Techs'].tolist()
    df_tech_2_code_plain_english    = df_tech_to_code['Plain_English'].tolist()
    #
    # 1 - Always call the structure of the model:
    #-------------------------------------------#
    structure_filename = "B1_Model_Structure.xlsx"
    structure_file = pd.ExcelFile(structure_filename)
    structure_sheetnames = structure_file.sheet_names  # see all sheet names
    sheet_sets_structure = pd.read_excel(open(structure_filename, 'rb'),
                                         header=None,
                                         sheet_name=structure_sheetnames[0])
    sheet_params_structure = pd.read_excel(open(structure_filename, 'rb'),
                                           header=None,
                                           sheet_name=structure_sheetnames[1])
    sheet_vars_structure = pd.read_excel(open(structure_filename, 'rb'),
                                         header=None,
                                         sheet_name=structure_sheetnames[2])

    S_DICT_sets_structure = {'set':[],'initial':[],'number_of_elements':[],'elements_list':[]}
    for col in range(1,11+1):  # 11 columns
        S_DICT_sets_structure['set'].append( sheet_sets_structure.iat[0, col] )
        S_DICT_sets_structure['initial'].append( sheet_sets_structure.iat[1, col] )
        S_DICT_sets_structure['number_of_elements'].append( int( sheet_sets_structure.iat[2, col] ) )
        #
        element_number = int( sheet_sets_structure.iat[2, col] )
        this_elements_list = []
        if element_number > 0:
            for n in range( 1, element_number+1 ):
                this_elements_list.append( sheet_sets_structure.iat[2+n, col] )
        S_DICT_sets_structure['elements_list'].append( this_elements_list )
    #
    S_DICT_params_structure = {'category':[],'parameter':[],'number_of_elements':[],'index_list':[]}
    param_category_list = []
    for col in range(1,30+1):  # 30 columns
        if str( sheet_params_structure.iat[0, col] ) != '':
            param_category_list.append( sheet_params_structure.iat[0, col] )
        S_DICT_params_structure['category'].append( param_category_list[-1] )
        S_DICT_params_structure['parameter'].append( sheet_params_structure.iat[1, col] )
        S_DICT_params_structure['number_of_elements'].append( int( sheet_params_structure.iat[2, col] ) )
        #
        index_number = int( sheet_params_structure.iat[2, col] )
        this_index_list = []
        for n in range(1, index_number+1):
            this_index_list.append( sheet_params_structure.iat[2+n, col] )
        S_DICT_params_structure['index_list'].append( this_index_list )
    #
    S_DICT_vars_structure = {'category':[],'variable':[],'number_of_elements':[],'index_list':[]}
    var_category_list = []
    for col in range(1,43+1):  # 43 columns
        if str( sheet_vars_structure.iat[0, col] ) != '':
            var_category_list.append( sheet_vars_structure.iat[0, col] )
        S_DICT_vars_structure['category'].append( var_category_list[-1] )
        S_DICT_vars_structure['variable'].append( sheet_vars_structure.iat[1, col] )
        S_DICT_vars_structure['number_of_elements'].append( int( sheet_vars_structure.iat[2, col] ) )
        #
        index_number = int( sheet_vars_structure.iat[2, col] )
        this_index_list = []
        for n in range(1, index_number+1):
            this_index_list.append( sheet_vars_structure.iat[2+n, col] )
        S_DICT_vars_structure['index_list'].append( this_index_list )
    #-------------------------------------------#
    all_vars = ['Demand',
                'NewCapacity',
                'AccumulatedNewCapacity',
                'TotalCapacityAnnual',
                'TotalTechnologyAnnualActivity',
                'ProductionByTechnology',
                'UseByTechnology',
                'CapitalInvestment',
                'DiscountedCapitalInvestment',
                'SalvageValue',
                'DiscountedSalvageValue',
                'OperatingCost',
                'DiscountedOperatingCost',
                'AnnualVariableOperatingCost',
                'AnnualFixedOperatingCost',
                'TotalDiscountedCostByTechnology',
                'TotalDiscountedCost',
                'AnnualTechnologyEmission',
                'AnnualTechnologyEmissionPenaltyByEmission',
                'AnnualTechnologyEmissionsPenalty',
                'DiscountedTechnologyEmissionsPenalty',
                'AnnualEmissions'
                ]
    #
    more_vars = [   'DistanceDriven',
                    'Fleet',
                    'NewFleet',
                    'ProducedMobility']
    #
    filter_vars = [ 'FilterFuelType',
                    'FilterVehicleType',
                    # 'DiscountedTechnEmissionsPen',
                    #
                    'Capex2021', # CapitalInvestment
                    'FixedOpex2021', # AnnualFixedOperatingCost
                    'VarOpex2021', # AnnualVariableOperatingCost
                    'Opex2021', # OperatingCost
                    'Externalities2021', # AnnualTechnologyEmissionPenaltyByEmission
                    #
                    'Capex_GDP', # CapitalInvestment
                    'FixedOpex_GDP', # AnnualFixedOperatingCost
                    'VarOpex_GDP', # AnnualVariableOperatingCost
                    'Opex_GDP', # OperatingCost
                    'Externalities_GDP' # AnnualTechnologyEmissionPenaltyByEmission
                    ]
    #
    all_vars_output_dict = [ {} for e in range( len( first_list ) ) ]
    #
    output_header = [ 'Strategy', 'Future.ID', 'Fuel', 'Technology', 'Emission', 'Year' ]
    #-------------------------------------------------------#
    for v in range( len( all_vars ) ):
        output_header.append( all_vars[v] )
    for v in range( len( more_vars ) ):
        output_header.append( more_vars[v] )
    for v in range( len( filter_vars ) ):
        output_header.append( filter_vars[v] )
    #-------------------------------------------------------#
    this_strategy = first_list[case].split('_')[0] 
    this_future   = first_list[case].split('_')[1]
    #-------------------------------------------------------#
    #
    vars_as_appear = []
    data_name = str( './Executables/' + first_list[case] ) + '/' + str(first_list[case]) + '_output.txt'
    #
    n = 0
    break_this_while = False
    while break_this_while == False:
        n += 1
        structure_line_raw = linecache.getline(data_name, n)
        if 'No. Column name  St   Activity     Lower bound   Upper bound    Marginal' in structure_line_raw:
            ini_line = deepcopy( n+2 )
        if 'Karush-Kuhn-Tucker' in structure_line_raw:
            end_line = deepcopy( n-1 )
            break_this_while = True
            break
    #
    for n in range(ini_line, end_line, 2 ):
        structure_line_raw = linecache.getline(data_name, n)
        structure_list_raw = structure_line_raw.split(' ')
        #
        structure_list_raw_2 = [ s_line for s_line in structure_list_raw if s_line != '' ]
        structure_line = structure_list_raw_2[1]
        structure_list = structure_line.split('[')
        the_variable = structure_list[0]
        #
        if the_variable in all_vars:
            set_list = structure_list[1].replace(']','').replace('\n','').split(',')
            #--%
            index = S_DICT_vars_structure['variable'].index( the_variable )
            this_variable_indices = S_DICT_vars_structure['index_list'][ index ]
            #
            # if ('y' in this_variable_indices) and ( ('2015' in set_list) or ('2019' in set_list) or ('2025' in set_list) or ('2030' in set_list) or ('2035' in set_list) or ('2040' in set_list) or ('2045' in set_list) or ('2050' in set_list) ):
            #--%
            if 'y' in this_variable_indices:
                data_line = linecache.getline(data_name, n+1)
                data_line_list_raw = data_line.split(' ')
                data_line_list = [ data_cell for data_cell in data_line_list_raw if data_cell != '' ]
                useful_data_cell = data_line_list[1]
                #--%
                if useful_data_cell != '0':
                    #
                    if the_variable not in vars_as_appear:
                        vars_as_appear.append( the_variable )
                        all_vars_output_dict[case].update({ the_variable:{} })
                        all_vars_output_dict[case][the_variable].update({ the_variable:[] })
                        #
                        for n in range( len( this_variable_indices ) ):
                            all_vars_output_dict[case][the_variable].update( { this_variable_indices[n]:[] } )
                    #--%
                    this_variable = vars_as_appear[-1]
                    all_vars_output_dict[case][this_variable][this_variable].append( useful_data_cell )
                    for n in range( len( this_variable_indices ) ):
                        all_vars_output_dict[case][the_variable][ this_variable_indices[n] ].append( set_list[n] )
                #
            #
            elif 'y' not in this_variable_indices:
                data_line = linecache.getline(data_name, n+1)
                data_line_list_raw = data_line.split(' ')
                data_line_list = [ data_cell for data_cell in data_line_list_raw if data_cell != '' ]
                useful_data_cell = data_line_list[1]
                #--%
                if useful_data_cell != '0':
                    #
                    if the_variable not in vars_as_appear:
                        vars_as_appear.append( the_variable )
                        all_vars_output_dict[case].update({ the_variable:{} })
                        all_vars_output_dict[case][the_variable].update({ the_variable:[] })
                        #
                        for n in range( len( this_variable_indices ) ):
                            all_vars_output_dict[case][the_variable].update( { this_variable_indices[n]:[] } )
                    #--%
                    this_variable = vars_as_appear[-1]
                    all_vars_output_dict[case][this_variable][this_variable].append( useful_data_cell )
                    for n in range( len( this_variable_indices ) ):
                        all_vars_output_dict[case][the_variable][ this_variable_indices[n] ].append( set_list[n] )
        #--%
        else:
            pass
    #
    linecache.clearcache()
    #%%
    #-----------------------------------------------------------------------------------------------------------%
    # Extract *AccumulatedNewCapacity* for every vehicle technology:
    this_var_out1 = 'AccumulatedNewCapacity'
    this_var_dict_out1 = all_vars_output_dict[case]['AccumulatedNewCapacity']
    this_var_techs = this_var_dict_out1['t']
    this_var_techs_unique = list( Fleet_Groups_inv.keys() )  # transport techs only
    this_var_years = this_var_dict_out1['y']
    this_var_years_unique = list(set(this_var_dict_out1['y']))
    this_var_years_unique.sort()
    aide_dict_accumnewcap = {}
    for t_aid in this_var_techs_unique:
        aide_dict_accumnewcap.update({t_aid:[]})
        for y_aid in this_var_years_unique:
            tech_indices = \
                [i for i, x in enumerate(this_var_techs) if (t_aid in x )]
            year_indices = \
                [i for i, x in enumerate(this_var_years) if (y_aid in x )]
            position_idx_list = \
                list(set(tech_indices) & set(year_indices))
            if len(position_idx_list) != 0:
                position_idx = position_idx_list[0]
                this_value = float(this_var_dict_out1[this_var_out1][position_idx])
            elif len(position_idx_list) == 0:
                this_value = 0
            else:
                print('*This is an error (out 1)*')
                sys.exit()
            aide_dict_accumnewcap[t_aid].append(this_value)

    # Extract *CapitalInvestment* for every vehicle technology: // gotta divide by *NewCapacity* below:
    this_var_out2 = 'CapitalInvestment'
    this_var_dict_out2 = all_vars_output_dict[case]['CapitalInvestment']
    this_var_techs = this_var_dict_out2['t']
    this_var_techs_unique = list( Fleet_Groups_inv.keys() )  # transport techs only
    this_var_years = this_var_dict_out2['y']
    this_var_years_unique = list(set(this_var_dict_out2['y']))
    this_var_years_unique.sort()
    aide_dict_capitalcost = {}
    for t_aid in this_var_techs_unique:
        aide_dict_capitalcost.update({t_aid:[]})
        for y_aid in this_var_years_unique:
            tech_indices = \
                [i for i, x in enumerate(this_var_techs) if (t_aid in x )]
            year_indices = \
                [i for i, x in enumerate(this_var_years) if (y_aid in x )]
            position_idx_list = \
                list(set(tech_indices) & set(year_indices))
            if len(position_idx_list) != 0:
                position_idx = position_idx_list[0]
                this_value = float(this_var_dict_out2[this_var_out2][position_idx])
            elif len(position_idx_list) == 0:
                this_value = 0
            else:
                print('*This is an error (out 2)*')
                sys.exit()
            aide_dict_capitalcost[t_aid].append(this_value)

    # Extract *NewCapacity* for every vehicle technology:
    this_var_out3 = 'NewCapacity'
    this_var_dict_out3 = all_vars_output_dict[case]['NewCapacity']
    this_var_techs = this_var_dict_out3['t']
    this_var_techs_unique = list( Fleet_Groups_inv.keys() )  # transport techs only
    this_var_years = this_var_dict_out3['y']
    this_var_years_unique = list(set(this_var_dict_out3['y']))
    this_var_years_unique.sort()
    aide_dict_newcap = {}
    for t_aid in this_var_techs_unique:
        aide_dict_newcap.update({t_aid:[]})
        for y_aid in this_var_years_unique:
            tech_indices = \
                [i for i, x in enumerate(this_var_techs) if (t_aid in x )]
            year_indices = \
                [i for i, x in enumerate(this_var_years) if (y_aid in x )]
            position_idx_list = \
                list(set(tech_indices) & set(year_indices))
            if len(position_idx_list) != 0:
                position_idx = position_idx_list[0]
                this_value = float(this_var_dict_out3[this_var_out3][position_idx])
            elif len(position_idx_list) == 0:
                this_value = 0
            else:
                print('*This is an error (out 3)*')
                sys.exit()
            aide_dict_newcap[t_aid].append(this_value)

    # Extract *TotalCapacityAnnual* for every vehicle technology:
    this_var_out4 = 'TotalCapacityAnnual'
    this_var_dict_out4 = all_vars_output_dict[case]['TotalCapacityAnnual']
    this_var_techs = this_var_dict_out4['t']
    this_var_techs_unique = list( Fleet_Groups_inv.keys() )  # transport techs only
    this_var_years = this_var_dict_out4['y']
    this_var_years_unique = list(set(this_var_dict_out4['y']))
    this_var_years_unique.sort()
    aide_dict_totalcap = {}
    for t_aid in this_var_techs_unique:
        aide_dict_totalcap.update({t_aid:[]})
        for y_aid in this_var_years_unique:
            tech_indices = \
                [i for i, x in enumerate(this_var_techs) if (t_aid in x )]
            year_indices = \
                [i for i, x in enumerate(this_var_years) if (y_aid in x )]
            position_idx_list = \
                list(set(tech_indices) & set(year_indices))
            if len(position_idx_list) != 0:
                position_idx = position_idx_list[0]
                this_value = float(this_var_dict_out4[this_var_out4][position_idx])
            elif len(position_idx_list) == 0:
                this_value = 0
            else:
                print('*This is an error (out 4)*')
                sys.exit()
            aide_dict_totalcap[t_aid].append(this_value)

    #-----------------------------------------------------------------------------------------------------------%
    output_adress = './Executables/' + str( first_list[case] )
    combination_list = [] # [fuel, technology, emission, year]
    data_row_list = []
    for var in range( len( vars_as_appear ) ):
        this_variable = vars_as_appear[var]
        this_var_dict = all_vars_output_dict[case][this_variable]
        #--%
        index = S_DICT_vars_structure['variable'].index( this_variable )
        this_variable_indices = S_DICT_vars_structure['index_list'][ index ]
        #--------------------------------------#
        for k in range( len( this_var_dict[this_variable] ) ):
            this_combination = []
            #
            if 'f' in this_variable_indices:
                this_combination.append( this_var_dict['f'][k] )
            else:
                this_combination.append( '' )
            #
            if 't' in this_variable_indices:
                this_combination.append( this_var_dict['t'][k] )
            else:
                this_combination.append( '' )
            #
            if 'e' in this_variable_indices:
                this_combination.append( this_var_dict['e'][k] )
            else:
                this_combination.append( '' )
            #
            if 'l' in this_variable_indices:
                this_combination.append( '' )
            else:
                this_combination.append( '' )
            #
            if 'y' in this_variable_indices:
                this_combination.append( this_var_dict['y'][k] )
            else:
                this_combination.append( '' )
            #
            if this_combination not in combination_list:
                combination_list.append( this_combination )
                data_row = ['' for n in range( len( output_header ) ) ]
                # print('check', len(data_row), len(run_id) )
                data_row[0] = this_strategy
                data_row[1] = this_future
                data_row[2] = this_combination[0] # Fuel
                data_row[3] = this_combination[1] # Technology
                data_row[4] = this_combination[2] # Emission
                # data_row[7] = this_combination[3]
                data_row[5] = this_combination[4] # Year
                #
                var_position_index = output_header.index( this_variable )
                data_row[ var_position_index ] = this_var_dict[ this_variable ][ k ]
                data_row_list.append( data_row )
            else:
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] )
                #
                var_position_index = output_header.index( this_variable )
                #
                if 'l' in this_variable_indices: 
                    #
                    if str(this_data_row[ var_position_index ]) != '' and str(this_var_dict[ this_variable ][ k ]) != '' and ( 'Rate' not in this_variable ):
                        this_data_row[ var_position_index ] = str(  float( this_data_row[ var_position_index ] ) + float( this_var_dict[ this_variable ][ k ] ) )
                    elif str(this_data_row[ var_position_index ]) == '' and str(this_var_dict[ this_variable ][ k ]) != '':
                        this_data_row[ var_position_index ] = str( float( this_var_dict[ this_variable ][ k ] ) )
                    elif str(this_data_row[ var_position_index ]) != '' and str(this_var_dict[ this_variable ][ k ]) == '':
                        pass
                else:
                    this_data_row[ var_position_index ] = this_var_dict[ this_variable ][ k ]
                #
                data_row_list[ ref_index ]  = deepcopy( this_data_row )
                #
            #
            if this_variable == 'TotalCapacityAnnual' or this_variable == 'NewCapacity':
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                this_tech = this_combination[1]
                if this_tech in list( Fleet_Groups_inv.keys() ):
                    group_tech = Fleet_Groups_inv[ this_tech ]
                    #
                    this_year = this_combination[4]
                    this_year_index = time_range_vector.index( int( this_year ) )
                    #
                    ref_var_position_index = output_header.index( this_variable )
                    #
                    if 'Trains' not in group_tech:
                        driven_distance = float(Reference_driven_distance[this_strategy][group_tech][this_year_index])
                        driven_distance_2024 = \
                            float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2024)])
                        driven_distance_final = \
                            float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2050)])
                        passenger_per_vehicle = float(Reference_occupancy_rate[this_strategy][group_tech][this_year_index])
                        #
                        if this_variable == 'NewCapacity':
                            var_position_index = output_header.index( 'NewFleet' )
                            new_cap_calculated = \
                                float(this_data_row[ref_var_position_index])
                            new_fleet_calculated = \
                                (10**9)*new_cap_calculated/driven_distance

                            accum_new_cap_subtract = 0
                            driven_distance_prev = float(Reference_driven_distance[this_strategy][group_tech][this_year_index-1])
                            if int(this_year) >= 2024 and driven_distance_2024 != driven_distance_final:
                                # We need to select the appropiate accumulated new capacity:
                                accum_new_cap = \
                                    aide_dict_accumnewcap[this_tech][this_year_index-1]

                                if int(this_year) > 2018+Reference_op_life[this_strategy][this_tech]:  # works with a timeframe by 2050; longer timeframes may need more lifetime cycle adjustments
                                    subtract_index_accum_old = \
                                        int(Reference_op_life[this_strategy][this_tech])
                                    if int(this_year) - subtract_index_accum_old <= 2024:
                                        driven_distance_17 = \
                                            float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2019)])
                                    else:
                                        driven_distance_17 = \
                                            float(Reference_driven_distance[this_strategy][group_tech][this_year_index-subtract_index_accum_old])

                                    adjust_factor_old_cap = \
                                        (1-driven_distance/driven_distance_17)

                                    if int(this_year) - subtract_index_accum_old > 2024:  # this is an odd rule, but works empirically
                                        driven_distance_2024 = \
                                            float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2024)])
                                        driven_distance_minus3 = \
                                            float(Reference_driven_distance[this_strategy][group_tech][this_year_index-3])
                                        adjust_factor_old_cap -= \
                                            (1-driven_distance_17/driven_distance_2024)
                                        adjust_factor_old_cap -= \
                                            (1-driven_distance/driven_distance_minus3)

                                    accum_new_cap_subtract += \
                                        aide_dict_newcap[this_tech][this_year_index-subtract_index_accum_old]*adjust_factor_old_cap

                                new_cap_adj = \
                                    accum_new_cap*(1-driven_distance/driven_distance_prev) - accum_new_cap_subtract
                            else:
                                new_cap_adj = 0
                            new_fleet_adj = \
                                (10**9)*new_cap_adj/driven_distance
                            this_data_row[ var_position_index ] = \
                                round(new_fleet_calculated + new_fleet_adj, 4)
                        #
                        if this_variable == 'TotalCapacityAnnual':
                            #
                            var_position_index = output_header.index( 'Fleet' )
                            this_data_row[ var_position_index ] =  round( (10**9)*float( this_data_row[ ref_var_position_index ] )/driven_distance, 4)
                            #
                            var_position_index = output_header.index( 'DistanceDriven' )
                            this_data_row[ var_position_index ] = round(driven_distance, 4)
                            #
                            var_position_index = output_header.index( 'ProducedMobility' )
                            this_data_row[ var_position_index ] =  round( float( this_data_row[ ref_var_position_index ] )*passenger_per_vehicle, 4)
                        #
                        data_row_list[ ref_index ] = deepcopy( this_data_row )
                        #
                    #
                    ###################################################################################################
                    #
                #
            #
            # Creating convinience filters for the analysis of model outputs:
            this_tech = this_combination[1]
            if this_tech in list( Fleet_Groups_inv.keys() ):
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                var_position_index = output_header.index( 'FilterFuelType' )
                ############################################
                # By Fuel Type
                for r in range( len( df_fuel_2_code_fuel_list ) ):
                    if df_fuel_2_code_fuel_list[r] in this_tech:
                        this_data_row[ var_position_index ] = df_fuel_2_code_plain_english[ r ]
                        break
                ############################################
                var_position_index = output_header.index( 'FilterVehicleType' )
                # By vehicle type
                for r in range( len( df_tech_2_code_fuel_list ) ):
                    if df_tech_2_code_fuel_list[r] in this_tech:
                        this_data_row[ var_position_index ] = df_tech_2_code_plain_english[ r ]
                        break
                data_row_list[ ref_index ] = deepcopy( this_data_row )
            #
            output_csv_r = dr_default*100
            output_csv_year = 2021
            #
            if this_combination[2] in ['Accidents', 'Health', 'Congestion'] and this_variable == 'AnnualTechnologyEmissionPenaltyByEmission':
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                ref_var_position_index = output_header.index( 'AnnualTechnologyEmissionPenaltyByEmission' )
                new_var_position_index = output_header.index( 'Externalities2021' )
                new2_var_position_index = output_header.index( 'Externalities_GDP' )
                #
                this_year = this_combination[4]
                this_year_index = time_range_vector.index( int( this_year ) )
                #
                resulting_value_raw = float(this_data_row[ ref_var_position_index ]) / ( ( 1 + output_csv_r/100 )**( float(this_year) - output_csv_year ) )
                resulting_value = round( resulting_value_raw, 4)
                #
                this_data_row[new_var_position_index] = str( resulting_value )
                this_data_row[new2_var_position_index] = str( float(this_data_row[ ref_var_position_index ])/list_gdp_ref[this_year_index] )
                #
                data_row_list[ ref_index ] = deepcopy( this_data_row )
                #
            #
            ''' $ This is new (beginning) $ '''
            #
            if this_variable == 'CapitalInvestment':
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                ref_var_position_index = output_header.index( 'CapitalInvestment' )
                new_var_position_index = output_header.index( 'Capex2021' )
                new2_var_position_index = output_header.index( 'Capex_GDP' )
                #
                this_year = this_combination[4]
                this_year_index = time_range_vector.index( int( this_year ) )
                #
                # Here we must add an adjustment to the capital investment to make the fleet constant:
                this_base_cap_inv = \
                    float(this_data_row[ ref_var_position_index ])
                this_plus_cap_inv = 0
                '''
                > We need to add new capital costs if the technology is in transport:
                '''
                if this_tech in list(Fleet_Groups_inv.keys()):
                    group_tech = Fleet_Groups_inv[this_tech]
                    if 'Trains' not in group_tech:
                        driven_distance = float(Reference_driven_distance[this_strategy][group_tech][this_year_index])
                        driven_distance_2024 = \
                            float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2024)])
                        driven_distance_final = \
                            float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2050)])

                        accum_new_cap_subtract = 0
                        driven_distance_prev = float(Reference_driven_distance[this_strategy][group_tech][this_year_index-1])
                        if int(this_year) >= 2024 and driven_distance_2024 != driven_distance_final:  # greater than the base year
                            # We need to select the appropiate accumulated new capacity:
                            accum_new_cap = \
                                aide_dict_accumnewcap[this_tech][this_year_index-1]

                            if int(this_year) > 2018+Reference_op_life[this_strategy][this_tech]:
                                subtract_index_accum_old = \
                                    int(Reference_op_life[this_strategy][this_tech])
                                if int(this_year) - subtract_index_accum_old <= 2024:
                                    driven_distance_17 = \
                                        float(Reference_driven_distance[this_strategy][group_tech][time_range_vector.index(2019)])
                                else:
                                    driven_distance_17 = \
                                        float(Reference_driven_distance[this_strategy][group_tech][this_year_index-subtract_index_accum_old])

                                adjust_factor_old_cap = \
                                    (1-driven_distance/driven_distance_17)

                                if int(this_year) - subtract_index_accum_old > 2024:  # this is an odd rule, but works empirically
                                    driven_distance_minus3 = \
                                        float(Reference_driven_distance[this_strategy][group_tech][this_year_index-3])
                                    adjust_factor_old_cap -= \
                                        (1-driven_distance_17/driven_distance_2024)
                                    adjust_factor_old_cap -= \
                                        (1-driven_distance/driven_distance_minus3)

                                accum_new_cap_subtract += \
                                    aide_dict_newcap[this_tech][this_year_index-subtract_index_accum_old]*adjust_factor_old_cap

                            new_cap_adj = \
                                accum_new_cap*(1-driven_distance/driven_distance_prev) - accum_new_cap_subtract
                            this_cap_cost = \
                                aide_dict_capitalcost[this_tech][this_year_index]
                            this_new_cap = \
                                aide_dict_newcap[this_tech][this_year_index]
                            this_plus_cap_inv += \
                                new_cap_adj*this_cap_cost/this_new_cap

                this_cap_inv = this_base_cap_inv + this_plus_cap_inv
                this_data_row[ref_var_position_index] = \
                    str(this_cap_inv)  # Here we re-write the new capacity to adjust the system
                '''
                > Below we continue as usual:
                '''
                resulting_value_raw = this_cap_inv/((1 + output_csv_r/100)**(float(this_year) - output_csv_year))
                resulting_value = round( resulting_value_raw, 4)
                #
                this_data_row[new_var_position_index] = str( resulting_value )
                this_data_row[new2_var_position_index] = str( float(this_data_row[ ref_var_position_index ])/list_gdp_ref[this_year_index] )
                #
                data_row_list[ ref_index ] = deepcopy( this_data_row )
                #
            #
            if this_variable == 'AnnualFixedOperatingCost':
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                ref_var_position_index = output_header.index( 'AnnualFixedOperatingCost' )
                new_var_position_index = output_header.index( 'FixedOpex2021' )
                new2_var_position_index = output_header.index( 'FixedOpex_GDP' )
                #
                this_year = this_combination[4]
                this_year_index = time_range_vector.index( int( this_year ) )
                #
                resulting_value_raw = float(this_data_row[ ref_var_position_index ]) / ( ( 1 + output_csv_r/100 )**( float(this_year) - output_csv_year ) )
                resulting_value = round( resulting_value_raw, 4)
                #
                this_data_row[new_var_position_index] = str( resulting_value )
                this_data_row[new2_var_position_index] = str( float(this_data_row[ ref_var_position_index ])/list_gdp_ref[this_year_index] )
                #
                data_row_list[ ref_index ] = deepcopy( this_data_row )
                #
            #
            if this_variable == 'AnnualVariableOperatingCost':
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                ref_var_position_index = output_header.index( 'AnnualVariableOperatingCost' )
                new_var_position_index = output_header.index( 'VarOpex2021' )
                new2_var_position_index = output_header.index( 'VarOpex_GDP' )
                #
                this_year = this_combination[4]
                this_year_index = time_range_vector.index( int( this_year ) )
                #
                resulting_value_raw = float(this_data_row[ ref_var_position_index ]) / ( ( 1 + output_csv_r/100 )**( float(this_year) - output_csv_year ) )
                resulting_value = round( resulting_value_raw, 4)
                #
                this_data_row[new_var_position_index] = str( resulting_value )
                this_data_row[new2_var_position_index] = str( float(this_data_row[ ref_var_position_index ])/list_gdp_ref[this_year_index] )
                #
                data_row_list[ ref_index ] = deepcopy( this_data_row )
                #
            #
            if this_variable == 'OperatingCost':
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( data_row_list[ ref_index ] ) # this must be updated in a further position of the list
                #
                ref_var_position_index = output_header.index( 'OperatingCost' )
                new_var_position_index = output_header.index( 'Opex2021' )
                new2_var_position_index = output_header.index( 'Opex_GDP' )
                #
                this_year = this_combination[4]
                this_year_index = time_range_vector.index( int( this_year ) )
                #
                resulting_value_raw = float(this_data_row[ ref_var_position_index ]) / ( ( 1 + output_csv_r/100 )**( float(this_year) - output_csv_year ) )
                resulting_value = round( resulting_value_raw, 4)
                #
                this_data_row[new_var_position_index] = str( resulting_value )
                this_data_row[new2_var_position_index] = str( float(this_data_row[ ref_var_position_index ])/list_gdp_ref[this_year_index] )
                #
                data_row_list[ ref_index ] = deepcopy( this_data_row )
                #
            #
            ''' $ (end) $ '''
            #
        #
    #
    non_year_combination_list = []
    non_year_combination_list_years = []
    for n in range( len( combination_list ) ):
        this_combination = combination_list[ n ]
        this_non_year_combination = [ this_combination[0], this_combination[1], this_combination[2] ]
        if this_combination[4] != '' and this_non_year_combination not in non_year_combination_list:
            non_year_combination_list.append( this_non_year_combination )
            non_year_combination_list_years.append( [ this_combination[4] ] )
        elif this_combination[4] != '' and this_non_year_combination in non_year_combination_list:
            non_year_combination_list_years[ non_year_combination_list.index( this_non_year_combination ) ].append( this_combination[4] )
    #
    for n in range( len( non_year_combination_list ) ):
        if len( non_year_combination_list_years[n] ) != len(time_range_vector):
            #
            this_existing_combination = non_year_combination_list[n]
            # print('flag 1', this_existing_combination )
            this_existing_combination.append( '' )
            # print('flag 2', this_existing_combination )
            this_existing_combination.append( non_year_combination_list_years[n][0] )
            # print('flag 3', this_existing_combination )
            ref_index = combination_list.index( this_existing_combination )
            this_existing_data_row = deepcopy( data_row_list[ ref_index ] )
            #
            for n2 in range( len( time_range_vector ) ):
                #
                if time_range_vector[n2] not in non_year_combination_list_years[n]:
                    #
                    data_row = ['' for n in range( len( output_header ) ) ]
                    data_row[0] = this_strategy
                    data_row[1] = this_future
                    data_row[2] = non_year_combination_list[n][0]
                    data_row[3] = non_year_combination_list[n][1]
                    data_row[4] = non_year_combination_list[n][2]
                    data_row[5] = time_range_vector[n2]
                    #
                    for n3 in range( len( vars_as_appear ) ):
                        this_variable = vars_as_appear[n3]
                        this_var_dict = all_vars_output_dict[case][this_variable]
                        index = S_DICT_vars_structure['variable'].index( this_variable )
                        this_variable_indices = S_DICT_vars_structure['index_list'][ index ]
                        #
                        var_position_index = output_header.index( this_variable )
                        #
                        print_true = False
                        if ( 'f' in this_variable_indices and str(non_year_combination_list[n][0]) != '' ): # or ( 'f' not in this_variable_indices and str(non_year_combination_list[n][0]) == '' ):
                            print_true = True
                        else:
                            pass
                        #
                        if ( 't' in this_variable_indices and str(non_year_combination_list[n][1]) != '' ): # or ( 't' not in this_variable_indices and str(non_year_combination_list[n][1]) == '' ):
                            print_true = True
                        else:
                            pass
                        #
                        if ( 'e' in this_variable_indices and str(non_year_combination_list[n][2]) != '' ): # or ( 'e' not in this_variable_indices and str(non_year_combination_list[n][2]) == '' ):
                            print_true = True
                        else:
                            pass
                        #
                        if 'y' in this_variable_indices and ( str( this_existing_data_row[ var_position_index ] ) != '' ) and print_true == True:
                            data_row[ var_position_index ] = '0'
                            #
                        else:
                            pass
                    #
                    data_row_list.append( data_row )
    #--------------------------------------#
    with open( output_adress + '/' + str( first_list[case] ) + '_Output' + '.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow( output_header )
        for n in range( len( data_row_list ) ):
            csvwriter.writerow( data_row_list[n] )
    #-----------------------------------------------------------------------------------------------------------%
    shutil.os.remove(data_name) #-----------------------------------------------------------------------------------------------------------%
    gc.collect(generation=2)
    time.sleep(0.05)
    #-----------------------------------------------------------------------------------------------------------%
    print(  'We finished with printing the outputs: ' + str( first_list[case] ) )
#
def function_C_mathprog( scen, stable_scenarios, unpackaged_useful_elements ):
    #
    scenario_list =                     unpackaged_useful_elements[0]
    S_DICT_sets_structure =             unpackaged_useful_elements[1]
    S_DICT_params_structure =           unpackaged_useful_elements[2]
    list_param_default_value_params =   unpackaged_useful_elements[3]
    list_param_default_value_value =    unpackaged_useful_elements[4]
    print_adress =                      unpackaged_useful_elements[5]

    # Extract the default (national) discount rate parameter
    dr_prm_idx = list_param_default_value_params.index('DiscountRate')
    dr_default = list_param_default_value_value[dr_prm_idx]

    Reference_driven_distance =         unpackaged_useful_elements[6]
    Fleet_Groups_inv =                  unpackaged_useful_elements[7]
    time_range_vector =                 unpackaged_useful_elements[8]
    Blend_Shares =                      unpackaged_useful_elements[9]
    #
    # Briefly open up the system coding to use when processing for visualization:
    df_fuel_to_code = pd.read_excel( './A1_Inputs/A-I_Classifier_Modes_Transport.xlsx', sheet_name='Fuel_to_Code' )
    df_fuel_2_code_fuel_list        = df_fuel_to_code['Code'].tolist()
    df_fuel_2_code_plain_english    = df_fuel_to_code['Plain_English'].tolist()
    df_tech_to_code = pd.read_excel( './A1_Inputs/A-I_Classifier_Modes_Transport.xlsx', sheet_name='Tech_to_Code' )
    df_tech_2_code_fuel_list        = df_tech_to_code['Techs'].tolist()
    df_tech_2_code_plain_english    = df_tech_to_code['Plain_English'].tolist()
    #
    # header = ['Scenario','Parameter','REGION','TECHNOLOGY','FUEL','EMISSION','MODE_OF_OPERATION','TIMESLICE','YEAR','SEASON','DAYTYPE','DAILYTIMEBRACKET','STORAGE','Value']
    header_indices = ['Scenario','Parameter','r','t','f','e','m','l','y','ls','ld','lh','s','value']
    #
    # for scen in range( len( scenario_list ) ):
    print('# This is scenario ', scenario_list[scen] )
    #
    try:
        scen_file_dir = print_adress + '/' + str( scenario_list[scen] ) + '_0'
        os.mkdir( scen_file_dir )
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
    this_scenario_data = stable_scenarios[ scenario_list[scen] ]
    #
    g= open( print_adress + '/' + str( scenario_list[scen] ) + '_0' + '/' + str( scenario_list[scen] ) + '_0' + '.txt',"w+")
    g.write( '###############\n#    Sets     #\n###############\n#\n' )
    g.write( 'set DAILYTIMEBRACKET :=  ;\n' )
    g.write( 'set DAYTYPE :=  ;\n' )
    g.write( 'set SEASON :=  ;\n' )
    g.write( 'set STORAGE :=  ;\n' )
    #
    for n1 in range( len( S_DICT_sets_structure['set'] ) ):
        if S_DICT_sets_structure['number_of_elements'][n1] != 0:
            g.write( 'set ' + S_DICT_sets_structure['set'][n1] + ' := ' )
            #
            for n2 in range( S_DICT_sets_structure['number_of_elements'][n1] ):
                if S_DICT_sets_structure['set'][n1] == 'YEAR' or S_DICT_sets_structure['set'][n1] == 'MODE_OF_OPERATION':
                    g.write( str( int( S_DICT_sets_structure['elements_list'][n1][n2] ) ) + ' ' )
                else:
                    g.write( str( S_DICT_sets_structure['elements_list'][n1][n2] ) + ' ' )
            g.write( ';\n' )
    #
    g.write( '\n' )
    g.write( '###############\n#    Parameters     #\n###############\n#\n' )
    #
    for p in range( len( list( this_scenario_data.keys() ) ) ):
        #
        this_param = list( this_scenario_data.keys() )[p]
        #
        default_value_list_params_index = list_param_default_value_params.index( this_param )
        default_value = float( list_param_default_value_value[ default_value_list_params_index ] )
        if default_value >= 0:
            default_value = int( default_value )
        else:
            pass
        #
        this_param_index = S_DICT_params_structure['parameter'].index( this_param )
        this_param_keys = S_DICT_params_structure['index_list'][this_param_index]
        #
        if len( this_scenario_data[ this_param ]['value'] ) != 0:
            #
#            f.write( 'param ' + this_param + ':=\n' )
            if len(this_param_keys) != 2:
                g.write( 'param ' + this_param + ' default ' + str( default_value ) + ' :=\n' )
            else:
                g.write( 'param ' + this_param + ' default ' + str( default_value ) + ' :\n' )
            #
            #-----------------------------------------#
            if len(this_param_keys) == 2: #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                # get the last and second last parameters of the list:
                last_set_element = this_scenario_data[ this_param ][ this_param_keys[-1] ] # header_indices.index( this_param_keys[-1] ) ]
                last_set_element_unique = [] # list( set( last_set_element ) )
                for u in range( len( last_set_element ) ):
                    if last_set_element[u] not in last_set_element_unique:
                        last_set_element_unique.append( last_set_element[u] )
                #
                for y in range( len( last_set_element_unique ) ):
                    g.write( str( last_set_element_unique[y] ) + ' ')
                g.write(':=\n')
                #
                second_last_set_element = this_scenario_data[ this_param ][ this_param_keys[-2] ] # header_indices.index( this_param_keys[-2] ) ]
                second_last_set_element_unique = [] # list( set( second_last_set_element ) )
                for u in range( len( second_last_set_element ) ):
                    if second_last_set_element[u] not in second_last_set_element_unique:
                        second_last_set_element_unique.append( second_last_set_element[u] )
                #
                for s in range( len( second_last_set_element_unique ) ):
                    g.write( second_last_set_element_unique[s] + ' ' )
                    value_indices = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[-2] ] ) if x == str( second_last_set_element_unique[s] ) ]
                    these_values = []
                    for val in range( len( value_indices ) ):
                        these_values.append( this_scenario_data[ this_param ]['value'][ value_indices[val] ] )
                    for val in range( len( these_values ) ):
                        g.write( str( these_values[val] ) + ' ' )
                    g.write('\n') #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            #%%%
            if len(this_param_keys) == 3:
                this_set_element_unique_all = []
                for pkey in range( len(this_param_keys)-2 ):
                    for i in range( 2, len(header_indices)-1 ):
                        if header_indices[i] == this_param_keys[pkey]:
                            this_set_element = this_scenario_data[ this_param ][ header_indices[i] ]
                    this_set_element_unique_all.append( list( set( this_set_element ) ) )
                #
                this_set_element_unique_1 = deepcopy( this_set_element_unique_all[0] )
                #
                for n1 in range( len( this_set_element_unique_1 ) ): #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                    g.write( '[' + str( this_set_element_unique_1[n1] ) + ',*,*]:\n' )
                    # get the last and second last parameters of the list:
                    last_set_element = this_scenario_data[ this_param ][ this_param_keys[-1] ] # header_indices.index( this_param_keys[-1] ) ]
                    last_set_element_unique = [] # list( set( last_set_element ) )
                    for u in range( len( last_set_element ) ):
                        if last_set_element[u] not in last_set_element_unique:
                            last_set_element_unique.append( last_set_element[u] )
                    #
                    for y in range( len( last_set_element_unique ) ):
                        g.write( str( last_set_element_unique[y] ) + ' ')
                    g.write(':=\n')
                    #
                    second_last_set_element = this_scenario_data[ this_param ][ this_param_keys[-2] ] #header_indices.index( this_param_keys[-2] ) ]
                    second_last_set_element_unique = [] # list( set( second_last_set_element ) )
                    for u in range( len( second_last_set_element ) ):
                        if second_last_set_element[u] not in second_last_set_element_unique:
                            second_last_set_element_unique.append( second_last_set_element[u] )
                    #
                    for s in range( len( second_last_set_element_unique ) ):
                        g.write( second_last_set_element_unique[s] + ' ' )
                        #
                        value_indices_s = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[-2] ] ) if x == str( second_last_set_element_unique[s] ) ]
                        value_indices_n1 = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[0] ] ) if x == str( this_set_element_unique_1[n1] ) ]
                        #
                        r_index = set(value_indices_s) & set(value_indices_n1)
                        #
                        value_indices = list( r_index )
                        value_indices.sort()
                        #
                        these_values = []
                        for val in range( len( value_indices ) ):
                            try:
                                these_values.append( this_scenario_data[ this_param ]['value'][ value_indices[val] ] )
                            except:
                                print( this_param, val )
                        for val in range( len( these_values ) ):
                            g.write( str( these_values[val] ) + ' ' )
                        g.write('\n') #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            #%%%
            if len(this_param_keys) == 4:
                this_set_element_unique_all = []
                for pkey in range( len(this_param_keys)-2 ):
                    for i in range( 2, len(header_indices)-1 ):
                        if header_indices[i] == this_param_keys[pkey]:
                            this_set_element = this_scenario_data[ this_param ][ header_indices[i] ]
                            this_set_element_unique_all.append( list( set( this_set_element ) ) )
                #
                this_set_element_unique_1 = deepcopy( this_set_element_unique_all[0] )
                this_set_element_unique_2 = deepcopy( this_set_element_unique_all[1] )
                #
                for n1 in range( len( this_set_element_unique_1 ) ):
                    for n2 in range( len( this_set_element_unique_2 ) ): #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                        g.write( '[' + str( this_set_element_unique_1[n1] ) + ',' + str( this_set_element_unique_2[n2] ) + ',*,*]:\n' )
                        # get the last and second last parameters of the list:
                        last_set_element = this_scenario_data[ this_param ][ this_param_keys[-1] ] # header_indices.index( this_param_keys[-1] ) ]
                        last_set_element_unique = [] # list( set( last_set_element ) )
                        for u in range( len( last_set_element ) ):
                            if last_set_element[u] not in last_set_element_unique:
                                last_set_element_unique.append( last_set_element[u] )
                        #
                        for y in range( len( last_set_element_unique ) ):
                            g.write( str( last_set_element_unique[y] ) + ' ')
                        g.write(':=\n')
                        #
                        second_last_set_element = this_scenario_data[ this_param ][ this_param_keys[-2] ] # header_indices.index( this_param_keys[-2] ) ]
                        second_last_set_element_unique = [] # list( set( second_last_set_element ) )
                        for u in range( len( second_last_set_element ) ):
                            if second_last_set_element[u] not in second_last_set_element_unique:
                                second_last_set_element_unique.append( second_last_set_element[u] )
                        #
                        for s in range( len( second_last_set_element_unique ) ):
                            g.write( second_last_set_element_unique[s] + ' ' )
                            #
                            value_indices_s = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[-2] ] ) if x == str( second_last_set_element_unique[s] ) ]
                            value_indices_n1 = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[0] ] ) if x == str( this_set_element_unique_1[n1] ) ]
                            value_indices_n2 = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[1] ] ) if x == str( this_set_element_unique_2[n2] ) ]
                            r_index = set(value_indices_s) & set(value_indices_n1) & set(value_indices_n2)
                            value_indices = list( r_index )
                            value_indices.sort()
                            #
                            # these_values = this_scenario_data[ this_param ]['value'][ value_indices[0]:value_indices[-1]+1 ]
                            these_values = []
                            for val in range( len( value_indices ) ):
                                these_values.append( this_scenario_data[ this_param ]['value'][ value_indices[val] ] )
                            for val in range( len( these_values ) ):
                                g.write( str( these_values[val] ) + ' ' )
                            g.write('\n') #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            #%%%
            if len(this_param_keys) == 5:
                this_set_element_unique_all = []
                for pkey in range( len(this_param_keys)-2 ):
                    for i in range( 2, len(header_indices)-1 ):
                        if header_indices[i] == this_param_keys[pkey]:
                            this_set_element = this_scenario_data[ this_param ][ header_indices[i] ]
                            this_set_element_unique_all.append( list( set( this_set_element ) ) )
                #
                this_set_element_unique_1 = deepcopy( this_set_element_unique_all[0] )
                this_set_element_unique_2 = deepcopy( this_set_element_unique_all[1] )
                this_set_element_unique_3 = deepcopy( this_set_element_unique_all[2] )
                #
                for n1 in range( len( this_set_element_unique_1 ) ):
                    for n2 in range( len( this_set_element_unique_2 ) ):
                        for n3 in range( len( this_set_element_unique_3 ) ): #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                            # MOVE AFTER len() conditional // g.write( '[' + str( this_set_element_unique_1[n1] ) + ',' + str( this_set_element_unique_2[n2] ) + ',' + str( this_set_element_unique_3[n3] ) + ',*,*]:\n' )
                            # get the last and second last parameters of the list:
                            last_set_element = this_scenario_data[ this_param ][ this_param_keys[-1] ]
                            last_set_element_unique = [] # list( set( last_set_element ) )
                            for u in range( len( last_set_element ) ):
                                if last_set_element[u] not in last_set_element_unique:
                                    last_set_element_unique.append( last_set_element[u] )
                            #
                            #
                            second_last_set_element = this_scenario_data[ this_param ][ this_param_keys[-2] ]
                            second_last_set_element_unique = [] # list( set( second_last_set_element ) )
                            for u in range( len( second_last_set_element ) ):
                                if second_last_set_element[u] not in second_last_set_element_unique:
                                    second_last_set_element_unique.append( second_last_set_element[u] )
                            #
                            for s in range( len( second_last_set_element_unique ) ):
                                #  MOVE AFTER len() conditional // g.write( second_last_set_element_unique[s] + ' ' )
                                value_indices_s = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[-2] ] ) if x == str( second_last_set_element_unique[s] ) ]
                                value_indices_n1 = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[0] ] ) if x == str( this_set_element_unique_1[n1] ) ]
                                value_indices_n2 = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[1] ] ) if x == str( this_set_element_unique_2[n2] ) ]
                                value_indices_n3 = [ i for i, x in enumerate( this_scenario_data[ this_param ][ this_param_keys[2] ] ) if x == str( this_set_element_unique_3[n3] ) ]
                                #
                                r_index = set(value_indices_s) & set(value_indices_n1) & set(value_indices_n2) & set(value_indices_n3)
                                value_indices = list( r_index )
                                value_indices.sort()
                                #
                                if len( value_indices ) != 0:
                                    g.write( '[' + str( this_set_element_unique_1[n1] ) + ',' + str( this_set_element_unique_2[n2] ) + ',' + str( this_set_element_unique_3[n3] ) + ',*,*]:\n' )
                                    #
                                    for y in range( len( last_set_element_unique ) ):
                                        g.write( str( last_set_element_unique[y] ) + ' ')
                                    g.write(':=\n')
                                    #
                                    g.write( second_last_set_element_unique[s] + ' ' )
                                    #
                                    # these_values = this_scenario_data[ this_param ]['value'][ value_indices[0]:value_indices[-1]+1 ]
                                    these_values = []
                                    for val in range( len( value_indices ) ):
                                        these_values.append( this_scenario_data[ this_param ]['value'][ value_indices[val] ] )
                                    for val in range( len( these_values ) ):
                                        g.write( str( these_values[val] ) + ' ' )
                                    g.write('\n') #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            #
            #g.write('\n') 
            #-----------------------------------------#
            g.write( ';\n\n' )
    #
    # remember the default values for printing:
    g.write('param AccumulatedAnnualDemand default 0 :=\n;\n')
    # if scenario_list[scen] == 'BAU':
    #     g.write('param AnnualEmissionLimit default 99999 :=\n;\n')
    g.write('param AnnualEmissionLimit default 99999 :=\n;\n') # here we are using no Emission Limit
    g.write('param AnnualExogenousEmission default 0 :=\n;\n')
    g.write('param CapacityOfOneTechnologyUnit default 0 :=\n;\n')
    g.write('param CapitalCostStorage default 0 :=\n;\n')
    g.write('param Conversionld default 0 :=\n;\n')
    g.write('param Conversionlh default 0 :=\n;\n')
    g.write('param Conversionls default 0 :=\n;\n')
    g.write('param DaySplit default 0.00137 :=\n;\n')
    g.write('param DaysInDayType default 7 :=\n;\n')
    g.write('param DepreciationMethod default 1 :=\n;\n')
    g.write('param DiscountRate default ' + str(dr_default) + ' :=\n;\n') # repalced from 0.05 // 0.0831
    # g.write('param EmissionsPenalty default 0 :=\n;\n')
    g.write('param MinStorageCharge default 0 :=\n;\n')
    g.write('param ModelPeriodEmissionLimit default 99999 :=\n;\n')
    g.write('param ModelPeriodExogenousEmission default 0 :=\n;\n')
    g.write('param OperationalLifeStorage default 1 :=\n;\n')
    g.write('param REMinProductionTarget default 0 :=\n;\n')
    g.write('param RETagFuel default 0 :=\n;\n')
    g.write('param RETagTechnology default 0 :=\n;\n')
    g.write('param ReserveMargin default 0 :=\n;\n')
    g.write('param ReserveMarginTagFuel default 0 :=\n;\n')
    g.write('param ReserveMarginTagTechnology default 0 :=\n;\n')
    g.write('param ResidualStorageCapacity default 0 :=\n;\n')
    g.write('param StorageLevelStart default 0 :=\n;\n')
    g.write('param StorageMaxChargeRate default 0 :=\n;\n')
    g.write('param StorageMaxDischargeRate default 0 :=\n;\n')
    g.write('param TechnologyFromStorage default 0 :=\n;\n')
    g.write('param TechnologyToStorage default 0 :=\n;\n')
    # g.write('param TotalAnnualMaxCapacityInvestment default 99999 :=\n;\n')
    if scenario_list[scen] == 'BAU':
        g.write('param TotalAnnualMinCapacity default 0 :=\n;\n')
    # g.write('param TotalTechnologyAnnualActivityUpperLimit default 99999 :=\n;\n')
    g.write('param TotalTechnologyModelPeriodActivityLowerLimit default 0 :=\n;\n')
    g.write('param TotalTechnologyModelPeriodActivityUpperLimit default 99999 :=\n;\n')
    g.write('param TradeRoute default 0 :=\n;\n')
    #
    g.write('#\n' + 'end;\n')
    #
    g.close()
    #
    ###########################################################################################################################
    # Furthermore, we must print the inputs separately for faste deployment of the input matrix:
    #
    if scenario_list[scen] != 'BAU':
        this_Blend_Shares_data = Blend_Shares[ scenario_list[scen] ]
    #
    basic_header_elements = [ 'Future.ID', 'Strategy.ID', 'Strategy', 'Fuel', 'Technology', 'Emission', 'Season', 'Year' ]
    #
    parameters_to_print = [ 'SpecifiedAnnualDemand',
                            'CapacityFactor',
                            'OperationalLife',
                            'ResidualCapacity',
                            'InputActivityRatio',
                            'OutputActivityRatio',
                            'EmissionActivityRatio',
                            'CapitalCost',
                            'VariableCost',
                            'FixedCost',
                            'TotalAnnualMaxCapacity',
                            'TotalAnnualMinCapacity',
                            'TotalAnnualMaxCapacityInvestment',
                            'TotalAnnualMinCapacityInvestment',
                            'TotalTechnologyAnnualActivityUpperLimit',
                            'TotalTechnologyAnnualActivityLowerLimit' ]
    #
    more_params = [   'DistanceDriven',
                    'UnitCapitalCost (USD)',
                    'UnitFixedCost (USD)',
                    'BiofuelShares']
    #
    filter_params = [   'FilterFuelType',
                    'FilterVehicleType']
    #
    input_params_table_headers = basic_header_elements + parameters_to_print + more_params + filter_params
    all_data_row = []
    all_data_row_partial = []
    #
    combination_list = []
    synthesized_all_data_row = []
    #
    # memory elements:
    f_unique_list, f_counter, f_counter_list, f_unique_counter_list = [], 1, [], []
    t_unique_list, t_counter, t_counter_list, t_unique_counter_list = [], 1, [], []
    e_unique_list, e_counter, e_counter_list, e_unique_counter_list = [], 1, [], []
    l_unique_list, l_counter, l_counter_list, l_unique_counter_list = [], 1, [], []
    y_unique_list, y_counter, y_counter_list, y_unique_counter_list = [], 1, [], []
    #
    for p in range( len( parameters_to_print ) ):
        #
        this_p_index = S_DICT_params_structure[ 'parameter' ].index( parameters_to_print[p] )
        this_p_index_list = S_DICT_params_structure[ 'index_list' ][ this_p_index ]
        #
        for n in range( 0, len( this_scenario_data[ parameters_to_print[p] ][ 'value' ] ) ):
            #
            single_data_row = []
            single_data_row_partial = []
            #
            single_data_row.append( 0 )
            single_data_row.append( scen )
            single_data_row.append( scenario_list[scen] )
            #
            strcode = ''
            #
            if 'f' in this_p_index_list:
                single_data_row.append( this_scenario_data[ parameters_to_print[p] ][ 'f' ][n] ) # Filling FUEL if necessary
                if single_data_row[-1] not in f_unique_list:
                    f_unique_list.append( single_data_row[-1] )
                    f_counter_list.append( f_counter )
                    f_unique_counter_list.append( f_counter )
                    f_counter += 1
                else:
                    f_counter_list.append( f_unique_counter_list[ f_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(f_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 't' in this_p_index_list:
                single_data_row.append( this_scenario_data[ parameters_to_print[p] ][ 't' ][n] ) # Filling TECHNOLOGY if necessary
                if single_data_row[-1] not in t_unique_list:
                    t_unique_list.append( single_data_row[-1] )
                    t_counter_list.append( t_counter )
                    t_unique_counter_list.append( t_counter )
                    t_counter += 1
                else:
                    t_counter_list.append( t_unique_counter_list[ t_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(t_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 'e' in this_p_index_list:
                single_data_row.append( this_scenario_data[ parameters_to_print[p] ][ 'e' ][n] ) # Filling EMISSION if necessary
                if single_data_row[-1] not in e_unique_list:
                    e_unique_list.append( single_data_row[-1] )
                    e_counter_list.append( e_counter )
                    e_unique_counter_list.append( e_counter )
                    e_counter += 1
                else:
                    e_counter_list.append( e_unique_counter_list[ e_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(e_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 'l' in this_p_index_list:
                single_data_row.append( this_scenario_data[ parameters_to_print[p] ][ 'l' ][n] ) # Filling SEASON if necessary
                if single_data_row[-1] not in l_unique_list:
                    l_unique_list.append( single_data_row[-1] )
                    l_counter_list.append( l_counter )
                    l_unique_counter_list.append( l_counter )
                    l_counter += 1
                else:
                    l_counter_list.append( l_unique_counter_list[ l_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(l_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 'y' in this_p_index_list:
                single_data_row.append( this_scenario_data[ parameters_to_print[p] ][ 'y' ][n] ) # Filling YEAR if necessary
                if single_data_row[-1] not in y_unique_list:
                    y_unique_list.append( single_data_row[-1] )
                    y_counter_list.append( y_counter )
                    y_unique_counter_list.append( y_counter )
                    y_counter += 1
                else:
                    y_counter_list.append( y_unique_counter_list[ y_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(y_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            this_combination_str = str(1) + strcode # deepcopy( single_data_row )
            this_combination = int( this_combination_str )
            #
            for aux_p in range( len(basic_header_elements), len(basic_header_elements) + len( parameters_to_print ) ):
                if aux_p == p + len(basic_header_elements):
                    single_data_row.append( this_scenario_data[ parameters_to_print[p] ][ 'value' ][n] ) # Filling the correct data point
                    single_data_row_partial.append( this_scenario_data[ parameters_to_print[p] ][ 'value' ][n] )
                else:
                    single_data_row.append( '' )
                    single_data_row_partial.append( '' )
            #
            #---------------------------------------------------------------------------------#
            for aide in range( len(more_params)+len(filter_params) ):
                single_data_row.append( '' )
                single_data_row_partial.append( '' )
            #---------------------------------------------------------------------------------#
            #
            all_data_row.append( single_data_row )
            all_data_row_partial.append( single_data_row_partial )
            #
            if this_combination not in combination_list:
                combination_list.append( this_combination )
                synthesized_all_data_row.append( single_data_row )
            else:
                ref_combination_index = combination_list.index( this_combination )
                ref_parameter_index = input_params_table_headers.index( parameters_to_print[p] )
                synthesized_all_data_row[ ref_combination_index ][ ref_parameter_index ] = deepcopy( single_data_row_partial[ ref_parameter_index-len( basic_header_elements ) ] )
                #
            #
            ##################################################################################################################
            #
            if parameters_to_print[p] in ['EmissionActivityRatio']:
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( synthesized_all_data_row[ ref_index ] ) # this must be updated in a further position of the list
                #
                this_tech = this_data_row[4]
                this_emission = this_data_row[5]
                this_year = this_data_row[7]
                this_year_index = time_range_vector.index( int( this_year ) )
                #
                if scenario_list[scen] != 'BAU':
                    if this_tech in list( this_Blend_Shares_data.keys() ):
                        if this_emission in list( this_Blend_Shares_data[ this_tech ].keys() ):
                            #
                            this_Blend_Shares = this_Blend_Shares_data[ this_tech ][ this_emission ]
                            #
                            var_position_index = input_params_table_headers.index( 'BiofuelShares' )
                            this_data_row[ var_position_index ] = round(this_Blend_Shares[ this_year_index ], 4)
                            #
                        #
                    #
                #
                else:
                    var_position_index = input_params_table_headers.index( 'BiofuelShares' )
                    this_data_row[ var_position_index ] = 0.0
                #
                synthesized_all_data_row[ ref_index ] = deepcopy( this_data_row )
                #
            #
            ##################################################################################################################
            #
            if parameters_to_print[p] in [ 'TotalAnnualMaxCapacity', 'CapitalCost', 'FixedCost' ]:
                ref_index = combination_list.index( this_combination )
                this_data_row = deepcopy( synthesized_all_data_row[ ref_index ] ) # this must be updated in a further position of the list
                #
                this_tech = this_data_row[4]
                if this_tech in list( Fleet_Groups_inv.keys() ):
                    group_tech = Fleet_Groups_inv[ this_tech ]
                    #
                    this_year = this_data_row[7]
                    this_year_index = time_range_vector.index( int( this_year ) )
                    #
                    ref_var_position_index = input_params_table_headers.index( parameters_to_print[p] )
                    #
                    if 'Trains' not in group_tech:
                        driven_distance = Reference_driven_distance[ scenario_list[scen] ][ group_tech ][ this_year_index ]
                        #
                        if parameters_to_print[p] == 'TotalAnnualMaxCapacity' or parameters_to_print[p] == 'FixedCost': # this will overwrite for zero-carbon techs, but will not fail.
                            var_position_index = input_params_table_headers.index( 'DistanceDriven' )
                            this_data_row[ var_position_index ] = round(driven_distance, 4)
                        #
                        if parameters_to_print[p] == 'CapitalCost':
                            var_position_index = input_params_table_headers.index( 'UnitCapitalCost (USD)' )
                            this_data_row[ var_position_index ] = round( (10**6)*float( this_data_row[ ref_var_position_index ] )*driven_distance/(10**9), 4)
                        #
                        if parameters_to_print[p] == 'FixedCost':
                            var_position_index = input_params_table_headers.index( 'UnitFixedCost (USD)' )
                            this_data_row[ var_position_index ] = round( (10**6)*float( this_data_row[ ref_var_position_index ] )*driven_distance/(10**9), 4)
                        #
                        synthesized_all_data_row[ ref_index ] = deepcopy( this_data_row )
                        #
                    #
                    ###################################################################################################
                    #
                #
                if parameters_to_print[p] == 'FixedCost':
                    # Creating convinience filters for the analysis of model outputs:
                    if 'TR' in this_tech:
                        #
                        ref_index = combination_list.index( this_combination )
                        this_data_row = deepcopy( synthesized_all_data_row[ ref_index ] ) # this must be updated in a further position of the list
                        #
                        var_position_index = input_params_table_headers.index( 'FilterFuelType' )
                        ############################################
                        # By Fuel Type
                        for r in range( len( df_fuel_2_code_fuel_list ) ):
                            if df_fuel_2_code_fuel_list[r] in this_tech:
                                this_data_row[ var_position_index ] = df_fuel_2_code_plain_english[ r ]
                                break
                        ############################################
                        var_position_index = input_params_table_headers.index( 'FilterVehicleType' )
                        # By vehicle type
                        for r in range( len( df_tech_2_code_fuel_list ) ):
                            if df_tech_2_code_fuel_list[r] in this_tech:
                                this_data_row[ var_position_index ] = df_tech_2_code_plain_english[ r ]
                                break
                        #
                        synthesized_all_data_row[ ref_index ] = deepcopy( this_data_row )
                        #
                    #
                #
            #
        #
    #
    ###########################################################################################################################
    #
    with open( './Executables' + '/' + str( scenario_list[scen] ) + '_0' + '/' + str( scenario_list[scen] ) + '_0' + '_Input.csv', 'w', newline = '') as param_csv:
        csvwriter = csv.writer(param_csv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        # Print the header:
        csvwriter.writerow( input_params_table_headers )
        # Print all else:
        for n in range( len( synthesized_all_data_row ) ):
            csvwriter.writerow( synthesized_all_data_row[n] )
    #

def generalized_logistic_curve(x, L, Q, k, M):
  return L/( 1 + Q*math.exp( -k*( x-M ) ) )
#
def interpolation_blend( start_blend_point, mid_blend_point, final_blend_point, value_list, time_range_vector ):
    #
    start_blend_year, start_blend_value = start_blend_point[0], start_blend_point[1]/100
    final_blend_year, final_blend_value = final_blend_point[0], final_blend_point[1]/100
    #
    # Now we need to interpolate:
    x_coord_tofill = [] # these are indices that are NOT known - to interpolate
    xp_coord_known = [] # these are known indices - use for interpolation
    fp_coord_known = [] # these are the values known to interpolate the whole series
    #
    if mid_blend_point != 'None': # this means we must use a linear interpolation
        mid_blend_year, mid_blend_value = mid_blend_point[0], mid_blend_point[1]/100
        #
        for t in range( len( time_range_vector ) ):
            something_to_fill = False
            #
            if time_range_vector[t] < start_blend_year:
                fp_coord_known.append( 0.0 )
            #
            if time_range_vector[t] == start_blend_year:
                fp_coord_known.append( start_blend_value )
            #
            if ( time_range_vector[t] > start_blend_year and time_range_vector[t] < mid_blend_year ) or ( time_range_vector[t] > mid_blend_year and time_range_vector[t] < final_blend_year ):
                something_to_fill = True
            #
            if time_range_vector[t] == mid_blend_year:
                fp_coord_known.append( mid_blend_value )
            #
            if time_range_vector[t] == final_blend_year or time_range_vector[t] > final_blend_year:
                fp_coord_known.append( final_blend_value )
            #
            if something_to_fill == True:
                x_coord_tofill.append( t )
            else:
                xp_coord_known.append( t ) # means this value was stored
            #
            y_coord_filled = list( np.interp( x_coord_tofill, xp_coord_known, fp_coord_known ) )
            #
            interpolated_values = []
            for coord in range( len( time_range_vector ) ):
                if coord in xp_coord_known:
                    value_index = xp_coord_known.index(coord)
                    interpolated_values.append( float( fp_coord_known[value_index] ) )
                elif coord in x_coord_tofill:
                    value_index = x_coord_tofill.index(coord)
                    interpolated_values.append( float( y_coord_filled[value_index] ) )
            #
        #
    else:
        #
        for t in range( len( time_range_vector ) ):
            something_to_fill = False
            #
            if time_range_vector[t] < start_blend_year:
                fp_coord_known.append( 0.0 )
            #
            if time_range_vector[t] == start_blend_year:
                fp_coord_known.append( start_blend_value )
            #
            if ( time_range_vector[t] > start_blend_year and time_range_vector[t] < final_blend_year ):
                something_to_fill = True
            #
            if time_range_vector[t] == final_blend_year or time_range_vector[t] > final_blend_year:
                fp_coord_known.append( final_blend_value )
            #
            if something_to_fill == True:
                x_coord_tofill.append( t )
            else:
                xp_coord_known.append( t ) # means this value was stored
            #
            y_coord_filled = list( np.interp( x_coord_tofill, xp_coord_known, fp_coord_known ) )
            #
            interpolated_values = []
            for coord in range( len( time_range_vector ) ):
                if coord in xp_coord_known:
                    value_index = xp_coord_known.index(coord)
                    interpolated_values.append( float( fp_coord_known[value_index] ) )
                elif coord in x_coord_tofill:
                    value_index = x_coord_tofill.index(coord)
                    interpolated_values.append( float( y_coord_filled[value_index] ) )
            #
        #
    #
    new_value_list = []
    for n in range( len( value_list ) ):
        new_value_list.append( value_list[n]*( 1-interpolated_values[n] ) )
    new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
    biofuel_shares = [ round(elem, 4) for elem in interpolated_values ]
    #
    return new_value_list_rounded, biofuel_shares
    #
#
def interpolation_non_linear_final_flexible( time_list, value_list, new_relative_final_value, Flexible_Initial_Year_of_Uncertainty ):
    # Rememeber that the 'old_relative_final_value' is 1
    old_relative_final_value = 1
    new_value_list = []
    # We select a list that goes from the "Flexible_Initial_Year_of_Uncertainty" to the Final Year of the Time Series
    initial_year_index = time_list.index( Flexible_Initial_Year_of_Uncertainty )
    fraction_time_list = time_list[initial_year_index:]
    fraction_value_list = value_list[initial_year_index:]
    # We now perform the 'non-linear OR linear adjustment':
    xdata = [ fraction_time_list[i] - fraction_time_list[0] for i in range( len( fraction_time_list ) ) ]
    ydata = [ float( fraction_value_list[i] ) for i in range( len( fraction_value_list ) ) ]
    delta_ydata = [ ydata[i]-ydata[i-1] for i in range( 1,len( ydata ) ) ]
    #
    m_original = ( ydata[-1]-ydata[0] ) / ( xdata[-1]-xdata[0] )
    #
    m_new = ( ydata[-1]*(new_relative_final_value/old_relative_final_value) - ydata[0] ) / ( xdata[-1]-xdata[0] )
    #
    if float(m_original) == 0.0:
        delta_ydata_new = [m_new for i in range( 1,len( ydata ) ) ]
    else:
        delta_ydata_new = [ (m_new/m_original)*(ydata[i]-ydata[i-1]) for i in range( 1,len( ydata ) ) ]
    #
    ydata_new = [ 0 for i in range( len( ydata ) ) ]
    ydata_new[0] = ydata[0]
    for i in range( 0, len( delta_ydata ) ):
        ydata_new[i+1] = ydata_new[i] + delta_ydata_new[i]
    #
    # We now recreate the new_value_list considering the fraction before and after the Flexible_Initial_Year_of_Uncertainty
    fraction_list_counter = 0
    for n in range( len( time_list ) ):
        if time_list[n] >= Flexible_Initial_Year_of_Uncertainty:
            new_value_list.append( ydata_new[ fraction_list_counter ] )
            fraction_list_counter += 1
        else:
            new_value_list.append( float( value_list[n] ) )
    #
    # We return the list:
    return new_value_list
#
def interpolation_non_linear_final( time_list, value_list, new_relative_final_value ):
    # Rememeber that the 'old_relative_final_value' is 1
    old_relative_final_value = 1
    new_value_list = []
    # We select a list that goes from the "Initial_Year_of_Uncertainty" to the Final Year of the Time Series
    initial_year_index = time_list.index( Initial_Year_of_Uncertainty )
    fraction_time_list = time_list[initial_year_index:]
    fraction_value_list = value_list[initial_year_index:]
    # We now perform the 'non-linear OR linear adjustment':
    xdata = [ fraction_time_list[i] - fraction_time_list[0] for i in range( len( fraction_time_list ) ) ]
    ydata = [ float( fraction_value_list[i] ) for i in range( len( fraction_value_list ) ) ]
    delta_ydata = [ ydata[i]-ydata[i-1] for i in range( 1,len( ydata ) ) ]
    #
    m_original = ( ydata[-1]-ydata[0] ) / ( xdata[-1]-xdata[0] )
    #
    m_new = ( ydata[-1]*(new_relative_final_value/old_relative_final_value) - ydata[0] ) / ( xdata[-1]-xdata[0] )
    #
    if float(m_original) == 0.0:
        delta_ydata_new = [m_new for i in range( 1,len( ydata ) ) ]
    else:
        delta_ydata_new = [ (m_new/m_original)*(ydata[i]-ydata[i-1]) for i in range( 1,len( ydata ) ) ]
    #
    ydata_new = [ 0 for i in range( len( ydata ) ) ]
    ydata_new[0] = ydata[0]
    for i in range( 0, len( delta_ydata ) ):
        ydata_new[i+1] = ydata_new[i] + delta_ydata_new[i]
    #
    # We now recreate the new_value_list considering the fraction before and after the Initial_Year_of_Uncertainty
    fraction_list_counter = 0
    for n in range( len( time_list ) ):
        if time_list[n] >= Initial_Year_of_Uncertainty:
            new_value_list.append( ydata_new[ fraction_list_counter ] )
            fraction_list_counter += 1
        else:
            new_value_list.append( float( value_list[n] ) )
    #
    # We return the list:
    return new_value_list
#
def linear_interpolation_time_series( time_range, known_years, known_values ):
    # Now we need to interpolate:
    x_coord_tofill = [] # these are indices that are NOT known - to interpolate
    xp_coord_known = [] # these are known indices - use for interpolation
    fp_coord_known = [] # these are the values known to interpolate the whole series
    #
    min_t = min( known_years )
    for t in range( len( time_range ) ):
        if ( time_range[t] in known_years ) or ( time_range[t] < min_t ):
            xp_coord_known.append( t )
            #
            if time_range[t] < min_t:
                fp_coord_known.append( 0.0 )
            else:
                future_year_index = known_years.index( time_range[t] )
                fp_coord_known.append( float(known_values[ future_year_index ]) )
            #
        else:
            x_coord_tofill.append( t )
    #
    y_coord_filled = list( np.interp( x_coord_tofill, xp_coord_known, fp_coord_known ) )
    #
    interpolated_values = []
    for coord in range( len( time_range ) ):
        if coord in xp_coord_known:
            value_index = xp_coord_known.index(coord)
            interpolated_values.append( float( fp_coord_known[value_index] ) )
        elif coord in x_coord_tofill:
            value_index = x_coord_tofill.index(coord)
            interpolated_values.append( float( y_coord_filled[value_index] ) )
    #
    return interpolated_values
#
def csv_printer_parallel(s, scenario_list, stable_scenarios, basic_header_elements, parameters_to_print, S_DICT_params_structure):
    #
    input_params_table_headers = basic_header_elements + parameters_to_print
    all_data_row = []
    all_data_row_partial = []
    #
    combination_list = []
    synthesized_all_data_row = []
    #
    # memory elements:
    f_unique_list, f_counter, f_counter_list, f_unique_counter_list = [], 1, [], []
    t_unique_list, t_counter, t_counter_list, t_unique_counter_list = [], 1, [], []
    e_unique_list, e_counter, e_counter_list, e_unique_counter_list = [], 1, [], []
    l_unique_list, l_counter, l_counter_list, l_unique_counter_list = [], 1, [], []
    y_unique_list, y_counter, y_counter_list, y_unique_counter_list = [], 1, [], []
    #
    each_parameter_header = [ 'PARAMETER','Scenario','REGION','TECHNOLOGY','FUEL','EMISSION','MODE_OF_OPERATION','YEAR','TIMESLICE','SEASON','DAYTYPE','DAILYTIMEBRACKET','STORAGE','Value' ]
    each_parameter_all_data_row = {}
    #
    print( '    ', s+1, ' // Printing scenarios: ', scenario_list[s] )
    each_parameter_all_data_row.update( { scenario_list[s]:{} } )
    #
    for p in range( len( parameters_to_print ) ):
        each_parameter_all_data_row[ scenario_list[s] ].update( { parameters_to_print[p]:[] } )
        #
        this_p_index = S_DICT_params_structure[ 'parameter' ].index( parameters_to_print[p] )
        this_p_index_list = S_DICT_params_structure[ 'index_list' ][ this_p_index ]
        #
        for n in range( 0, len( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'value' ] ) ):
            #
            single_data_row = []
            single_data_row_partial = []
            #
            single_data_row.append( 0 ) # Filling Future.ID
            single_data_row.append( s ) # Filling Strategy.ID
            single_data_row.append( scenario_list[s] ) # Filling Strategy
            #
            strcode = ''
            #
            if 'f' in this_p_index_list:
                single_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'f' ][n] ) # Filling FUEL if necessary
                if single_data_row[-1] not in f_unique_list:
                    f_unique_list.append( single_data_row[-1] )
                    f_counter_list.append( f_counter )
                    f_unique_counter_list.append( f_counter )
                    f_counter += 1
                else:
                    f_counter_list.append( f_unique_counter_list[ f_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(f_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 't' in this_p_index_list:
                try:
                    single_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 't' ][n] ) # Filling TECHNOLOGY if necessary
                except Exception:
                    print('---------------------------')
                    print(scenario_list[s], parameters_to_print[p], n, len(stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 't' ]))
                    print('---------------------------')
                    sys.exit()

                if single_data_row[-1] not in t_unique_list:
                    t_unique_list.append( single_data_row[-1] )
                    t_counter_list.append( t_counter )
                    t_unique_counter_list.append( t_counter )
                    t_counter += 1
                else:
                    t_counter_list.append( t_unique_counter_list[ t_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(t_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 'e' in this_p_index_list:
                single_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'e' ][n] ) # Filling EMISSION if necessary
                if single_data_row[-1] not in e_unique_list:
                    e_unique_list.append( single_data_row[-1] )
                    e_counter_list.append( e_counter )
                    e_unique_counter_list.append( e_counter )
                    e_counter += 1
                else:
                    e_counter_list.append( e_unique_counter_list[ e_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(e_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            if 'l' in this_p_index_list:
                single_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'l' ][n] ) # Filling SEASON if necessary
                if single_data_row[-1] not in l_unique_list:
                    l_unique_list.append( single_data_row[-1] )
                    l_counter_list.append( l_counter )
                    l_unique_counter_list.append( l_counter )
                    l_counter += 1
                else:
                    l_counter_list.append( l_unique_counter_list[ l_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(l_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '000' # this is done to avoid repeated characters
            #
            if 'y' in this_p_index_list:
                single_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'y' ][n] ) # Filling YEAR if necessary
                if single_data_row[-1] not in y_unique_list:
                    y_unique_list.append( single_data_row[-1] )
                    y_counter_list.append( y_counter )
                    y_unique_counter_list.append( y_counter )
                    y_counter += 1
                else:
                    y_counter_list.append( y_unique_counter_list[ y_unique_list.index( single_data_row[-1] ) ] )
                strcode += str(y_counter_list[-1])
            else:
                single_data_row.append( '' )
                strcode += '0'
            #
            this_combination_str = str(10) + str(s) + strcode # deepcopy( single_data_row )
            #
            this_combination = int( this_combination_str )
            #
            for aux_p in range( len(basic_header_elements), len(basic_header_elements) + len( parameters_to_print ) ):
                if aux_p == p + len(basic_header_elements):
                    single_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'value' ][n] ) # Filling the correct data point
                    single_data_row_partial.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'value' ][n] )
                else:
                    single_data_row.append( '' )
                    single_data_row_partial.append( '' )
            #
            all_data_row.append( single_data_row )
            all_data_row_partial.append( single_data_row_partial )
            #
            if this_combination not in combination_list:
                combination_list.append( this_combination )
                synthesized_all_data_row.append( single_data_row )
            else:
                ref_combination_index = combination_list.index( this_combination )
                ref_parameter_index = input_params_table_headers.index( parameters_to_print[p] )
                synthesized_all_data_row[ ref_combination_index ][ ref_parameter_index ] = deepcopy( single_data_row_partial[ ref_parameter_index-len( basic_header_elements ) ] )
            #
            # Let us proceed with the list for the each_parameter list:
            this_each_parameter_all_data_row = [] # each_parameter_header = [ 'PARAMETER','Scenario','REGION','TECHNOLOGY','FUEL','EMISSION','MODE_OF_OPERATION','YEAR','TIMESLICE','SEASON','DAYTYPE','DAILYTIMEBRACKET','STORAGE','Value' ]
            #
            this_each_parameter_all_data_row.append( parameters_to_print[p] ) # Alternatively, fill PARAMETER
            this_each_parameter_all_data_row.append( scenario_list[s] ) # Alternatively, fill Scenario
            if 'r' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'r' ][n] ) # Filling REGION if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            if 't' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 't' ][n] ) # Filling TECHNOLOGY if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            if 'f' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'f' ][n] ) # Filling FUEL if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            if 'e' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'e' ][n] ) # Filling EMISSION if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            if 'm' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'm' ][n] ) # Filling MODE_OF_OPERATION if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            if 'y' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'y' ][n] ) # Filling YEAR if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            if 'l' in this_p_index_list:
                this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'l' ][n] ) # Filling TIMESLICE if necessary
            else:
                this_each_parameter_all_data_row.append( '' )
            this_each_parameter_all_data_row.append( '' )
            this_each_parameter_all_data_row.append( '' )
            this_each_parameter_all_data_row.append( '' )
            this_each_parameter_all_data_row.append( '' )
            this_each_parameter_all_data_row.append( stable_scenarios[ scenario_list[s] ][ parameters_to_print[p] ][ 'value' ][n] )
            #
            each_parameter_all_data_row[ scenario_list[s] ][ parameters_to_print[p] ].append( this_each_parameter_all_data_row )

    #########################################################################################
    print('4: We have printed the inputs. We will store the parameters that the experiment uses and be done.')
    # let us be reminded of the 'each_parameter_header'
    for p in range( len( parameters_to_print ) ):
        param_filename = './B1_Output_Params/' + str( scenario_list[s] ) + '/' + str( parameters_to_print[p] ) + '.csv'
        with open( param_filename, 'w', newline = '') as param_csv:
            csvwriter = csv.writer(param_csv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            # Print the header:
            csvwriter.writerow( each_parameter_header )
            # Let us locate the data:
            for n in range( len( each_parameter_all_data_row[ scenario_list[s] ][ parameters_to_print[p] ] ) ):
                csvwriter.writerow( each_parameter_all_data_row[ scenario_list[s] ][ parameters_to_print[p] ][n] )

if __name__ == '__main__':
    #
    all_years = [ y for y in range( 2018 , 2050+1 ) ]
    index_2024 = all_years.index( 2024 )
    initial_year = all_years[0]
    final_year = all_years[-1]
    """
    *Abbreviations:*
    """
    start1 = time.time()
    #
    # We must open useful GDP data for denominator
    df_gdp_ref = pd.read_excel('_GDP_Ref.xlsx', 'GDP')
    list_gdp_growth_ref = df_gdp_ref['GDP_Growth'].tolist()
    list_gdp_ref = df_gdp_ref['GDP'].tolist()
    #
    '''''
    ################################# PART 1 #################################
    '''''
    print('1: We have defined some data. Now we will read the parameters we have as reference (or previous parameters) into a dictionary.')
    '''
    # 1.A) We extract the strucute setup of the model based on 'Structure.xlsx'
    '''
    structure_filename = "B1_Model_Structure.xlsx"
    structure_file = pd.ExcelFile(structure_filename)
    structure_sheetnames = structure_file.sheet_names  # see all sheet names
    sheet_sets_structure = pd.read_excel(open(structure_filename, 'rb'),
                                         header=None,
                                         sheet_name=structure_sheetnames[0])
    sheet_params_structure = pd.read_excel(open(structure_filename, 'rb'),
                                           header=None,
                                           sheet_name=structure_sheetnames[1])
    sheet_vars_structure = pd.read_excel(open(structure_filename, 'rb'),
                                         header=None,
                                         sheet_name=structure_sheetnames[2])

    S_DICT_sets_structure = {'set':[],'initial':[],'number_of_elements':[],'elements_list':[]}
    for col in range(1,11+1):  # 11 columns
        S_DICT_sets_structure['set'].append( sheet_sets_structure.iat[0, col] )
        S_DICT_sets_structure['initial'].append( sheet_sets_structure.iat[1, col] )
        S_DICT_sets_structure['number_of_elements'].append( int( sheet_sets_structure.iat[2, col] ) )
        #
        element_number = int( sheet_sets_structure.iat[2, col] )
        this_elements_list = []
        if element_number > 0:
            for n in range( 1, element_number+1 ):
                this_elements_list.append( sheet_sets_structure.iat[2+n, col] )
        S_DICT_sets_structure['elements_list'].append( this_elements_list )
    #
    S_DICT_params_structure = {'category':[],'parameter':[],'number_of_elements':[],'index_list':[]}
    param_category_list = []
    for col in range(1,30+1):  # 30 columns
        if str( sheet_params_structure.iat[0, col] ) != '':
            param_category_list.append( sheet_params_structure.iat[0, col] )
        S_DICT_params_structure['category'].append( param_category_list[-1] )
        S_DICT_params_structure['parameter'].append( sheet_params_structure.iat[1, col] )
        S_DICT_params_structure['number_of_elements'].append( int( sheet_params_structure.iat[2, col] ) )
        #
        index_number = int( sheet_params_structure.iat[2, col] )
        this_index_list = []
        for n in range(1, index_number+1):
            this_index_list.append( sheet_params_structure.iat[2+n, col] )
        S_DICT_params_structure['index_list'].append( this_index_list )
    #
    S_DICT_vars_structure = {'category':[],'variable':[],'number_of_elements':[],'index_list':[]}
    var_category_list = []
    for col in range(1,43+1):  # 43 columns
        if str( sheet_vars_structure.iat[0, col] ) != '':
            var_category_list.append( sheet_vars_structure.iat[0, col] )
        S_DICT_vars_structure['category'].append( var_category_list[-1] )
        S_DICT_vars_structure['variable'].append( sheet_vars_structure.iat[1, col] )
        S_DICT_vars_structure['number_of_elements'].append( int( sheet_vars_structure.iat[2, col] ) )
        #
        index_number = int( sheet_vars_structure.iat[2, col] )
        this_index_list = []
        for n in range(1, index_number+1):
            this_index_list.append( sheet_vars_structure.iat[2+n, col] )
        S_DICT_vars_structure['index_list'].append( this_index_list )
    #-------------------------------------------#
    # LET'S HAVE THE ENTIRE LIST OF TECHNOLOGIES:
    all_techs_list = S_DICT_sets_structure[ 'elements_list' ][ 1 ]
    #-------------------------------------------#
    '''
    Structural dictionary 1: Notes
    a) We use this dictionary relating a specific technology and a group technology and associate the prefix list
    '''
    Fleet_Groups =              pickle.load( open( './A1_Outputs/A-O_Fleet_Groups.pickle',            "rb" ) )
    Ind_Groups =                pickle.load( open( './A1_Outputs/A-O_Ind_Groups.pickle',            "rb" ) )
    Fleet_Groups['Techs_Microbuses'] += [ 'TRMBUSHYD' ] # this is an add on, kind of a patch
    Fleet_Groups_Distance =     pickle.load( open( './A1_Outputs/A-O_Fleet_Groups_Distance.pickle',   "rb" ) )
    Fleet_Groups_OR =           pickle.load( open( './A1_Outputs/A-O_Fleet_Groups_OR.pickle',         "rb" ) )
    Fleet_Groups_techs_2_dem =  pickle.load( open( './A1_Outputs/A-O_Fleet_Groups_T2D.pickle',        "rb" ) )
    #
    Fleet_Groups_inv = {}
    for k in range( len( list( Fleet_Groups.keys() ) ) ):
        this_fleet_group_key = list( Fleet_Groups.keys() )[k]
        for e in range( len( Fleet_Groups[ this_fleet_group_key ] ) ):
            this_fleet_group_tech = Fleet_Groups[ this_fleet_group_key ][ e ]
            Fleet_Groups_inv.update( { this_fleet_group_tech:this_fleet_group_key } )
    #
    Ind_Groups_inv = {}
    for k in range( len( list( Ind_Groups.keys() ) ) ):
        this_ind_group_key = list( Ind_Groups.keys() )[k]
        for e in range( len( Ind_Groups[ this_ind_group_key ] ) ):
            this_ind_group_tech = Ind_Groups[ this_ind_group_key ][ e ]
            Ind_Groups_inv.update( { this_ind_group_tech:this_ind_group_key } )
    #
    group_tech_PUBLIC = []
    group_tech_PRIVATE = []
    group_tech_FREIGHT_HEA = []
    group_tech_FREIGHT_LIG = []
    #
    for t in range( len( list( Fleet_Groups_techs_2_dem.keys() ) ) ):
        tech_key = list( Fleet_Groups_techs_2_dem.keys() )[t]
        this_fuel = Fleet_Groups_techs_2_dem[ tech_key ]
        if 'PRI' in this_fuel:
            group_tech_PRIVATE.append( tech_key )
        if 'PUB' in this_fuel:
            group_tech_PUBLIC.append( tech_key )
        if 'FREHEA' in this_fuel:
            group_tech_FREIGHT_HEA.append( tech_key )
        if 'FRELIG' in this_fuel:
            group_tech_FREIGHT_LIG.append( tech_key )
    #
    group_tech_PASSENGER = group_tech_PUBLIC + group_tech_PRIVATE
    group_tech_FREIGHT = group_tech_FREIGHT_HEA + group_tech_FREIGHT_LIG
    #
    global time_range_vector
    time_range_vector = [ int(i) for i in S_DICT_sets_structure[ 'elements_list' ][0] ]
    '''
    ####################################################################################################################################################
    # 1.B) We finish this sub-part, and proceed to read all the base scenarios.
    '''
    header_row = ['PARAMETER','Scenario','REGION','TECHNOLOGY','FUEL','EMISSION','MODE_OF_OPERATION','TIMESLICE','YEAR','SEASON','DAYTYPE','DAILYTIMEBRACKET','STORAGE','Value']
    #
    scenario_list_sheet = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Scenarios' )
    scenario_list_all = [ scenario_list_sheet[ 'Name' ].tolist()[i] for i in range( len( scenario_list_sheet[ 'Name' ].tolist() ) ) if scenario_list_sheet[ 'Activated' ].tolist()[i] == 'YES' ]
    scenario_list_reference = [ scenario_list_sheet[ 'Reference' ].tolist()[i] for i in range( len( scenario_list_sheet[ 'Name' ].tolist() ) ) if scenario_list_sheet[ 'Activated' ].tolist()[i] == 'YES' ] # the address to the produced dataset
    scenario_list_based = [ scenario_list_sheet[ 'Based_On' ].tolist()[i] for i in range( len( scenario_list_sheet[ 'Name' ].tolist() ) ) if scenario_list_sheet[ 'Activated' ].tolist()[i] == 'YES' ]
    for i in range( len( scenario_list_sheet[ 'Base' ].tolist() ) ):
        if scenario_list_sheet[ 'Base' ].tolist()[i] == 'YES':
            ref_scenario = scenario_list_sheet[ 'Name' ].tolist()[i]
    #
    scenario_list = [ scenario_list_reference[i] for i in range( len( scenario_list_all ) ) if scenario_list_reference[i] != 'based' ]
    #sys.exit()
    #
    base_configuration_overall = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Overall_Parameters' )
    base_configuration_transport_elasticity = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='TElasticity' )
    base_configuration_distance = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Distance_Levers' )
    base_configuration_modeshift = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Mode_Shift' )
    base_configuration_or = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Occupancy_Rate' )
    base_configuration_adoption = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Tech_Adoption' )
    base_configuration_electrical = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Electrical' )
    base_configuration_smartGrid = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='SmartGrid' )
    base_configuration_E_and_D = pd.read_excel( 'B1_Scenario_Config.xlsx', sheet_name='Efficiency' )
    #
    all_dataset_address = './A2_Output_Params/'
    '''
    # Call the default parameters for later use:
    '''
    list_param_default_value = pd.read_excel( 'B1_Default_Param.xlsx' )
    list_param_default_value_params = list( list_param_default_value['Parameter'] )
    list_param_default_value_value = list( list_param_default_value['Default_Value'] )
    #
    global Initial_Year_of_Uncertainty
    for n in range( len( base_configuration_overall.index ) ):
        if str( base_configuration_overall.loc[ n, 'Parameter' ] ) == 'Initial_Year_of_Uncertainty':
            Initial_Year_of_Uncertainty = int( base_configuration_overall.loc[ n, 'Value' ] )
    '''
    ####################################################################################################################################################
    '''
    # This section reads a reference data.csv from baseline scenarios and frames Structure-OSEMOSYS_CR.xlsx
    col_position = []
    col_corresponding_initial = []
    for n in range( len( S_DICT_sets_structure['set'] ) ):
        col_position.append( header_row.index( S_DICT_sets_structure['set'][n] ) )
        col_corresponding_initial.append( S_DICT_sets_structure['initial'][n] )
    # Define the dictionary for calibrated database:
    stable_scenarios = {}
    for scen in scenario_list:
        stable_scenarios.update( { scen:{} } )
    #
    for scen in range( len( scenario_list ) ):
        this_paramter_list_dir = 'A2_Output_Params/' + str( scenario_list[scen] )
        parameter_list = os.listdir( this_paramter_list_dir )
        #
        for p in range( len( parameter_list ) ):
            this_param = parameter_list[p].replace('.csv','')
            stable_scenarios[ scenario_list[scen] ].update( { this_param:{} } )
            # To extract the parameter input data:
            all_params_list_index = S_DICT_params_structure['parameter'].index(this_param)
            this_number_of_elements = S_DICT_params_structure['number_of_elements'][all_params_list_index]
            this_index_list = S_DICT_params_structure['index_list'][all_params_list_index]
            #
            for k in range(this_number_of_elements):
                stable_scenarios[ scenario_list[scen] ][ this_param ].update({this_index_list[k]:[]})
            stable_scenarios[ scenario_list[scen] ][ this_param ].update({'value':[]})
            # Extract data:
            with open( this_paramter_list_dir + '/' + str(parameter_list[p]), mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                #
                for row in csv_reader:
                    if row[ header_row[-1] ] != None and row[ header_row[-1] ] != '':
                        #
                        for h in range( 2, len(header_row)-1 ):
                            if row[ header_row[h] ] != None and row[ header_row[h] ] != '':
                                set_index  = S_DICT_sets_structure['set'].index( header_row[h] )
                                set_initial = S_DICT_sets_structure['initial'][ set_index ]
                                stable_scenarios[ scenario_list[scen] ][ this_param ][ set_initial ].append( row[ header_row[h] ] )
                        stable_scenarios[ scenario_list[scen] ][ this_param ][ 'value' ].append( row[ header_row[-1] ] )
                        #
    stable_scenarios_freeze = deepcopy(stable_scenarios)
    ####################################################################################################################################################
    # 1 - DISTANCE DICTIONARY:
    distance_levers = {}
    base_configuration_distance_unique_scenario_list = []
    for n in range( len( base_configuration_distance.index ) ):
        #
        if str( base_configuration_distance.loc[ n ,'Scenario'] ) not in base_configuration_distance_unique_scenario_list:
            base_configuration_distance_group_set_list = []
            base_configuration_distance_unique_scenario_list.append( str( base_configuration_distance.loc[ n ,'Scenario'] ) )
            distance_levers.update( { base_configuration_distance_unique_scenario_list[-1]:{} } )
        else:
            pass
        #
        if str( base_configuration_distance.loc[ n ,'Group_Set'] ) not in base_configuration_distance_group_set_list:
            base_configuration_distance_group_set_list.append( str( base_configuration_distance.loc[ n ,'Group_Set'] ) )
            distance_levers[ base_configuration_distance_unique_scenario_list[-1] ].update( { base_configuration_distance_group_set_list[-1]:0 } )
        else:
            pass
        #
        # Now we fill the data:
        distance_levers[ base_configuration_distance_unique_scenario_list[-1] ][ base_configuration_distance_group_set_list[-1] ] = float( base_configuration_distance.loc[ n ,'Relative reduction to BAU - distance'] )
        #
    #
    ####################################################################################################################################################
    # 2 - MODE SHIFT DICTIONARY:
    modeshift_params = {}
    base_configuration_modeshift_unique_scenario_list = []
    for n in range( len( base_configuration_modeshift.index ) ):
        #
        if str( base_configuration_modeshift.loc[ n ,'Scenario'] ) not in base_configuration_modeshift_unique_scenario_list:
            base_configuration_modeshift_group_set_list = []
            base_configuration_modeshift_unique_scenario_list.append( str( base_configuration_modeshift.loc[ n ,'Scenario'] ) )
            modeshift_params.update( { base_configuration_modeshift_unique_scenario_list[-1]:{} } )
        else:
            pass
        #
        base_configuration_modeshift_group_set_list.append( str( base_configuration_modeshift.loc[ n ,'Tech_Set'] ) )
        modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ].update( { base_configuration_modeshift_group_set_list[-1]:{} } )
        #
        if str( base_configuration_modeshift.loc[ n ,'Logistic'] ) == 'YES' and str( base_configuration_modeshift.loc[ n ,'Linear'] ) == 'NO':
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ].update( {'Values':[],'Type':'Logistic'} ) # WE MUST REMEMBER THE ORDER OF APPENDING THE PARAMETERS OF LOGISTIC BEHAVIOR: R2021, R2050, L, C, M
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ].update( { 'Context':base_configuration_modeshift.loc[ n ,'Context'] } )
            #
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_modeshift.loc[ n ,'R2021'] ) )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_modeshift.loc[ n ,'R2050'] ) )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_modeshift.loc[ n ,'L'] ) )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_modeshift.loc[ n ,'C'] ) )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_modeshift.loc[ n ,'M'] ) )
            #
        #
        elif str( base_configuration_modeshift.loc[ n ,'Logistic'] ) == 'NO' and str( base_configuration_modeshift.loc[ n ,'Linear'] ) == 'YES':
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ].update( {'Values':[], 'Type':'Linear'} ) # WE MUST REMEMBER THE ORDER OF APPENDING THE PARAMETERS OF LINEAR BEHAVIOR: y_ini, v_2030, v_2040, v_2050
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ].update( { 'Context':base_configuration_modeshift.loc[ n ,'Context'] } )
            #
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_modeshift.loc[ n ,'y_ini'] ) )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( base_configuration_modeshift.loc[ n ,'v_2030'] )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( base_configuration_modeshift.loc[ n ,'v_2040'] )
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ][ 'Values' ].append( base_configuration_modeshift.loc[ n ,'v_2050'] )
            #
        #
        elif str( base_configuration_modeshift.loc[ n ,'Built-in'] ) == 'YES':
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ].update( {'Values':'Check_Cap', 'Type':'Built-in'} ) # WE MUST REMEMBER TO MAKE REFERENCE
            modeshift_params[ base_configuration_modeshift_unique_scenario_list[-1] ][ base_configuration_modeshift_group_set_list[-1] ].update( { 'Context':base_configuration_modeshift.loc[ n ,'Context'] } )
            #
        #
    #
    ####################################################################################################################################################
    # 3 - OCCUPANCY RATE DICTIONARY:
    or_params = {}
    base_configuration_or_unique_scenario_list = []
    for n in range( len( base_configuration_or.index ) ):
        #
        if str( base_configuration_or.loc[ n ,'Scenario'] ) not in base_configuration_or_unique_scenario_list:
            base_configuration_or_group_set_list = []
            base_configuration_or_unique_scenario_list.append( str( base_configuration_or.loc[ n ,'Scenario'] ) )
            or_params.update( { base_configuration_or_unique_scenario_list[-1]:{} } )
        else:
            pass
        #
        if str( base_configuration_or.loc[ n ,'Group_Set'] ) not in base_configuration_or_group_set_list:
            base_configuration_or_group_set_list.append( str( base_configuration_or.loc[ n ,'Group_Set'] ) )
            or_params[ base_configuration_or_unique_scenario_list[-1] ].update( { base_configuration_or_group_set_list[-1]:0 } )
        else:
            pass
        #
        # Now we fill the data:
        or_params[ base_configuration_or_unique_scenario_list[-1] ][ base_configuration_or_group_set_list[-1] ] = float( base_configuration_or.loc[ n ,'Relative increase to BAU - occupancy rate'] )
        #
    ####################################################################################################################################################
    # 4 - TECH ADOPTION DICTIONARY:
    adoption_params = {}
    base_configuration_adoption_unique_scenario_list = []
    for n in range( len( base_configuration_adoption.index ) ):
        #
        if str( base_configuration_adoption.loc[ n ,'Scenario'] ) not in base_configuration_adoption_unique_scenario_list:
            base_configuration_adoption_group_set_list = []
            base_configuration_adoption_unique_scenario_list.append( str( base_configuration_adoption.loc[ n ,'Scenario'] ) )
            adoption_params.update( { base_configuration_adoption_unique_scenario_list[-1]:{} } )
        else:
            pass
        #
        base_configuration_adoption_group_set_list.append( str( base_configuration_adoption.loc[ n ,'Tech_Set'] ) )
        adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ].update( { base_configuration_adoption_group_set_list[-1]:{} } )
        store_the_sector = deepcopy(str( base_configuration_adoption.loc[ n ,'Sector'] ))
        #
        if str( base_configuration_adoption.loc[ n ,'Logistic'] ) == 'YES' and str( base_configuration_adoption.loc[ n ,'Linear'] ) == 'NO':
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ].update( {'Values':[], 'Type':'Logistic', 'Restriction_Type':str( base_configuration_adoption.loc[ n ,'Restriction_Type'] ) } ) # WE MUST REMEMBER THE ORDER OF APPENDING THE PARAMETERS OF LOGISTIC BEHAVIOR: R2021, R2050, L, C, M
            #
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_adoption.loc[ n ,'R2021'] ) )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_adoption.loc[ n ,'R2050'] ) )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_adoption.loc[ n ,'L'] ) )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_adoption.loc[ n ,'C'] ) )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_adoption.loc[ n ,'M'] ) )
            #
        #
        elif str( base_configuration_adoption.loc[ n ,'Logistic'] ) == 'NO' and str( base_configuration_adoption.loc[ n ,'Linear'] ) == 'YES':
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ].update( {'Values':[], 'Type':'Linear', 'Restriction_Type':str( base_configuration_adoption.loc[ n ,'Restriction_Type'] ) } ) # WE MUST REMEMBER THE ORDER OF APPENDING THE PARAMETERS OF LINEAR BEHAVIOR: y_ini, v_2050
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( float( base_configuration_adoption.loc[ n ,'y_ini'] ) )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( base_configuration_adoption.loc[ n ,'v_2030'] )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( base_configuration_adoption.loc[ n ,'v_2040'] )
            adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ][ 'Values' ].append( base_configuration_adoption.loc[ n ,'v_2050'] )
            #
        #
        adoption_params[ base_configuration_adoption_unique_scenario_list[-1] ][ base_configuration_adoption_group_set_list[-1] ].update( {'Sector':store_the_sector} )
    #
    '''
    ##########################################################################
    '''
    transport_group_sets = list( Fleet_Groups.keys() )
    transport_group_sets = [ i for i in transport_group_sets if 'Train' not in i ]
    Reference_driven_distance = {}
    Reference_occupancy_rate = {}
    Reference_op_life = {}
    #
    for s in range( len( scenario_list ) ):
        Reference_driven_distance.update( { scenario_list[s]:{} } )
        Reference_occupancy_rate.update( { scenario_list[s]:{} } )
        Reference_op_life.update( { scenario_list[s]:{} } )
        for n in range( len( transport_group_sets ) ):
            this_set = transport_group_sets[n]
            #
            if scenario_list[s] in base_configuration_distance_unique_scenario_list or scenario_list[s] == ref_scenario:
                base_distance = Fleet_Groups_Distance[ Fleet_Groups[this_set][0] ] # the [0] helps call the detail fo distance per vehicle
                if scenario_list[s] != ref_scenario:
                    new_distance = deepcopy( interpolation_non_linear_final_flexible( time_range_vector, base_distance, distance_levers[scenario_list[s]][this_set], Initial_Year_of_Uncertainty ) )
                    new_distance_rounded = [ round(elem, 4) for elem in new_distance ]
                    Reference_driven_distance[ scenario_list[s] ].update( {this_set:new_distance_rounded} )
                else:
                    Reference_driven_distance[ scenario_list[s] ].update( {this_set:base_distance} )
            #
            if scenario_list[s] in base_configuration_or_unique_scenario_list or scenario_list[s] == ref_scenario:
                these_or_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ][ 't' ] ) if x == str( this_set ) ]
                base_or = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ these_or_indices[0]:these_or_indices[-1]+1 ] )
                base_or = [ float( base_or[j] ) for j in range( len( base_or ) ) ]
                if scenario_list[s] != ref_scenario:
                    new_or = deepcopy( interpolation_non_linear_final_flexible( time_range_vector, base_or, or_params[scenario_list[s]][this_set], Initial_Year_of_Uncertainty ) )
                    new_or_rounded = [ round(elem, 4) for elem in new_or ]
                    Reference_occupancy_rate[ scenario_list[s] ].update( {this_set:new_or_rounded} )
                else:
                    Reference_occupancy_rate[ scenario_list[s] ].update( {this_set:base_or} )
            #
        #
        for n in range(len(list(Fleet_Groups_inv.keys()))):
            this_set = list(Fleet_Groups_inv.keys())[n]
            if scenario_list[s] in base_configuration_distance_unique_scenario_list or scenario_list[s] == ref_scenario:  # includes distance scenarios
                these_ol_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'OperationalLife' ][ 't' ] ) if x == str( this_set ) ]
                base_ol = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OperationalLife' ]['value'][ these_ol_indices[0]:these_ol_indices[-1]+1 ] )
                base_ol = [ float( base_ol[j] ) for j in range( len( base_ol ) ) ]
                Reference_op_life[ scenario_list[s] ].update( {this_set:base_ol[0]} )
    #
    '''''
    ################################# PART 2 #################################
    '''''
    print('2: We will now manipulate each scenario for later printing of the .csv files in the same adress.')
    '''
    NOTES:
    i) The manipulation of the scenarios is done by taking the demand as reference and the orderly applying the modifications to the transport elements.
    ii) We first perform changes to the _Base_Dataset file to fix the errors found in the system.
    iii) We execute the changes in the scenario restrictions.
    '''
    Blend_Shares = {}
    for s in range( len( scenario_list ) ):
        Blend_Shares.update({scenario_list[s]:{}})
        #
    #
    for s in range( len( scenario_list ) ):
        #
        this_set_type_initial = S_DICT_sets_structure['initial'][ S_DICT_sets_structure['set'].index('TECHNOLOGY') ]
        capacity_variables = [ 'TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit' ]
        #
        if scenario_list[s] == 'BAU':
            relative_pkm_to_demand = { 'TotalAnnualMaxCapacity':{}, 'TotalTechnologyAnnualActivityLowerLimit':{} }
            relative_pkm_to_demand_nonrail = { 'TotalAnnualMaxCapacity':{}, 'TotalTechnologyAnnualActivityLowerLimit':{} }
            relative_tkm_to_demand = { 'TotalAnnualMaxCapacity':{}, 'TotalTechnologyAnnualActivityLowerLimit':{} }
            relative_tkm_to_demand_nonrail  = { 'TotalAnnualMaxCapacity':{}, 'TotalTechnologyAnnualActivityLowerLimit':{} }
        #
        ### Call the demand and go from there for restriciton definition ###
        this_set_type_initial = S_DICT_sets_structure['initial'][ S_DICT_sets_structure['set'].index('FUEL') ]
        passpub_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ this_set_type_initial ] ) if x == str( 'E6TDPASPUB' ) ]
        passpriv_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ this_set_type_initial ] ) if x == str( 'E6TDPASPRI' ) ]
        nonmotorized_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ this_set_type_initial ] ) if x == str( 'E6TRNOMOT' ) ]

        hfre_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ this_set_type_initial ] ) if x == str( 'E6TDFREHEA' ) ]
        lfre_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ this_set_type_initial ] ) if x == str( 'E6TDFRELIG' ) ]
        #
        # We will need to store the BAU data for later use.
        if scenario_list[s] == 'BAU':
            #
            passpub_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ passpub_range_indices[0]:passpub_range_indices[-1]+1 ] )
            passpriv_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ passpriv_range_indices[0]:passpriv_range_indices[-1]+1 ] )
            nonmotorized_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ nonmotorized_range_indices[0]:nonmotorized_range_indices[-1]+1 ] )
            #
            ref_fre_hea = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ hfre_range_indices[0]:hfre_range_indices[-1]+1 ] )
            ref_fre_lig = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ lfre_range_indices[0]:lfre_range_indices[-1]+1 ] )
            #
            Total_Demand = []
            Total_Demand_Fre = []
            for n in range( len( time_range_vector ) ):
                Total_Demand.append( float( passpub_values[n] ) + float( passpriv_values[n] ) + float ( nonmotorized_values[n] ) )
                Total_Demand_Fre.append( float( ref_fre_hea[n] ) + float( ref_fre_lig[n] ) )
            #
            ref_pass_pub_shares     = [ float(passpub_values[n])/Total_Demand[n] for n in range( len( time_range_vector ) ) ]
            ref_pass_priv_shares    = [ float(passpriv_values[n])/Total_Demand[n] for n in range( len( time_range_vector ) ) ]
            ref_nonmotorized_shares = [ float(nonmotorized_values[n])/Total_Demand[n] for n in range( len( time_range_vector ) ) ]
        #
        else:
            ###################################################################################################
            ### BLOCK 3: modify mode_shift ###
            applicable_sets_demand = []
            applicable_sets_tech = []
            for a_set in range( len( list( modeshift_params[ scenario_list[s] ].keys() ) ) ):
                this_set = list( modeshift_params[ scenario_list[s] ].keys() )[ a_set ]
                if modeshift_params[ scenario_list[s] ][ this_set ][ 'Context' ] == 'Demand':
                    applicable_sets_demand.append( this_set )
                elif modeshift_params[ scenario_list[s] ][ this_set ][ 'Context' ] == 'Technology':
                    applicable_sets_tech.append( this_set )

            # Now we perform the adjustment of the system, after having modified the demand:
            for a_set in range( len( applicable_sets_demand ) ): # FLAG: in the future we must consider non-logistic behaviors
                #
                this_set = applicable_sets_demand[ a_set ]
                if modeshift_params[ scenario_list[s] ][ this_set ][ 'Type' ] == 'Logistic':
                    #
                    R2021 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 0 ] # This is not used / remove in future versions.
                    R2050 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 1 ]
                    L =     modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 2 ]
                    C =     modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 3 ]
                    M =     modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 4 ]
                    #
                    r2050 = 1/R2050
                    Q =     L/C - 1
                    k =     np.log( (r2050-1)/Q )/(M-2050)
                    #
                    shift_years = [ n for n in range( Initial_Year_of_Uncertainty+1,2050+1 ) ]
                    shift_year_counter = 0
                    adoption_shift = []
                    #
                    for t in range( len( time_range_vector ) ):
                        if time_range_vector[t] > Initial_Year_of_Uncertainty:
                            x = int( shift_years[shift_year_counter] )
                            adoption_shift.append( generalized_logistic_curve(x, L, Q, k, M))
                            shift_year_counter += 1
                        else:
                            adoption_shift.append( 0.0 )
                        #
                    #
                #
                elif modeshift_params[ scenario_list[s] ][ this_set ][ 'Type' ] == 'Linear':
                    y_ini = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 0 ]
                    v_2030 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 1 ]
                    v_2040 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 2 ]                
                    v_2050 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 3 ]
                    #
                    x_coord_tofill, xp_coord_known, yp_coord_known = [], [], []
                    for y in range( len( time_range_vector ) ):
                        not_known_e = True
                        if time_range_vector[y] <= y_ini:
                            xp_coord_known.append( y )
                            yp_coord_known.append( 0 )
                            not_known_e = False
                        if v_2030 != 'interp' and time_range_vector[y] == 2030:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2030 )
                            not_known_e = False
                        if v_2040 != 'interp' and time_range_vector[y] == 2040:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2040 )
                            not_known_e = False
                        if v_2050 != 'interp' and time_range_vector[y] == 2050:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2050 )
                            not_known_e = False
                        if not_known_e == True:
                            x_coord_tofill.append( y )
                    #
                    y_coord_filled = list( np.interp( x_coord_tofill, xp_coord_known, yp_coord_known ) )
                    interpolated_values = []
                    for coord in range( len( time_range_vector ) ):
                        if coord in xp_coord_known:
                            value_index = xp_coord_known.index(coord)
                            interpolated_values.append( float( yp_coord_known[value_index] ) )
                        elif coord in x_coord_tofill:
                            value_index = x_coord_tofill.index(coord)
                            interpolated_values.append( float( y_coord_filled[value_index] ) )
                    #
                    adoption_shift = interpolated_values
                    #
                #
                if 'E6TDPASPUB' in this_set:
                    new_value_list_PUB = []
                elif 'E6TRNOMOT' in this_set:
                    new_value_list_NOMOT = []
                #
                for n in range( len( time_range_vector ) ):               
                    if 'E6TDPASPUB' in this_set: # we must subtract the rail activity and then add it again above
                        new_value_list_PUB.append( ( ref_pass_pub_shares[n] + adoption_shift[n] )*( Total_Demand[n] ) ) # - ref_value_range_RAILACTIVITY[n] )
                        new_value_list_PUB_rounded = [ round(elem, 4) for elem in new_value_list_PUB ]
                    elif 'E6TRNOMOT' in this_set:
                        new_value_list_NOMOT.append( ( adoption_shift[n] )*( Total_Demand[n] ) )
                        new_value_list_NOMOT_rounded = [ round(elem, 4) for elem in new_value_list_NOMOT ]
            #
            adjust_with_rail = False
            for a_set in range( len( applicable_sets_tech ) ): # REMEMBER THIS IS A CHANGE FUNCTION
                this_set = applicable_sets_tech[ a_set ]
                if 'Techs' not in this_set:
                    this_set_group = Fleet_Groups_inv[ this_set ]
                else:
                    this_set_group = this_set
                adjust_with_rail = True
                #
                # We need to call the group capacity
                this_set_group_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_set_group ) ]
                this_set_group_range_indices_lm = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) if x == str( this_set_group ) ]
                value_range_set_group = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_group_range_indices[0]:this_set_group_range_indices[-1]+1 ] )
                value_range_set_group = [ float(value_range_set_group[j]) for j in range( len( time_range_vector ) ) ]
                #
                # We also need the demand correspoding to this set:
                this_demand_set = Fleet_Groups_techs_2_dem[ this_set_group ]
                this_demand_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( this_demand_set ) ]
                this_demand_set_value = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'SpecifiedAnnualDemand' ]['value'][ this_demand_set_range_indices[0]:this_demand_set_range_indices[-1]+1 ] )
                this_demand_set_value = [ float(this_demand_set_value[j]) for j in range( len( time_range_vector ) ) ]
                #
                if modeshift_params[ scenario_list[s] ][ this_set ][ 'Type' ] == 'Linear':
                    y_ini = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 0 ]
                    v_2030 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 1 ]
                    v_2040 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 2 ]                
                    v_2050 = modeshift_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 3 ]
                    #
                    x_coord_tofill, xp_coord_known, yp_coord_known = [], [], []
                    for y in range( len( time_range_vector ) ):
                        not_known_e = True
                        if time_range_vector[y] <= y_ini:
                            xp_coord_known.append( y )
                            yp_coord_known.append( 0 )
                            not_known_e = False
                        if v_2030 != 'interp' and time_range_vector[y] == 2030:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2030 )
                            not_known_e = False
                        if v_2040 != 'interp' and time_range_vector[y] == 2040:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2040 )
                            not_known_e = False
                        if v_2050 != 'interp' and time_range_vector[y] == 2050:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2050 )
                            not_known_e = False
                        if not_known_e == True:
                            x_coord_tofill.append( y )
                    #
                    y_coord_filled = list( np.interp( x_coord_tofill, xp_coord_known, yp_coord_known ) )
                    interpolated_values = []
                    for coord in range( len( time_range_vector ) ):
                        if coord in xp_coord_known:
                            value_index = xp_coord_known.index(coord)
                            interpolated_values.append( float( yp_coord_known[value_index] ) )
                        elif coord in x_coord_tofill:
                            value_index = x_coord_tofill.index(coord)
                            interpolated_values.append( float( y_coord_filled[value_index] ) )
                    #
                    new_value_range_set_group = [ float( value_range_set_group[j] ) + interpolated_values[j]*this_demand_set_value[j] for j in range( len( time_range_vector ) ) ]
                    new_value_range_set_group_rounded = [ round(elem, 4) for elem in new_value_range_set_group ]
                    #
                    # Store the value of train rail (freight) below
                    if this_set == 'Techs_Trains_Freight':
                        stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_group_range_indices[0]:this_set_group_range_indices[-1]+1 ] = deepcopy( new_value_range_set_group_rounded )
                        stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ this_set_group_range_indices_lm[0]:this_set_group_range_indices_lm[-1]+1 ] = deepcopy( new_value_range_set_group_rounded )

                        for this_parameter in [ 'TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit' ]:
                            # We must adjust the capacity of the complementary set of *Techs_Trains_Freight*
                            this_set_complement_dict = {'Techs_Trains_Freight':'Techs_He_Freight'}
                            this_set_complement = this_set_complement_dict[this_set]
                            this_set_complement_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][ this_parameter ][ 't' ] ) if x == str( this_set_complement ) ]
                            value_list_complement = deepcopy( stable_scenarios[scenario_list[s]][ this_parameter ]['value'][ this_set_complement_indices[0]:this_set_complement_indices[-1]+1 ] )
                            value_list_complement = [ float(value_list_complement[j]) for j in range( len( time_range_vector ) ) ]

                            # Extract OR parameters:
                            or_group_tech_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'OutputActivityRatio' ][ 't' ] ) if x == str( this_set_complement ) ]
                            or_group_tech_values = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'OutputActivityRatio' ]['value'][ or_group_tech_indices[0]:or_group_tech_indices[-1]+1 ] )
                            or_group_tech_values = [ float( or_group_tech_values[j] ) for j in range( len( or_group_tech_values ) ) ]

                            # Define new heavy truck capacity
                            if this_parameter == 'TotalAnnualMaxCapacity':
                                security_multiplier_factor = 1.01
                            elif this_parameter == 'TotalTechnologyAnnualActivityLowerLimit':
                                security_multiplier_factor = 0.999

                            new_value_list_comp = []
                            for y in range(len(time_range_vector)):
                                if time_range_vector[y] < Initial_Year_of_Uncertainty:
                                    new_value_list_comp.append(value_list_complement[y])
                                else:
                                    new_value_list_comp.append( security_multiplier_factor*(this_demand_set_value[y] - new_value_range_set_group_rounded[y])/or_group_tech_values[y] )
                            # Store the value of trucks (after change) below
                            new_value_list_comp_rounded = [ round(elem, 4) for elem in new_value_list_comp ]
                            stable_scenarios[scenario_list[s]][ this_parameter ]['value'][ this_set_complement_indices[0]:this_set_complement_indices[-1]+1 ] = deepcopy( new_value_list_comp_rounded )
                #
                if modeshift_params[ scenario_list[s] ][ this_set ][ 'Type' ] == 'Built-in' and this_set == 'TRXTRAIELE':  # *ALERT* add the elimination of rail as a possible tool
                    this_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_set ) ]
                    value_range_set = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
                    value_range_set = [ float(value_range_set[j]) for j in range( len( time_range_vector ) ) ]
                    #
                    new_value_range_set_group = [ float( value_range_set_group[i] ) + float( value_range_set[i] ) for i in range( len( value_range_set ) ) ]
                    new_value_range_set_group_rounded = [ round(elem, 4) for elem in new_value_range_set_group ]
                    #
                    stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_group_range_indices[0]:this_set_group_range_indices[-1]+1 ] = deepcopy( new_value_range_set_group_rounded )
                    stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ this_set_group_range_indices_lm[0]:this_set_group_range_indices_lm[-1]+1 ] = deepcopy( new_value_range_set_group_rounded )
                #
                if modeshift_params[ scenario_list[s] ][ this_set ][ 'Type' ] == 'Linear' and this_set == 'TRXTRAIELE':  # *ALERT* add the elimination of rail as a possible tool
                    #
                    value_range_set_zero = [ 0.0 for j in range( len( time_range_vector ) ) ]
                    #
                    # Set zero for NDP (total capacity)
                    this_set_range_indices_max = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_set ) ]
                    this_set_range_indices_lower = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) if x == str( this_set ) ]
                    #
                    stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_range_indices_max[0]:this_set_range_indices_max[-1]+1 ] = deepcopy( value_range_set_zero )
                    stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ this_set_range_indices_lower[0]:this_set_range_indices_lower[-1]+1 ] = deepcopy( value_range_set_zero )
                    #
                    # Set zero for NDP (costs for passenger rail)
                    cost_sets_eliminate = \
                        ['TRANOMOTBike', 'TRANOMOTWalk', 'TRANPUB', 'TRANRAILINF', 'TRANRAILCAR']
                    for this_cost in cost_sets_eliminate:
                        this_set_range_indices_cost = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'CapitalCost' ][ 't' ] ) if x == str( this_cost ) ]
                        stable_scenarios[ scenario_list[ s ] ][ 'CapitalCost' ]['value'][ this_set_range_indices_cost[0]:this_set_range_indices_cost[-1]+1 ] = deepcopy( value_range_set_zero )
                    #
                    cost_sets_eliminate = ['TRANRAILINF']
                    for this_cost in cost_sets_eliminate:
                        this_set_range_indices_cost = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'FixedCost' ][ 't' ] ) if x == str( this_cost ) ]
                        stable_scenarios[ scenario_list[ s ] ][ 'FixedCost' ]['value'][ this_set_range_indices_cost[0]:this_set_range_indices_cost[-1]+1 ] = deepcopy( value_range_set_zero )
                    #
                    # Re-establish BAU for NDP (group capacity)
                    this_set_range_indices_bau = [ i for i, x in enumerate( stable_scenarios[ 'BAU' ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_set_group ) ]
                    value_range_set = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_range_indices_bau[0]:this_set_range_indices_bau[-1]+1 ] )
                    value_range_set = [ float(value_range_set[j]) for j in range( len( time_range_vector ) ) ]
                    stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_group_range_indices[0]:this_set_group_range_indices[-1]+1 ] = deepcopy( value_range_set )
                    stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ this_set_group_range_indices_lm[0]:this_set_group_range_indices_lm[-1]+1 ] = deepcopy( value_range_set )
            #
            new_value_list_PRIV = [ Total_Demand[n] - new_value_list_PUB_rounded[n] - new_value_list_NOMOT_rounded[n] for n in range( len( time_range_vector ) ) ]
            new_value_list_PRIV_rounded = [ round(elem, 4) for elem in new_value_list_PRIV ]
            #
            # Assign parameters back: for these subset of uncertainties
            stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ passpub_range_indices[0]:passpub_range_indices[-1]+1 ] = deepcopy( new_value_list_PUB_rounded )
            stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ passpriv_range_indices[0]:passpriv_range_indices[-1]+1 ] = deepcopy( new_value_list_PRIV_rounded )
            stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ nonmotorized_range_indices[0]:nonmotorized_range_indices[-1]+1 ] = deepcopy( new_value_list_NOMOT_rounded )
            #
        #
        ### BLOCK 4: call and modify the occupancy rate ###
        this_set_type_initial = S_DICT_sets_structure['initial'][ S_DICT_sets_structure['set'].index('TECHNOLOGY') ]
        if scenario_list[s] == 'BAU':
            ref_or_values = {}
        #
        for g in range( len( transport_group_sets ) ):
            or_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ][ this_set_type_initial ] ) if x == str( transport_group_sets[g] ) ]
            #
            if scenario_list[s] == 'BAU':
                or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                ref_or_values.update( { transport_group_sets[g]:or_values } )
            #
            else:
                #
                new_value_list = deepcopy( interpolation_non_linear_final_flexible( time_range_vector, ref_or_values[ transport_group_sets[g] ] , or_params[ scenario_list[s] ][ transport_group_sets[g] ], Initial_Year_of_Uncertainty ) )
                new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] = deepcopy( new_value_list_rounded )
        #
        ### BLOCK 5: call and re-establish the capacity variables of group techs after modal shift change AND occupancy rate change ###
        this_set_type_initial = S_DICT_sets_structure['initial'][ S_DICT_sets_structure['set'].index('TECHNOLOGY') ]
        capacity_variables = [ 'TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit' ]
        #
        # We must call the group techs and calculate the passenger kilometers provided by each tech, then store the share relative to the demand
        for capvar in range( len( capacity_variables ) ):
            #
            for g in range( len( group_tech_PRIVATE ) ):
                #
                cap_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( group_tech_PRIVATE[g] ) ]
                or_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ][ this_set_type_initial ] ) if x == str( group_tech_PRIVATE[g] ) ]
                demand_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( Fleet_Groups_techs_2_dem[ group_tech_PRIVATE[g] ] ) ]
                #
                # here we quickly call the occupancy rates
                or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                #
                # here we quickly call the associated demand
                demand_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                demand_values = [ float( demand_values[j] ) for j in range( len( demand_values ) ) ]
                #
                cap_values = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] )
                cap_values = [ float( cap_values[j] ) for j in range( len( cap_values ) ) ]
                #
                if scenario_list[s] == 'BAU': # REMEMBER THE VARIABLES OF BAU DO NOT CHANGE
                    #
                    this_pkm_share = [ cap_values[n]*or_values[n]/demand_values[n] for n in range( len( time_range_vector ) ) ]
                    this_pkm_share_rounded = [ round(elem, 4) for elem in this_pkm_share ]
                    #
                    relative_pkm_to_demand[ capacity_variables[capvar] ].update( { group_tech_PRIVATE[g]:this_pkm_share_rounded } )
                #
                else: # if scenario_list[s] in ['NDP','NDP_A','OP15C']: # we must apply the same distribution of transport in pkm as in the BAU, considering the new demands. The variable to modify is the capacity.
                    #
                    apply_these_shares = relative_pkm_to_demand[ capacity_variables[capvar] ][ group_tech_PRIVATE[g] ]
                    new_cap_values = [ apply_these_shares[n]*demand_values[n]/or_values[n] for n in range( len( time_range_vector ) ) ]
                    new_cap_values_rounded = [ round(elem, 4) for elem in new_cap_values ]
                    #
                    stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] = deepcopy( new_cap_values_rounded )
                    #
                #
            #----------------------------------------------------------------------------------------------------------------------------------------------------------
            for g in range( len( group_tech_PUBLIC ) ):
                #
                cap_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( group_tech_PUBLIC[g] ) ]
                or_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ][ this_set_type_initial ] ) if x == str( group_tech_PUBLIC[g] ) ]
                demand_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( Fleet_Groups_techs_2_dem[ group_tech_PUBLIC[g] ] ) ]
                #
                cap_values = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] )
                cap_values = [ float( cap_values[j] ) for j in range( len( cap_values ) ) ]
                #
                if scenario_list[s] == 'BAU':
                    #
                    or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                    or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                    #
                    # here we quickly call the associated demand
                    demand_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                    demand_values = [ float( demand_values[j] ) for j in range( len( demand_values ) ) ]
                    #
                    this_pkm_share = [ cap_values[n]*or_values[n]/demand_values[n] for n in range( len( time_range_vector ) ) ]
                    this_pkm_share_rounded = [ round(elem, 4) for elem in this_pkm_share ]
                    #
                    relative_pkm_to_demand[ capacity_variables[capvar] ].update( { group_tech_PUBLIC[g]:deepcopy( this_pkm_share_rounded ) } )
                    #
                    if 'Train' not in group_tech_PUBLIC[g]: # we need to find the shares of non-rail modes:
                        cap_indices_rail = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( 'Techs_Trains' ) ]
                        cap_values_rail = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices_rail[0]:cap_indices_rail[-1]+1 ] )
                        cap_values_rail = [ float( cap_values_rail[j] ) for j in range( len( cap_values_rail ) ) ]
                        demand_values_norail = [ demand_values[j] - cap_values_rail[j] for j in range( len( demand_values ) ) ]
                        #
                        this_pkm_share = [ cap_values[n]*or_values[n]/demand_values_norail[n] for n in range( len( time_range_vector ) ) ]
                        this_pkm_share_rounded = [ round(elem, 4) for elem in this_pkm_share ]
                        #
                        relative_pkm_to_demand_nonrail[ capacity_variables[capvar] ].update( { group_tech_PUBLIC[g]:this_pkm_share_rounded } )
                    #
                #
                else: # we must apply the same distribution of transport in pkm as in the BAU, considering the new demands. The variable to modify is the capacity.
                    #
                    if adjust_with_rail == False:
                        or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                        or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                        #
                        # here we quickly call the associated demand
                        demand_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                        demand_values = [ float( demand_values[j] ) for j in range( len( demand_values ) ) ]
                        #
                        apply_these_shares = relative_pkm_to_demand[ capacity_variables[capvar] ][ group_tech_PUBLIC[g] ]
                        new_cap_values = [ apply_these_shares[n]*demand_values[n]/or_values[n] for n in range( len( time_range_vector ) ) ]
                        new_cap_values_rounded = [ round(elem, 4) for elem in new_cap_values ]
                        #
                        stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] = deepcopy( new_cap_values_rounded )
                    #
                    elif 'Train' not in group_tech_PUBLIC[g]:
                        or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                        or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                        #
                        # here we quickly call the associated demand
                        cap_indices_rail = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( 'Techs_Trains' ) ]
                        cap_values_rail = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices_rail[0]:cap_indices_rail[-1]+1 ] )
                        cap_values_rail = [ float( cap_values_rail[j] ) for j in range( len( cap_values_rail ) ) ]
                        demand_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                        demand_values_norail = [ demand_values[j] - cap_values_rail[j] for j in range( len( demand_values ) ) ]
                        #
                        apply_these_shares = relative_pkm_to_demand_nonrail[ capacity_variables[capvar] ][ group_tech_PUBLIC[g] ]
                        new_cap_values = [ apply_these_shares[n]*demand_values_norail[n]/or_values[n] for n in range( len( time_range_vector ) ) ]
                        new_cap_values_rounded = [ round(elem, 4) for elem in new_cap_values ]
                        #
                        stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] = deepcopy( new_cap_values_rounded )
                    #
                #
            #----------------------------------------------------------------------------------------------------------------------------------------------------------
            for g in range( len( group_tech_FREIGHT_HEA ) ):
                #
                cap_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( group_tech_FREIGHT_HEA[g] ) ]
                or_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ][ this_set_type_initial ] ) if x == str( group_tech_FREIGHT_HEA[g] ) ]
                demand_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( Fleet_Groups_techs_2_dem[ group_tech_FREIGHT_HEA[g] ] ) ]
                # here we quickly call the associated demand
                demand_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                demand_values = [ float( demand_values[j] ) for j in range( len( demand_values ) ) ]
                #
                cap_values = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] )
                cap_values = [ float( cap_values[j] ) for j in range( len( cap_values ) ) ]
                #
                if scenario_list[s] == 'BAU':
                    #
                    or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                    or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                    #
                    this_tkm_share = [ cap_values[n]*or_values[n]/demand_values[n] for n in range( len( time_range_vector ) ) ]
                    this_tkm_share_rounded = [ round(elem, 4) for elem in this_tkm_share ]
                    #
                    relative_tkm_to_demand[ capacity_variables[capvar] ].update( { group_tech_FREIGHT_HEA[g]:deepcopy( this_tkm_share_rounded ) } )
                    #
                    if 'Train' not in group_tech_FREIGHT_HEA[g]: # we need to find the shares of non-rail modes:
                        cap_indices_rail = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( 'Techs_Trains_Freight' ) ]
                        cap_values_rail = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices_rail[0]:cap_indices_rail[-1]+1 ] )
                        cap_values_rail = [ float( cap_values_rail[j] ) for j in range( len( cap_values_rail ) ) ]
                        demand_values_norail = [ demand_values[j] - cap_values_rail[j] for j in range( len( demand_values ) ) ]
                        #
                        this_tkm_share = [ cap_values[n]*or_values[n]/demand_values_norail[n] for n in range( len( time_range_vector ) ) ]
                        this_tkm_share_rounded = [ round(elem, 4) for elem in this_tkm_share ]
                        #
                        relative_tkm_to_demand_nonrail[ capacity_variables[capvar] ].update( { group_tech_FREIGHT_HEA[g]:this_tkm_share_rounded } )
                    #
                #
                else: # we must apply the same distribution of transport in pkm as in the BAU, considering the new demands. The variable to modify is the capacity.
                    #
                    if adjust_with_rail == False:
                        or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                        or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                        #
                        apply_these_shares = relative_tkm_to_demand[ capacity_variables[capvar] ][ group_tech_FREIGHT_HEA[g] ]
                        new_cap_values = [ apply_these_shares[n]*demand_values[n]/or_values[n] for n in range( len( time_range_vector ) ) ]
                        new_cap_values_rounded = [ round(elem, 4) for elem in new_cap_values ]
                        #
                        stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] = deepcopy( new_cap_values_rounded )
                    #
                    elif 'Train' not in group_tech_FREIGHT_HEA[g]:
                        or_values = deepcopy( stable_scenarios[ scenario_list[s] ][ 'OutputActivityRatio' ]['value'][ or_indices[0]:or_indices[-1]+1 ] )
                        or_values = [ float( or_values[j] ) for j in range( len( or_values ) ) ]
                        #
                        # here we quickly call the associated demand
                        cap_indices_rail = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ][ this_set_type_initial ] ) if x == str( 'Techs_Trains_Freight' ) ]
                        cap_values_rail = deepcopy( stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices_rail[0]:cap_indices_rail[-1]+1 ] )
                        cap_values_rail = [ float( cap_values_rail[j] ) for j in range( len( cap_values_rail ) ) ]
                        demand_values_norail = [ demand_values[j] - cap_values_rail[j] for j in range( len( demand_values ) ) ]
                        #
                        apply_these_shares = relative_tkm_to_demand_nonrail[ capacity_variables[capvar] ][ group_tech_FREIGHT_HEA[g] ]
                        new_cap_values = [ apply_these_shares[n]*demand_values_norail[n]/or_values[n] for n in range( len( time_range_vector ) ) ]
                        new_cap_values_rounded = [ round(elem, 4) for elem in new_cap_values ]
                        #
                        stable_scenarios[ scenario_list[s] ][ capacity_variables[capvar] ]['value'][ cap_indices[0]:cap_indices[-1]+1 ] = deepcopy( new_cap_values_rounded )

        #########################################################################################
        ### BLOCK 6: modify demand ###
        if scenario_list[s] in list(set(base_configuration_transport_elasticity['Scenario'].tolist())):            
            ''' MODIFYING *base_configuration_transport_elasticity* '''
            this_scenario_df = deepcopy( base_configuration_transport_elasticity.loc[ base_configuration_transport_elasticity['Scenario'].isin( [ scenario_list[s] ] ) ] )
            #
            set_list_group_dict = {'Passenger':['E6TDPASPRI', 'E6TDPASPUB', 'E6TRNOMOT'],
                                   'Freight':['E6TDFREHEA', 'E6TDFRELIG']}
            #
            set_list_group = list( set( this_scenario_df[ 'Set' ].tolist() ) )
            #
            unique_demand_list = []
            unique_demand = {}
            #
            elasticity_Params_built_in_all = list(set(this_scenario_df['Built-in Parameter-Set'].tolist()))[0]
            elasticity_Params_reference_all = list(set(this_scenario_df['Reference'].tolist()))[0]
            elasticity_Params_method_all = list(set(this_scenario_df['Method'].tolist()))[0]
            elasticity_Params_setIndex_all = list(set(this_scenario_df['Set_Index'].tolist()))[0]
            #
            for l0 in range( len( set_list_group ) ):
                this_scenario_tech_df = this_scenario_df.loc[ this_scenario_df['Set'] == set_list_group[l0] ]
                set_list = set_list_group_dict[set_list_group[l0]]
                #
                for l in range( len( set_list ) ):
                    param_list = list( set( this_scenario_tech_df[ 'Parameter' ].tolist() ) )
                    for p in range( len( param_list ) ):
                        this_scenario_tech_param_df = this_scenario_tech_df.loc[ this_scenario_tech_df['Parameter'] == param_list[p] ]
                        #
                        elasticity_Params_built_in  = this_scenario_tech_param_df['Built-in Parameter-Set'].tolist()[0]
                        elasticity_Params_reference = this_scenario_tech_param_df['Reference'].tolist()[0]
                        elasticity_Params_method    = this_scenario_tech_param_df['Method'].tolist()[0]
                        elasticity_Params_setIndex    = this_scenario_tech_param_df['Set_Index'].tolist()[0]
                        #
                        if elasticity_Params_method == 'Exact': # only modify demands and capacities if this is turned on
                            value_list_num = []
                            this_index = this_scenario_tech_param_df.index.tolist()[0]
                            for y in range( len( time_range_vector ) ):
                                value_list_num.append( this_scenario_tech_param_df.loc[ this_index, time_range_vector[y] ] )
                            #
                            if set_list_group[l0] == 'Passenger':
                                value_list_mult = [value_list_num[i]/Total_Demand[i] for i in range(len(value_list_num))]
                            elif set_list_group[l0] == 'Freight':
                                value_list_mult = [value_list_num[i]/Total_Demand_Fre[i] for i in range(len(value_list_num))]
                            #
                            # OBTAINED VALUES, NOW PRINTING
                            if elasticity_Params_built_in == 'YES':
                                this_param_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ param_list[p] ][ elasticity_Params_setIndex ] ) if x == str( set_list[l] ) ]
                                value_list = deepcopy( stable_scenarios[ scenario_list[s] ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] )
                                value_list = [float(e) for e in value_list]
                                #
                                if set_list[l] not in unique_demand_list:
                                    unique_demand_list.append(set_list[l])
                                    unique_demand.update({set_list[l]:deepcopy(value_list)})
                                #
                                new_value_list = [ round( value_list[e]*value_list_mult[e], 4 ) for e in range(len(value_list)) ]
                                stable_scenarios[ scenario_list[s] ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] = deepcopy( new_value_list )
            #
            # Below we must adjust capacities:
            if elasticity_Params_method_all == 'Exact':
                Sets_Involved = ['Techs_He_Freight', 'Techs_Li_Freight', 'Techs_Trains_Freight', 'Techs_SUVMIV', 'Techs_Sedan', 'Techs_Motos', 'Techs_Buses', 'Techs_Microbuses', 'Techs_Taxis']
                params_to_adjust = [ 'TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit' ]
                for par in range( len( params_to_adjust ) ):
                    for a_set in range( len( Sets_Involved ) ):
                        this_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ params_to_adjust[par] ][ 't' ] ) if x == str( Sets_Involved[ a_set ] ) ]
                        value_list = deepcopy( stable_scenarios[ scenario_list[s] ][ params_to_adjust[par] ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
                        value_list = [ float( value_list[j] ) for j in range( len( value_list ) ) ]
                        #
                        '''
                        demand_indices_BASE = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( Fleet_Groups_techs_2_dem[ Sets_Involved[ a_set ] ] ) ]
                        demand_list_BASE = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices_BASE[0]:demand_indices_BASE[-1]+1 ] )
                        demand_list_BASE = [ float(demand_list_BASE[j]) for j in range(len(demand_list_BASE)) ]
                        '''
                        #
                        demand_list_BASE = unique_demand[str( Fleet_Groups_techs_2_dem[ Sets_Involved[ a_set ] ] )]
                        #
                        demand_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( Fleet_Groups_techs_2_dem[ Sets_Involved[ a_set ] ] ) ]
                        demand_list = deepcopy( stable_scenarios[ scenario_list[s] ][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                        #
                        if 'PUB' in str( Fleet_Groups_techs_2_dem[ Sets_Involved[ a_set ] ] ):
                            # let's extract rail capacity to adjust this apropiately
                            train_pass_capacity_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( 'Techs_Trains' ) ]
                            train_pass_capacity_values = stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'][ train_pass_capacity_indices[0]:train_pass_capacity_indices[-1]+1 ]
                            if Fleet_Groups_techs_2_dem[ Sets_Involved[ a_set ] ] == 'E6TDPASPUB' and scenario_list[ s ] == 'NDP':
                                subtract_list = [float(train_pass_capacity_values[j]) for j in range(len(train_pass_capacity_values))]
                            else:
                                subtract_list = [0 for j in range(len(train_pass_capacity_values))]
                            #
                            new_value_list_old_base = deepcopy( value_list )
                            new_value_list = []
                            for n in range( len( new_value_list_old_base ) ):
                                if n < index_2024:
                                    new_value_list.append( new_value_list_old_base[n] )
                                else:
                                    new_value_list.append( (new_value_list_old_base[n]-subtract_list[n])*(demand_list[n]/demand_list_BASE[n]) )
                                    new_value_list[-1] += subtract_list[n]
                            new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                        else:
                            new_value_list_old_base = deepcopy( value_list )
                            new_value_list = [ new_value_list_old_base[n]*(demand_list[n]/demand_list_BASE[n]) for n in range( len( new_value_list_old_base ) )]
                            new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                        #
                        stable_scenarios[ scenario_list[s] ][ params_to_adjust[par] ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] = deepcopy(new_value_list_rounded)

        #print('---------------------------')
        #print('block 7')
        ##print(scenario_list[s], len(stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityUpperLimit' ][ 't' ]))
        ##print(scenario_list[s], len(stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityUpperLimit' ][ 'value' ]))
        #print(scenario_list[s], len(stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ][ 't' ]))
        #print(scenario_list[s], len(stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ][ 'value' ]))
        #print('---------------------------')

        # This is necessary to lose the restrictions we already defined
        unique_max_cap_techs = list( set( stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) )
        unique_low_lim_techs = list( set( stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) )
        ignore_techs = ['TRANRAILFREINF',  'TRANOMOTWalk', 'TRANOMOTBike',
                        'TRXTRAIELE', 'TRXTRAIFREELE', 'TRANRAILINF', 'TRANPUB', 'TRANRAILCAR']
        rewrite_techs_maxcap = \
            [e for e in unique_max_cap_techs if
             'TR' in e and 'IN' not in e and e not in ignore_techs]
        rewrite_techs_lowlim = \
            [e for e in unique_low_lim_techs if
             'TR' in e and 'IN' not in e and e not in ignore_techs]

        # Let's adjust existing restrictions to new capacities (transport sector);
        # First, max capacity:
        for t in range(len(rewrite_techs_maxcap)):
            this_set = rewrite_techs_maxcap[t]
            group_tech_set = Fleet_Groups_inv[ this_set ]

            group_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( group_tech_set ) ]
            group_value_list = stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'][ group_set_range_indices[0]:group_set_range_indices[-1]+1 ]
            group_value_list = [ float( group_value_list[j] ) for j in range( len( group_value_list ) ) ]

            set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_set ) ]

            freeze_group_set_range_indices = [ i for i, x in enumerate( stable_scenarios_freeze[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( group_tech_set ) ]
            freeze_group_value_list = stable_scenarios_freeze[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'][ freeze_group_set_range_indices[0]:freeze_group_set_range_indices[-1]+1 ]
            freeze_group_value_list = [ float( freeze_group_value_list[j] ) for j in range( len( freeze_group_value_list ) ) ]

            freeze_set_range_indices = [ i for i, x in enumerate( stable_scenarios_freeze[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_set ) ]
            freeze_value_list = stable_scenarios_freeze[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'][ freeze_set_range_indices[0]:freeze_set_range_indices[-1]+1 ]
            freeze_value_list = [ float( freeze_value_list[j] ) for j in range( len( freeze_value_list ) ) ]

            value_list = [1.01*group_value_list[i]*freeze_value_list[i]/freeze_group_value_list[i] for i in range(len(group_value_list))]
            value_list_rounded = [ round(elem, 4) for elem in value_list ]
            stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'][ set_range_indices[0]:set_range_indices[-1]+1 ] = deepcopy(value_list_rounded)

        # Second, lower limit:
        for t in range(len(rewrite_techs_lowlim)):
            this_set = rewrite_techs_lowlim[t]
            group_tech_set = Fleet_Groups_inv[ this_set ]

            group_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) if x == str( group_tech_set ) ]
            group_value_list = stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ group_set_range_indices[0]:group_set_range_indices[-1]+1 ]
            group_value_list = [ float( group_value_list[j] ) for j in range( len( group_value_list ) ) ]

            set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) if x == str( this_set ) ]

            freeze_group_set_range_indices = [ i for i, x in enumerate( stable_scenarios_freeze[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) if x == str( group_tech_set ) ]
            freeze_group_value_list = stable_scenarios_freeze[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ freeze_group_set_range_indices[0]:freeze_group_set_range_indices[-1]+1 ]
            freeze_group_value_list = [ float( freeze_group_value_list[j] ) for j in range( len( freeze_group_value_list ) ) ]

            freeze_set_range_indices = [ i for i, x in enumerate( stable_scenarios_freeze[ scenario_list[ s ] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) if x == str( this_set ) ]
            freeze_value_list = stable_scenarios_freeze[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ freeze_set_range_indices[0]:freeze_set_range_indices[-1]+1 ]
            freeze_value_list = [ float( freeze_value_list[j] ) for j in range( len( freeze_value_list ) ) ]

            value_list = [0.999*group_value_list[i]*freeze_value_list[i]/freeze_group_value_list[i] for i in range(len(group_value_list))]
            value_list_rounded = [ round(elem, 4) for elem in value_list ]
            stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityLowerLimit' ]['value'][ set_range_indices[0]:set_range_indices[-1]+1 ] = deepcopy(value_list)

        ### BLOCK 7: define the *vehicle/ind_tech fuel tech* composition for each scenario ###
        # NOTE: check whether the scenario is contained in the system dictionary:
        if scenario_list[s] in list( set( list( adoption_params.keys() ) ) ):
            applicable_sets = []
            for a_set in range( len( list( adoption_params[ scenario_list[s] ].keys() ) ) ):
                this_set = list( adoption_params[ scenario_list[s] ].keys() )[ a_set ]
                applicable_sets.append( this_set )

            # Now we perform the adjustment of the system, after having modified the demand:
            for a_set in range( len( applicable_sets ) ):
                #
                ### x1 = len(stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityUpperLimit' ][ 't' ])
                ### x2 = len(stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityUpperLimit' ][ 'value' ])
                ### print('happens??', a_set, applicable_sets[a_set], x1/x2)

                this_set = applicable_sets[ a_set ]
                this_sector = adoption_params[ scenario_list[s] ][ this_set ][ 'Sector' ]
                #
                this_param = adoption_params[ scenario_list[s] ][ this_set ][ 'Restriction_Type' ]
                #
                this_type = adoption_params[ scenario_list[s] ][ this_set ][ 'Type' ]
                #
                if this_param == 'Min/Max' and this_sector == 'Transport':
                    cap_vars = [ 'TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit' ]
                if this_param == 'Min/Max' and this_sector == 'Industry':
                    cap_vars = [ 'TotalTechnologyAnnualActivityUpperLimit', 'TotalTechnologyAnnualActivityLowerLimit' ]
                if this_param == 'Min':
                    cap_vars = [ 'TotalTechnologyAnnualActivityLowerLimit' ]
                if this_param == 'Max' and this_sector == 'Transport':
                    cap_vars = [ 'TotalAnnualMaxCapacity']
                if this_param == 'Max' and this_sector == 'Industry':
                    cap_vars = [ 'TotalTechnologyAnnualActivityUpperLimit']
                #########################################################################################
                # Here, let's select the groups:
                if this_sector == 'Transport':
                    group_tech_set = Fleet_Groups_inv[ this_set ]
                elif this_sector == 'Industry':
                    group_tech_set = Ind_Groups_inv[ this_set ]
                #
                #########################################################################################
                if this_type == 'Linear':
                    y_ini  = adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 0 ] # This is not used / remove in future versions.
                    v_2030 = adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 1 ]
                    v_2040 = adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 2 ]
                    v_2050 = adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 3 ]
                    #
                    known_years_ini = [e for e in range(2018, int(y_ini)+1)]
                    known_years = known_years_ini + [2030, 2040, 2050 ]
                    #2030
                    try:
                        float_v2030 = float(v_2030)
                    except Exception:
                        float_v2030 = 'interp'
                    #2040
                    try:
                        float_v2040 = float(v_2040)
                    except Exception:
                        float_v2040 = 'interp' 
                    #2050
                    try:
                        float_v2050 = float(v_2050)
                    except Exception:    
                        float_v2050 = 'interp'
                    #
                    ### if this_sector == 'Industry':
                    # Here we must know the initial share (extracting the group values):
                    group_set_range_indices = [ i for i, x in enumerate(stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityLowerLimit']['t']) if x == str(group_tech_set)]
                    group_value_list = stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityLowerLimit']['value'][group_set_range_indices[0]:group_set_range_indices[-1]+1]
                    group_value_list = [ float( group_value_list[j] ) for j in range( len( group_value_list ) ) ]

                    this_set_range_indices = [ i for i, x in enumerate(stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityLowerLimit']['t']) if x == str(this_set)]
                    if len( this_set_range_indices ) != 0:
                        value_list = stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityLowerLimit']['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ]
                        value_list = [ float( value_list[j] ) for j in range( len( value_list ) ) ]
                        known_value_ini = []
                        for y in range( len( time_range_vector ) ):
                            if time_range_vector[y] <= y_ini:
                                known_value_ini.append(value_list[y]/group_value_list[y])
                                #
                            #
                        #
                    #
                    else:  # If there is no prior restriction, we star from zero.
                        known_value_ini = []
                        for y in range( len( time_range_vector ) ):
                            if time_range_vector[y] <= y_ini:
                                known_value_ini.append(0)
                                #
                            #
                        #
                    #
                    #
                    ### else:  # Let's not change anything for transport (this works well by design)
                    ###     known_value_ini = []
                    ###     for y in range( len( time_range_vector ) ):
                    ###         if time_range_vector[y] <= y_ini:
                    ###             known_value_ini.append(0)
                    ###             #
                    ###         #
                    ###     #
                    #
                    known_values = known_value_ini + [float_v2030, float_v2040, float_v2050 ]
                    #
                    x_coord_tofill, xp_coord_known, yp_coord_known = [], [], []
                    for y in range( len( time_range_vector ) ):
                        not_known_e = True
                        if time_range_vector[y] <= y_ini:
                            xp_coord_known.append( y )
                            yp_coord_known.append( known_value_ini[y] )
                            not_known_e = False
                        if v_2030 != 'interp' and time_range_vector[y] == 2030:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2030 )
                            not_known_e = False
                        if v_2040 != 'interp' and time_range_vector[y] == 2040:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2040 )
                            not_known_e = False
                        if v_2050 != 'interp' and time_range_vector[y] == 2050:
                            xp_coord_known.append( y )
                            yp_coord_known.append( v_2050 )
                            not_known_e = False
                        if not_known_e == True:
                            x_coord_tofill.append( y )
                    #
                    y_coord_filled = list( np.interp( x_coord_tofill, xp_coord_known, yp_coord_known ) )
                    interpolated_values = []
                    for coord in range( len( time_range_vector ) ):
                        if coord in xp_coord_known:
                            value_index = xp_coord_known.index(coord)
                            interpolated_values.append( float( yp_coord_known[value_index] ) )
                        elif coord in x_coord_tofill:
                            value_index = x_coord_tofill.index(coord)
                            interpolated_values.append( float( y_coord_filled[value_index] ) )
                    #
                    adoption_shift = interpolated_values
                    #
                #
                if this_type == 'Logistic':
                    R2021 = adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 0 ] # This is not used / remove in future versions.
                    R2050 = adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 1 ]
                    L =     adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 2 ]
                    C =     adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 3 ]
                    M =     adoption_params[ scenario_list[s] ][ this_set ][ 'Values' ][ 4 ]
                    #
                    r2050 = 1/R2050
                    Q =     L/C - 1
                    k =     np.log( (r2050-1)/Q )/(M-2050)
                    #
                    shift_years = [ n for n in range( Initial_Year_of_Uncertainty+1,2050+1 ) ]
                    shift_year_counter = 0
                    adoption_shift = []
                    #
                    for t in range( len( time_range_vector ) ):
                        if time_range_vector[t] > Initial_Year_of_Uncertainty:
                            x = int( shift_years[shift_year_counter] )
                            adoption_shift.append( generalized_logistic_curve(x, L, Q, k, M))
                            shift_year_counter += 1
                        else:
                            adoption_shift.append( 0.0 )
                #########################################################################################
                #
                for cp in range( len( cap_vars ) ):
                    #
                    if cap_vars[cp] in ['TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityUpperLimit']:
                        security_multiplier_factor = 1.001 # 1.0001
                    elif cap_vars[cp] == 'TotalTechnologyAnnualActivityLowerLimit':
                        security_multiplier_factor = 0.999 # 0.9999
                    #
                    group_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ cap_vars[cp] ][ 't' ] ) if x == str( group_tech_set ) ]
                    group_value_list = stable_scenarios[ scenario_list[s] ][ cap_vars[cp] ]['value'][ group_set_range_indices[0]:group_set_range_indices[-1]+1 ]
                    group_value_list = [ float( group_value_list[j] ) for j in range( len( group_value_list ) ) ]
                    #**********************************************************************
                    if this_type == 'Linear':
                        if 999 in known_values:
                            indices_999 = [ i for i, x in enumerate( known_values ) if x != float( 999 ) ]
                            max_known_years = known_years[ max( indices_999 ) ]
                            for y in range( len( time_range_vector ) ):
                                if cap_vars[cp] == 'TotalAnnualMaxCapacity' and time_range_vector[y] > max_known_years:
                                    adoption_shift[y] = 1
                                elif cap_vars[cp] == 'TotalTechnologyAnnualActivityLowerLimit' and time_range_vector[y] > max_known_years:
                                    adoption_shift[y] = 0

                    #**********************************************************************
                    new_value_list = []
                    for n in range( len( time_range_vector ) ):
                        new_value_list.append( security_multiplier_factor*adoption_shift[n]*group_value_list[n] )
                        new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                    #
                    this_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ cap_vars[cp] ][ 't' ] ) if x == str( this_set ) ]
                    if len( this_set_range_indices ) != 0:
                        stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] = deepcopy(new_value_list_rounded)
                        # print('happens??', this_set, this_sector, scenario_list[s], cap_vars[cp])
                    else: # this means we need to add the data to the dictionary
                        # print('happens??', this_set, this_sector, scenario_list[s], cap_vars[cp])
                        for y in range( len( time_range_vector ) ):
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['r'].append( 'CR' )
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['t'].append( this_set )
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['y'].append( str( time_range_vector[y] ) )
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['value'].append( new_value_list_rounded[y] )
            #
            # This section makes the code have coherent restrictions for transport:
            if scenario_list[s] != 'BAU':
                cap_vars = [ 'TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit' ]
                for cp in range( len( cap_vars ) ):
                    all_sets = list( set( stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['t'] ) )
                    all_sets.sort()
                    ref_dict = deepcopy( stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ] )
                    stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['r'] = []
                    stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['t'] = []
                    stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['y'] = []
                    stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['value'] = []
                    for t in range( len( all_sets ) ):
                        ###if all_sets[t] in applicable_sets or all_sets[t][:2] != 'TR':
                        if ((all_sets[t] in applicable_sets or all_sets[t][:2] != 'TR') or
                            (all_sets[t] in rewrite_techs_lowlim and all_sets[t] not in applicable_sets and cap_vars[cp] == 'TotalTechnologyAnnualActivityLowerLimit') or
                            (all_sets[t] in rewrite_techs_maxcap and all_sets[t] not in applicable_sets and cap_vars[cp] == 'TotalAnnualMaxCapacity')):
                            this_set_range_indices = [ i for i, x in enumerate( ref_dict[ 't' ] ) if x == str( all_sets[t] ) ]
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['r'] += deepcopy( ref_dict['r'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['t'] += deepcopy( ref_dict['t'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['y'] += deepcopy( ref_dict['y'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
                            stable_scenarios[ scenario_list[s] ][ cap_vars[ cp ] ]['value'] += deepcopy( ref_dict['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
            #


        ### # DEBUG BLOCK BEFORE:
        ### if 'NDPMC7A3' == scenario_list[s]:
        ###     print('DEBUG SECTION 1')
        ###     this_set = 'TRSEDGSL'
        ###     this_set_group = Fleet_Groups_inv[ this_set ]
        ###     
        ###     # 1) distances:
        ###     xdistances = Reference_driven_distance[ scenario_list[s] ][ this_set_group ]
        ###     xdistances_bau = Reference_driven_distance[ 'BAU' ][ this_set_group ]
        ###     
        ###     # 2)
        ###     this_param = 'TotalAnnualMaxCapacity'
        ###     this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set_group) ]
        ###     this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###     this_param_values_maxcapgroup = deepcopy(this_param_values)
        ### 
        ###     # 3)
        ###     this_param = 'TotalTechnologyAnnualActivityLowerLimit'
        ###     this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set_group) ]
        ###     this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###     this_param_values_lowlimgroup = deepcopy(this_param_values)
        ### 
        ###     # 4)
        ###     #this_param = 'TotalAnnualMaxCapacity'
        ###     #this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###     #this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###     #this_param_values_maxcap = deepcopy(this_param_values)
        ### 
        ###     # 5)
        ###     this_param = 'TotalTechnologyAnnualActivityLowerLimit'
        ###     this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###     this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###     this_param_values_lowlim = deepcopy(this_param_values)
        ### 
        ###     # 6)
        ###     this_param = 'ResidualCapacity'
        ###     this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###     this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###     this_param_values_rescap = deepcopy(this_param_values)
        ### 
        ###     # 7)
        ###     this_param = 'CapitalCost'
        ###     this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###     this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###     this_param_values_capcost = deepcopy(this_param_values)
        ### 
        ###     #print:
        ###     print('1 distances:', xdistances)
        ###     print('2 distances_bau:', xdistances_bau)
        ###     print('3 TotalAnnualMaxCapacity (group):', this_param_values_maxcapgroup)
        ###     print('4 TotalTechnologyAnnualActivityLowerLimit (group):', this_param_values_lowlimgroup)
        ###     #print('TotalAnnualMaxCapacity:', this_param_values_maxcap)
        ###     print('5 TotalTechnologyAnnualActivityLowerLimit:', this_param_values_lowlim)
        ###     print('6 ResidualCapacity:', this_param_values_rescap)
        ###     print('7 CapitalCost:', this_param_values_capcost)

        ### BLOCK 8: Adjust all paramters for distance change ### // we do not apply this to BAU // here the occupancy rate AND the modal shift were already adjusted
        # parameters_involved = ['CapitalCost','FixedCost','ResidualCapacity','TotalAnnualMaxCapacity','TotalTechnologyAnnualActivityLowerLimit']
        parameters_involved = ['CapitalCost','FixedCost','TotalAnnualMaxCapacity','TotalTechnologyAnnualActivityLowerLimit','ResidualCapacity']
        #
        if scenario_list[s] != 'BAU': # we proceed to adjust first the parameters and corresponding sets affected by distance, then the demands.
            for p in range(len(parameters_involved)):
                this_parameter = parameters_involved[p]
                if p == 0:
                    dem_adj_public = True
                    dem_adj_private = True
                    dem_adj_heafre = True
                    dem_adj_ligfre = True
        
                for a_set in range( len( transport_group_sets ) ):
                    # Distance is a parameter that is not in Osemosys directly, but is implicit in multiple parameters.
                    # Now, we proceed to estimate the change in the curve of distance across futures. Note that this modification does not depend on the baseline values.
                    #
                    this_set_type_initial = S_DICT_sets_structure['initial'][ S_DICT_sets_structure['set'].index('TECHNOLOGY') ]
                    #
                    this_group_set = transport_group_sets[a_set] # these are GROUP TECHS, please do not forget
                    #
                    base_distance = Reference_driven_distance[ ref_scenario ][this_group_set]
                    new_distance = Reference_driven_distance[ scenario_list[s] ][this_group_set]

                    # the demand adjustment is done first:
                    this_demand_set = Fleet_Groups_techs_2_dem[ this_group_set ]
                    if ((this_demand_set == 'E6TDPASPRI' and dem_adj_private is True) or
                        (this_demand_set == 'E6TDPASPUB' and dem_adj_public is True) or
                        (this_demand_set == 'E6TDFREHEA' and dem_adj_heafre is True) or
                        (this_demand_set == 'E6TDFRELIG' and dem_adj_ligfre is True)):
        
                        # let's extract rail capacity to adjust this apropiately
                        train_pass_capacity_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( 'Techs_Trains' ) ]
                        train_pass_capacity_values = stable_scenarios[scenario_list[s]][ 'TotalAnnualMaxCapacity' ]['value'][ train_pass_capacity_indices[0]:train_pass_capacity_indices[-1]+1 ]
                        if Fleet_Groups_techs_2_dem[ this_group_set ] == 'E6TDPASPUB' and scenario_list[ s ] == 'NDP':
                            subtract_list = [float(train_pass_capacity_values[j]) for j in range(len(train_pass_capacity_values))]
                        else:
                            subtract_list = [0 for j in range(len(train_pass_capacity_values))]
        
                        demand_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( this_demand_set ) ]
                        demand_list = deepcopy( stable_scenarios[scenario_list[s]][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                        demand_list = [float(i) for i in demand_list]
                        #
                        new_value_list = []
                        for n in range( len( demand_list ) ):
                            if n < index_2024:
                                new_value_list.append( demand_list[n] )
                            else:
                                new_value_list.append( (demand_list[n]-subtract_list[n])*new_distance[n]/base_distance[n] )
                                new_value_list[-1] += subtract_list[n]
                        new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                        #
                        stable_scenarios[scenario_list[s]][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] = deepcopy(new_value_list_rounded)
                        #                                       
                        if this_demand_set == 'E6TDPASPRI':
                            demand_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][ 'SpecifiedAnnualDemand' ][ 'f' ] ) if x == str( 'E6TRNOMOT' ) ]
                            demand_list = deepcopy( stable_scenarios[scenario_list[s]][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] )
                            #
                            new_value_list = []
                            for n in range( len( demand_list ) ):
                                if n < index_2024:
                                    new_value_list.append( demand_list[n] )
                                else:
                                    new_value_list.append( demand_list[n]*new_distance[n]/base_distance[n] )
                            new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                            #
                            stable_scenarios[scenario_list[s]][ 'SpecifiedAnnualDemand' ]['value'][ demand_indices[0]:demand_indices[-1]+1 ] = deepcopy(new_value_list_rounded)
                            dem_adj_private = False
                            #
                        if this_demand_set == 'E6TDPASPUB':
                            dem_adj_public = False
                            #
                        if this_demand_set == 'E6TDFREHEA':
                            dem_adj_heafre = False
                            #
                        if this_demand_set == 'E6TDFRELIG':
                            dem_adj_ligfre = False

                    # group-tech capacity adjustments are done second:
                    if ('Techs_' in this_group_set and this_parameter in ['TotalAnnualMaxCapacity', 'TotalTechnologyAnnualActivityLowerLimit'] ): # THIS CONDITION WILL ALWAYS BE TRUE
                        #
                        this_set_range_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][ this_parameter ][ this_set_type_initial ] ) if x == str( this_group_set ) ]
                        #
                        if len(this_set_range_indices) != 0:
                            # The obtained distance change is used appropiately from here on (...)
                            # We must proceed with the group set IF the parameter is adequate:
                            value_list = deepcopy( stable_scenarios[scenario_list[s]][ this_parameter ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
                            value_list = [ float(value_list[j]) for j in range( len(value_list) ) ]
                            #
                            new_value_list = []
                            for n in range( len( value_list ) ):
                                if n < index_2024:
                                    new_value_list.append( value_list[n] )
                                else:
                                    new_value_list.append( value_list[n]*new_distance[n]/base_distance[n] )
                            #
                            new_value_list_rounded = [ round(elem, 4) for elem in new_value_list ]
                            stable_scenarios[scenario_list[s]][ this_parameter ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] = deepcopy( new_value_list_rounded )
        
                            if this_group_set == 'Techs_He_Freight' and scenario_list[s] != 'BAU':  # here we need to adjust the capacity of freight rail for consistency
                                tsri_frerail = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][ this_parameter ][ this_set_type_initial ] ) if x == str( 'Techs_Trains_Freight' ) ]
                                value_list_frerail = deepcopy( stable_scenarios[scenario_list[s]][ this_parameter ]['value'][ tsri_frerail[0]:tsri_frerail[-1]+1 ] )
                                value_list_frerail = [ float(value_list_frerail[j]) for j in range( len(value_list_frerail) ) ]
                                #
                                new_value_list_frerail = []
                                for n in range( len( value_list_frerail ) ):
                                    new_value_list_frerail.append( value_list_frerail[n]*new_distance[n]/base_distance[n] )
                                #
                                new_value_list_frerail_rounded = [ round(elem, 4) for elem in new_value_list_frerail ]
                                stable_scenarios[scenario_list[s]][ this_parameter ]['value'][ tsri_frerail[0]:tsri_frerail[-1]+1 ] = deepcopy( new_value_list_frerail_rounded )

                    '''
                    # Me must act upon the parameters that get affected by the distance change. We must the read the scenario and extract a list of the technologies that require the change.
                    for g in range( len( transport_group_sets ) ):
                        #
                        this_group_set = transport_group_sets[g]
                        #
                        base_distance = Reference_driven_distance[ ref_scenario ][this_group_set]
                        new_distance = Reference_driven_distance[ scenario_list[s] ][this_group_set]
                        #
                    '''
                    # specific-tech capacity adjustments are done third:
                    specific_techs = Fleet_Groups[ this_group_set ]
                    # Let us attack the 02 techs:
                    for n in range( len( specific_techs ) ):
                        #
                        tech_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ this_parameter ][ 't' ] ) if x == str( specific_techs[n] ) ]
                        if len( tech_indices ) != 0:
                            tech_values = deepcopy( stable_scenarios[ scenario_list[ s ] ][ this_parameter ]['value'][ tech_indices[0]:tech_indices[-1]+1 ] )
                            tech_values = [ float( tech_values[j] ) for j in range( len( tech_values ) ) ]
                            #
                            if 'Cost' not in this_parameter:
                                adjustment_factor = \
                                    [new_distance[z]/base_distance[z] for z in range(len(tech_values))]
                            else:
                                adjustment_factor = \
                                    [(new_distance[z]/base_distance[z])**(-1) for z in range(len(tech_values))]
                            tech_values_new = [ tech_values[z]*(adjustment_factor[z]) for z in range(len(tech_values))]
                            #
                            tech_values_new_rounded = [ round(elem, 4) for elem in tech_values_new ]
                            # if this_parameter == 'TotalAnnualMaxCapacity': # this avoids issues with the capacity of the vehicles
                            #     print( specific_techs[n] )
                            #     tech_values_new_rounded = deepcopy( interp_max_cap( tech_values_new_rounded ) )
                            stable_scenarios[ scenario_list[ s ] ][ this_parameter ]['value'][ tech_indices[0]:tech_indices[-1]+1 ] = deepcopy( tech_values_new_rounded )

        #### DEBUG BLOCK AFTER:
        ###if 'NDPMC7A3' == scenario_list[s]:
        ###    print('\n')
        ###    print('DEBUG SECTION 2')
        ###    this_set = 'TRSEDGSL'
        ###    this_set_group = Fleet_Groups_inv[ this_set ]
        ###    
        ###    # 1) distances:
        ###    xdistances = Reference_driven_distance[ scenario_list[s] ][ this_set_group ]
        ###    xdistances_bau = Reference_driven_distance[ 'BAU' ][ this_set_group ]
        ###    
        ###    # 2)
        ###    this_param = 'TotalAnnualMaxCapacity'
        ###    this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set_group) ]
        ###    this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###    this_param_values_maxcapgroup = deepcopy(this_param_values)
        ###
        ###    # 3)
        ###    this_param = 'TotalTechnologyAnnualActivityLowerLimit'
        ###    this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set_group) ]
        ###    this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###    this_param_values_lowlimgroup = deepcopy(this_param_values)
        ###
        ###    # 4)
        ###    #this_param = 'TotalAnnualMaxCapacity'
        ###    #this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###    #this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###    #this_param_values_maxcap = deepcopy(this_param_values)
        ###
        ###    # 5)
        ###    this_param = 'TotalTechnologyAnnualActivityLowerLimit'
        ###    this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###    this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###    this_param_values_lowlim = deepcopy(this_param_values)
        ###
        ###    # 6)
        ###    this_param = 'ResidualCapacity'
        ###    this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###    this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###    this_param_values_rescap = deepcopy(this_param_values)
        ###
        ###    # 7)
        ###    this_param = 'CapitalCost'
        ###    this_param_indices = [ i for i, x in enumerate( stable_scenarios[scenario_list[s]][this_param][ 't' ] ) if x == str(this_set) ]
        ###    this_param_values = stable_scenarios[scenario_list[s]][this_param]['value'][this_param_indices[0]:this_param_indices[-1]+1]
        ###    this_param_values_capcost = deepcopy(this_param_values)
        ###
        ###    #print:
        ###    print('1 distances:', xdistances)
        ###    print('2 distances_bau:', xdistances_bau)
        ###    print('3 TotalAnnualMaxCapacity (group):', this_param_values_maxcapgroup)
        ###    print('4 TotalTechnologyAnnualActivityLowerLimit (group):', this_param_values_lowlimgroup)
        ###    #print('TotalAnnualMaxCapacity:', this_param_values_maxcap)
        ###    print('5 TotalTechnologyAnnualActivityLowerLimit:', this_param_values_lowlim)
        ###    print('6 ResidualCapacity:', this_param_values_rescap)
        ###    print('7 CapitalCost:', this_param_values_capcost)
        ###    sys.exit()


        #
        #***********************************************************************************************
        #if scenario_list[s] != 'BAU':
        for g in range( len( transport_group_sets ) ): # this actually avoids the maxcap issue
            this_group_set = transport_group_sets[g]
            this_set_range_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ][ this_set_type_initial ] ) if x == str( this_group_set ) ]
            value_list = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] )
            value_list = [ 1.01*float(value_list[j]) for j in range( len(value_list) ) ]
            #
            new_value_list_rounded = [ round(elem, 4) for elem in value_list ]
            new_value_list_rounded = deepcopy( interp_max_cap( new_value_list_rounded ) )
            #
            stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_set_range_indices[0]:this_set_range_indices[-1]+1 ] = deepcopy( new_value_list_rounded )
        #***********************************************************************************************
        #'''
        # Let's define rules to limit the adoption of technology in the early years:
        unique_residual_cap_techs = list( set( stable_scenarios[ scenario_list[s] ][ 'ResidualCapacity' ][ 't' ] ) )
        unique_max_cap_techs = list( set( stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) )
        unique_low_lim_techs = list( set( stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityLowerLimit' ][ 't' ] ) )
        #
        for g in range( len( transport_group_sets ) ): # this actually avoids the maxcap issue
            this_group_set = transport_group_sets[g]
            this_tech_set_list = Fleet_Groups[ this_group_set ]
            #
            this_g_tech_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ][ 't' ] ) if x == str( this_group_set ) ]
            this_g_tech_values = stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'][ this_g_tech_indices[0]:this_g_tech_indices[-1]+1 ]
            #
            for t in range( len( this_tech_set_list ) ):
                this_tech = this_tech_set_list[t]
                #
                if this_tech in unique_residual_cap_techs and this_tech not in unique_max_cap_techs:
                    this_res_tech_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[s] ][ 'ResidualCapacity' ][ 't' ] ) if x == str( this_tech ) ]
                    this_res_tech_values = stable_scenarios[ scenario_list[s] ][ 'ResidualCapacity' ]['value'][ this_res_tech_indices[0]:this_res_tech_indices[-1]+1 ]
                    this_res_tech_values = [ float( this_res_tech_values[j] ) for j in range( len( this_res_tech_values ) ) ]
                    
                    ### print( scenario_list[s], this_tech, 'here1', len(scenario_list) )
                    
                    #
                    for y in range( len( time_range_vector ) ):
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['r'].append( 'CR' )
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['t'].append( this_tech )                            
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['y'].append( str( time_range_vector[y] ) )
                        if time_range_vector[y] <= Initial_Year_of_Uncertainty:
                            stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( this_g_tech_values[y] )
                        else:
                            stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( 99 ) # this 99 is a top that is hardly ever reached

                elif this_tech not in unique_residual_cap_techs and this_tech not in unique_max_cap_techs and this_tech not in unique_low_lim_techs: # or ('LPG' in this_tech and 'He' in this_group_set):
                    #
                    ### print( '*', scenario_list[s], this_tech, 'here2', len(scenario_list) )
                    
                    for y in range( len( time_range_vector ) ):
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['r'].append( 'CR' )
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['t'].append( this_tech )                            
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['y'].append( str( time_range_vector[y] ) )
                        if time_range_vector[y] <= Initial_Year_of_Uncertainty:
                            stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( 0 )
                        else:
                            stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( 99 ) # this 99 is a top that is hardly ever reached
        #
        unique_min_cap_techs = list( set( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMinCapacity' ][ 't' ] ) )
        for t in range( len( unique_min_cap_techs ) ):
            this_tech = unique_min_cap_techs[t]
            
            this_min_tech_indices = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMinCapacity' ][ 't' ] ) if x == str( this_tech ) ]
            this_min_tech_values = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'TotalAnnualMinCapacity' ]['value'][ this_min_tech_indices[0]:this_min_tech_indices[-1]+1 ] )
            this_min_tech_values = [ float( this_min_tech_values[j] ) for j in range( len( this_min_tech_values ) ) ]
            
            for y in range( len( time_range_vector ) ):
                stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['r'].append( 'CR' )
                stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['t'].append( this_tech )                            
                stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['y'].append( str( time_range_vector[y] ) )
                stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( str( this_min_tech_values[y] ) )

        ### BLOCK 9: makes the code have coherent restrictions for industry // applies for any scenario:
        ul_all_sets = list( set( stable_scenarios[ scenario_list[s] ][ 'TotalTechnologyAnnualActivityUpperLimit' ]['t'] ) )
        ul_ind_sets = [e for e in ul_all_sets if 'IN' in e]  # these techs have a CAPEX
        ul_ind_sets.sort()
        for t in range( len( ul_ind_sets ) ):
            this_set = ul_ind_sets[t]
            # Check residual capacity for the techs
            set_range_indices = [ i for i, x in enumerate(stable_scenarios[scenario_list[s]]['ResidualCapacity']['t']) if x == str(this_set)]
            if len(set_range_indices) != 0:  # you can work here
                value_list = stable_scenarios[scenario_list[s]]['ResidualCapacity']['value'][set_range_indices[0]:set_range_indices[-1]+1]
                value_list = [ float( value_list[j] ) for j in range( len( value_list ) ) ]
                base_max_cap = value_list[0]
            else:
                base_max_cap = 0
            #
            # Check capacity factor
            cap_set_range_indices = [ i for i, x in enumerate(stable_scenarios[scenario_list[s]]['CapacityFactor']['t']) if x == str(this_set)]
            if len(cap_set_range_indices) != 0:  # you can work here
                cap_value_list = stable_scenarios[scenario_list[s]]['CapacityFactor']['value'][cap_set_range_indices[0]:cap_set_range_indices[-1]+1]
                cap_value_list = [ float( cap_value_list[j] ) for j in range( len( cap_value_list ) ) ]
            else:
                cap_value_list = [1 for y in range( len( time_range_vector ) )]
            # gather the capacity of the group technologies
            group_tech_set = Ind_Groups_inv[ this_set ]
            group_set_range_indices = [ i for i, x in enumerate(stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityUpperLimit']['t']) if x == str(group_tech_set)]
            group_value_list = stable_scenarios[scenario_list[s]]['ResidualCapacity']['value'][group_set_range_indices[0]:group_set_range_indices[-1]+1]
            group_value_list = [ float( group_value_list[j] ) for j in range( len( group_value_list ) ) ]
            #
            # Translate activity upper limits to max capacity.
            cap_2_act = [31.536*e for e in cap_value_list]  # act = cap_2_act * cap // 0.99 is a security
            ul_set_range_indices = [ i for i, x in enumerate(stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityUpperLimit']['t']) if x == str(this_set)]
            ul_value_list = stable_scenarios[scenario_list[s]]['TotalTechnologyAnnualActivityUpperLimit']['value'][ul_set_range_indices[0]:ul_set_range_indices[-1]+1]
            ul_value_list = [ float( ul_value_list[j] ) for j in range( len( ul_value_list ) ) ]
            ul_value_list_cap = [ul_value_list[e]/cap_2_act[e] for e in range(len(ul_value_list))]
            ul_value_list_cap_rounded = \
                [ 1.02*e for e in ul_value_list_cap ]
            #
            if base_max_cap > ul_value_list_cap_rounded[0]:
                ul_value_list_cap_rounded_freeze = deepcopy(ul_value_list_cap_rounded)
                for y in range( len( time_range_vector ) ):
                    ul_value_list_cap_rounded[y] += base_max_cap - ul_value_list_cap_rounded_freeze[0]
            #
            if len(ul_set_range_indices) != 0:
                freeze_value = 0
                for y in range( len( time_range_vector ) ):
                    stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['r'].append( 'CR' )
                    stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['t'].append( this_set )
                    stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['y'].append( str( time_range_vector[y] ) )
                    if (ul_value_list_cap_rounded[y] < ul_value_list_cap_rounded[y-1]) and y != 0:
                        if freeze_value < ul_value_list_cap_rounded[y-1]:
                            freeze_value = deepcopy(ul_value_list_cap_rounded[y-1])
                        else:
                            pass
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( freeze_value )
                    else:
                        stable_scenarios[ scenario_list[s] ][ 'TotalAnnualMaxCapacity' ]['value'].append( ul_value_list_cap_rounded[y] )
                        #
                    #
                #
            #
            #if 'INOPGELE' == this_set:
            #    sys.exit()
            #
        #
        #'''
        #***********************************************************************************************
        ### BLOCK 10: Integrate biofuels according to RECOPE / *we must use a new interpolation function*.
        #  Note: the biodiesel blend will affect all the sectors, not only transport.
        if scenario_list[s] != 'BAU': # GENERALIZE THIS LATER.
            #
            Diesel_Techs = [
                'T4DSL_HEA',
                'T4DSL_LIG',
                'T4DSL_PRI',
                'T4DSL_PUB']
            #
            Diesel_Techs_Emissions = {
                'T4DSL_HEA':[ 'CO2e_Freight', 'CO2e_HeavyCargo', 'CO2e' ],
                'T4DSL_LIG':[ 'CO2e_Freight', 'CO2e_LightCargo', 'CO2e' ],
                'T4DSL_PRI':[ 'CO2e' ],
                'T4DSL_PUB':[ 'CO2e' ] }
            #
            Gasoline_Techs = [
                'T4GSL_LIG',
                'T4GSL_PRI',
                'T4GSL_PUB',
                'DIST_GSL' ]
            #
            Gasoline_Techs_Emissions = {
                'T4GSL_LIG':[ 'CO2e_Freight', 'CO2e_LightCargo', 'CO2e' ],
                'T4GSL_PRI':[ 'CO2e' ],
                'T4GSL_PUB':[ 'CO2e' ],
                'DIST_GSL':['CO2e_sources'] }
            #
            # 10.1. Let us adjust for diesel and biodiesel: (remember to use  *time_range_vector*)
            for n in range( len( Diesel_Techs ) ):
                #
                Blend_Shares[ scenario_list[s] ].update( { Diesel_Techs[n]:{} } )
                #
                for n2 in range( len( Diesel_Techs_Emissions[ Diesel_Techs[n] ] ) ):
                    this_tech_emission_indices_diesel = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ][ 't' ] ) if x == Diesel_Techs[n] ]
                    this_tech_emission_indices_emission = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ][ 'e' ] ) if x == Diesel_Techs_Emissions[ Diesel_Techs[n] ][n2] ]
                    #
                    r_index = set(this_tech_emission_indices_diesel) & set(this_tech_emission_indices_emission)
                    this_tech_emission_indices = list( r_index )
                    this_tech_emission_indices.sort()
                    #
                    value_list = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ]['value'][ this_tech_emission_indices[0]:this_tech_emission_indices[-1]+1 ] )
                    value_list = [ float(value_list[j]) for j in range( len(value_list) ) ]
                    #
                    start_blend_point = [2026, 1]
                    final_blend_point = [2030, 5]
                    new_value_list_rounded, biofuel_shares = interpolation_blend( start_blend_point, 'None', final_blend_point, value_list, time_range_vector )
                    #
                    stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ]['value'][ this_tech_emission_indices[0]:this_tech_emission_indices[-1]+1 ] = deepcopy( new_value_list_rounded )
                    #
                    Blend_Shares[ scenario_list[s] ][  Diesel_Techs[n] ].update( { Diesel_Techs_Emissions[ Diesel_Techs[n] ][n2]: deepcopy( biofuel_shares ) } )
                    #
                #
            #
            # 10.2. Let us adjust for gasoline and ethanol: (remember to use  *time_range_vector*)
            for n in range( len( Gasoline_Techs ) ):
                #
                Blend_Shares[ scenario_list[s] ].update( { Gasoline_Techs[n]:{} } )
                #
                for n2 in range( len( Gasoline_Techs_Emissions[ Gasoline_Techs[n] ] ) ):
                    this_tech_emission_indices_gasoline = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ][ 't' ] ) if x == Gasoline_Techs[n] ]
                    this_tech_emission_indices_emission = [ i for i, x in enumerate( stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ][ 'e' ] ) if x == Gasoline_Techs_Emissions[ Gasoline_Techs[n] ][n2] ]
                    #
                    r_index = set(this_tech_emission_indices_gasoline) & set(this_tech_emission_indices_emission)
                    this_tech_emission_indices = list( r_index )
                    this_tech_emission_indices.sort()
                    #
                    value_list = deepcopy( stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ]['value'][ this_tech_emission_indices[0]:this_tech_emission_indices[-1]+1 ] )
                    value_list = [ float(value_list[j]) for j in range( len(value_list) ) ]
                    #
                    start_blend_point = [2020, 2]
                    mid_blend_point = [2021, 4]
                    final_blend_point = [2022, 8]
                    new_value_list_rounded, biofuel_shares = interpolation_blend( start_blend_point, mid_blend_point, final_blend_point, value_list, time_range_vector )
                    #
                    stable_scenarios[ scenario_list[ s ] ][ 'EmissionActivityRatio' ]['value'][ this_tech_emission_indices[0]:this_tech_emission_indices[-1]+1 ] = deepcopy( new_value_list_rounded )
                    #
                    Blend_Shares[ scenario_list[s] ][  Gasoline_Techs[n] ].update( { Gasoline_Techs_Emissions[ Gasoline_Techs[n] ][n2]:biofuel_shares } )

    print('  finished the standard adjustment, now to processing')

    # print('check 0')
    # sys.exit()

    '''
    # We must create the *Based_On* parameters:
        * Affects:
            - base_configuration_electrical
            - base_configuration_E_and_D
    '''
    for sb in range( len( scenario_list_based ) ):
        if scenario_list_based[sb] != 'ref':
            this_scenario_name = scenario_list_all[sb]
            stable_scenarios.update( { this_scenario_name:{} } )
            stable_scenarios[ this_scenario_name ] = deepcopy( stable_scenarios[ scenario_list_based[sb] ] )
            #
            if scenario_list_based[sb] != 'BAU':
                Blend_Shares.update( { this_scenario_name:Blend_Shares[ scenario_list_based[sb] ] } )
            else:
                Blend_Shares.update( { this_scenario_name:Blend_Shares[ 'NDP' ] } )
            Reference_driven_distance.update( { this_scenario_name:Reference_driven_distance[ scenario_list_based[sb] ] } )
            Reference_occupancy_rate.update( { this_scenario_name:Reference_occupancy_rate[ scenario_list_based[sb] ] } )
            Reference_op_life.update( { this_scenario_name:Reference_op_life[ scenario_list_based[sb] ] } )
    #
    with open('Blend_Shares_0.pickle', 'wb') as handle:
        pickle.dump(Blend_Shares, handle, protocol=pickle.HIGHEST_PROTOCOL)
    handle.close()

    #print('check')
    #sys.exit()

    scenario_list_all.sort()
    for sb in range( len( scenario_list_all ) ):
        this_scenario_name = scenario_list_all[sb]
        #
        #########################################################################################
        ''' MODIFYING *base_configuration_electrical* '''
        local_application_iter = ['All', this_scenario_name]
        for iter_scen in local_application_iter:
            this_scenario_df = deepcopy( base_configuration_electrical.loc[ base_configuration_electrical['Scenario'].isin( [ iter_scen ] ) ] )
            #
            set_list = list( set( this_scenario_df[ 'Tech_Set' ].tolist() ) )
            for l in range( len( set_list ) ):
                this_scenario_tech_df = this_scenario_df.loc[ this_scenario_df['Tech_Set'] == set_list[l] ]
                #
                param_list = list( set( this_scenario_tech_df[ 'Parameter' ].tolist() ) )
                for p in range( len( param_list ) ):
                    this_scenario_tech_param_df = this_scenario_tech_df.loc[ this_scenario_tech_df['Parameter'] == param_list[p] ]
                    #
                    electrical_Params_built_in      = this_scenario_tech_param_df['Built-in Parameter-Set'].tolist()[0].replace(' ','')
                    electrical_Params_linear        = this_scenario_tech_param_df['Linear'].tolist()[0].replace(' ','')
                    electrical_Params_exactYears    = this_scenario_tech_param_df['Exact_Years'].astype(str).tolist()[0].replace(' ','')
                    electrical_Params_exactValues   = this_scenario_tech_param_df['Exact_Values'].astype(str).tolist()[0].replace(' ','')
                    electrical_Params_initialYear   = this_scenario_tech_param_df['y_ini'].tolist()[0]
                    electrical_Params_mYears        = this_scenario_tech_param_df['Milestone_Years'].astype(str).tolist()[0].replace(' ','')
                    electrical_Params_mValues       = this_scenario_tech_param_df['Milestone_Value'].astype(str).tolist()[0].replace(' ','')
                    electrical_Params_Unit          = this_scenario_tech_param_df['Unit'].tolist()[0].replace(' ','')
                    electrical_Params_methods       = this_scenario_tech_param_df['Method'].tolist()[0].replace(' ','')
                    #
                    electrical_Params_secMultiplier = this_scenario_tech_param_df['Security_Multiplier'].tolist()[0]
                    #
                    electrical_Params_exactYears    = electrical_Params_exactYears.split( ';' )
                    electrical_Params_exactValues   = electrical_Params_exactValues.split( ';' )
                    electrical_Params_mYears        = electrical_Params_mYears.split( ';' )
                    electrical_Params_mValues       = electrical_Params_mValues.split( ';' )
                    electrical_Params_methods       = electrical_Params_methods.split( ';' )
                    #
                    # Let us create the value vector when the parameter is not built in:
                    if electrical_Params_built_in == 'NO':
                        if 'Interpolate_Escalate' in electrical_Params_methods and 'Fix_Last' in electrical_Params_methods and 'intact' not in electrical_Params_exactYears:
                            last_electrical_Params_exactValues = deepcopy( electrical_Params_exactValues[-1] )
    
                            for i in range( int( electrical_Params_exactYears[-1] )+1, int( electrical_Params_mYears[0] ) ):
                                electrical_Params_exactYears += [ i ]
                                electrical_Params_exactValues += [ last_electrical_Params_exactValues ]
        
                            known_years     = [ float(e) for e in electrical_Params_exactYears ] + [ float(e) for e in electrical_Params_mYears ]
                            known_values     = [ float(e) for e in electrical_Params_exactValues ] + [ float(e) for e in electrical_Params_mValues ]
                            value_list = linear_interpolation_time_series( time_range_vector, known_years, known_values )
    
                        if 'Interpolate' in electrical_Params_methods and 'Fix_Last' in electrical_Params_methods and 'intact' not in electrical_Params_exactYears:
                            known_years     = [ float(e) for e in electrical_Params_exactYears ] + [ float(e) for e in electrical_Params_mYears ]
                            known_values     = [ float(e) for e in electrical_Params_exactValues ] + [ float(e) for e in electrical_Params_mValues ]
                            value_list = linear_interpolation_time_series( time_range_vector, known_years, known_values )
    
                        if 'Fix_Indicated' in electrical_Params_methods and 'intact' not in electrical_Params_exactYears:
                            known_years     = [ float(e) for e in electrical_Params_exactYears ] +  [ electrical_Params_initialYear ]
                            known_values     = [ float(e) for e in electrical_Params_exactValues ] + [ float( electrical_Params_mValues[0] ) ]
                            value_list = linear_interpolation_time_series( time_range_vector, known_years, known_values )
    
                        if 'Write' in electrical_Params_methods:
                            value_list = [ round( e*electrical_Params_secMultiplier, 4 ) for e in value_list ]
                            for y in range( len( time_range_vector ) ):
                                stable_scenarios[ this_scenario_name ][ param_list[p] ]['r'].append( 'CR' )
                                stable_scenarios[ this_scenario_name ][ param_list[p] ]['t'].append( set_list[l] )                            
                                stable_scenarios[ this_scenario_name ][ param_list[p] ]['y'].append( str( time_range_vector[y] ) )
                                stable_scenarios[ this_scenario_name ][ param_list[p] ]['value'].append( float( value_list[y] ) )
    
                    # Let us modify the value vector if it already exists:
                    if electrical_Params_built_in == 'YES':
                        this_param_indices = [ i for i, x in enumerate( stable_scenarios[ this_scenario_name ][ param_list[p] ][ 't' ] ) if x == str( set_list[l] ) ]
                        this_param_values = deepcopy( stable_scenarios[ this_scenario_name ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] )
                        #
                        if 'Interpolate' in electrical_Params_methods and 'intact' in electrical_Params_exactYears:
                            known_years = [ y for y in time_range_vector if y <= electrical_Params_initialYear ]
                            known_values = [ float( this_param_values[y] ) for y in range( len(time_range_vector) ) if time_range_vector[y] <= electrical_Params_initialYear ]
                            known_years += [ float(e) for e in electrical_Params_mYears ]
                            known_values += [ float(e) for e in electrical_Params_mValues ]
                            value_list = linear_interpolation_time_series( time_range_vector, known_years, known_values )
                        #
                        if 'Interpolate' in electrical_Params_methods and 'Fix_Last' in electrical_Params_methods and 'intact' not in electrical_Params_exactYears:
                            known_years     = [ float(e) for e in electrical_Params_exactYears ] + [ float(e) for e in electrical_Params_mYears ]
                            known_values     = [ float(e) for e in electrical_Params_exactValues ] + [ float(e) for e in electrical_Params_mValues ]
                            value_list = linear_interpolation_time_series( time_range_vector, known_years, known_values )
                        #
                        if 'Overwrite' in electrical_Params_methods:
                            value_list = [ round( e, 4 ) for e in value_list ]
                            stable_scenarios[ this_scenario_name ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] = deepcopy( value_list )

                        #if this_scenario_name == 'NDPMC13A1' and iter_scen == 'NDPMC13A1' and 'TotalAnnualMaxCapacityInvestment' == param_list[p]:
                        #    print('what is going on?')
                        #    print(param_list[p])
                        #    # sys.exit()

        #########################################################################################
        ''' MODIFYING *base_configuration_smartGrid* '''
        this_scenario_df = deepcopy( base_configuration_smartGrid.loc[ base_configuration_smartGrid['Scenario'].isin( [ this_scenario_name ] ) ] )
        #
        set_list = list( set( this_scenario_df[ 'Tech_Set' ].tolist() ) )
        for l in range( len( set_list ) ):
            this_scenario_tech_df = this_scenario_df.loc[ this_scenario_df['Tech_Set'] == set_list[l] ]
            #
            if 'Contains' in set_list[l]:
                tech_indicator_list_raw = set_list[l].replace( ' ','' ).split( ':' )[1] # This is a string with a list after a colon
                tech_indicator_list = tech_indicator_list_raw.split( ';' ) # This could be a list of strings separated by semicolon
                for tech_indicator in tech_indicator_list:
                    tech_list = [ e for e in all_techs_list if tech_indicator in e ]
            else:
                tech_list = [ set_list[l] ]
            #
            for t in range( len( tech_list ) ):
                this_set = tech_list[t]
                param_list = list( set( this_scenario_tech_df[ 'Parameter' ].tolist() ) )
                for p in range( len( param_list ) ):
                    this_scenario_tech_param_df = this_scenario_tech_df.loc[ this_scenario_tech_df['Parameter'] == param_list[p] ]
                    #
                    smartGrid_Params_built_in  = this_scenario_tech_param_df['Built-in Parameter-Set'].tolist()[0]
                    smartGrid_Params_reference = this_scenario_tech_param_df['Reference'].tolist()[0]
                    smartGrid_Params_method    = this_scenario_tech_param_df['Method'].tolist()[0]
                    #------------------------------
                    # TAKE REFERENCE FOR INTERPOLATION, IF AVAILABLE
                    if smartGrid_Params_built_in == 'YES':
                        this_param_indices = [ i for i, x in enumerate( stable_scenarios[ this_scenario_name ][ param_list[p] ][ 't' ] ) if x == str( this_set ) ]
                        this_param_values = deepcopy( stable_scenarios[ this_scenario_name ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] )
                    #------------------------------
                    # CALCULATE THE VALUE LIST
                    if smartGrid_Params_method == 'Exact_Multiplier': # use *time_range_horizon*
                        value_list = []
                        this_index = this_scenario_tech_param_df.index.tolist()[0]
                        for y in range( len( time_range_vector ) ):
                            value_list.append( float( this_param_values[y] )*float( this_scenario_tech_param_df.loc[ this_index, time_range_vector[y] ] ) )
                    #
                    if smartGrid_Params_method == 'Exact': # use *time_range_horizon*
                        value_list = []
                        this_index = this_scenario_tech_param_df.index.tolist()[0]
                        for y in range( len( time_range_vector ) ):
                            value_list.append( this_scenario_tech_param_df.loc[ this_index, time_range_vector[y] ] )
                    #
                    if smartGrid_Params_method == 'Linear': # use *time_range_horizon*
                        smartGrid_Params_initialYear  = this_scenario_tech_param_df['y_ini'].tolist()[0]
                        smartGrid_Params_mYears = this_scenario_tech_param_df['Milestone_Years'].astype(str).tolist()[0].replace(' ','')
                        smartGrid_Params_mValue = this_scenario_tech_param_df['Milestone_Value'].astype(str).tolist()[0].replace(' ','')
                        #
                        smartGrid_Params_mYears = smartGrid_Params_mYears.split( ';' )
                        smartGrid_Params_mValue = smartGrid_Params_mValue.split( ';' )
                        #
                        known_years = [ y for y in time_range_vector if y <= smartGrid_Params_initialYear ]
                        known_values = [ float( this_param_values[y] ) for y in range( len(time_range_vector) ) if time_range_vector[y] <= smartGrid_Params_initialYear ]
                        known_years += [ float(e) for e in smartGrid_Params_mYears ]
                        known_values += [ float(e) for e in smartGrid_Params_mValue ]
                        value_list = linear_interpolation_time_series( time_range_vector, known_years, known_values )
                    #
                    if smartGrid_Params_method == 'Copy':
                        this_param_indices = [ i for i, x in enumerate( stable_scenarios[ smartGrid_Params_reference ][ param_list[p] ][ 't' ] ) if x == str( this_set ) ]
                        value_list = deepcopy( stable_scenarios[ smartGrid_Params_reference ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] )
                    #------------------------------
                    # OBTAINED VALUES, NOW PRINTING
                    if smartGrid_Params_built_in == 'YES':
                        value_list = [ round( e, 4 ) for e in value_list ]
                        this_param_indices = [ i for i, x in enumerate( stable_scenarios[ this_scenario_name ][ param_list[p] ][ 't' ] ) if x == str( this_set ) ]
                        stable_scenarios[ this_scenario_name ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] = deepcopy( value_list )

        #########################################################################################
        ''' MODIFYING *base_configuration_E_and_D* '''
        this_scenario_df = deepcopy( base_configuration_E_and_D.loc[ base_configuration_E_and_D['Scenario'].isin( [ this_scenario_name ] ) ] )
        #
        set_list = list( set( this_scenario_df[ 'Set' ].tolist() ) )
        for l in range( len( set_list ) ):
            this_scenario_tech_df = this_scenario_df.loc[ this_scenario_df['Set'] == set_list[l] ]
            #
            param_list = list( set( this_scenario_tech_df[ 'Parameter' ].tolist() ) )
            for p in range( len( param_list ) ):
                this_scenario_tech_param_df = this_scenario_tech_df.loc[ this_scenario_tech_df['Parameter'] == param_list[p] ]
                #
                efficiency_Params_built_in  = this_scenario_tech_param_df['Built-in Parameter-Set'].tolist()[0]
                efficiency_Params_reference = this_scenario_tech_param_df['Reference'].tolist()[0]
                efficiency_Params_method    = this_scenario_tech_param_df['Method'].tolist()[0]
                efficiency_Params_setIndex    = this_scenario_tech_param_df['Set_Index'].tolist()[0]
                #
                if efficiency_Params_method == 'Exact': # use *time_range_horizon*
                    value_list = []
                    this_index = this_scenario_tech_param_df.index.tolist()[0]
                    for y in range( len( time_range_vector ) ):
                        value_list.append( this_scenario_tech_param_df.loc[ this_index, time_range_vector[y] ] )
                #
                if efficiency_Params_method == 'Copy':
                    this_param_indices = [ i for i, x in enumerate( stable_scenarios[ efficiency_Params_reference ][ param_list[p] ][ efficiency_Params_setIndex ] ) if x == str( set_list[l] ) ]
                    value_list = deepcopy( stable_scenarios[ efficiency_Params_reference ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] )
                #
                # OBTAINED VALUES, NOW PRINTING
                if efficiency_Params_built_in == 'YES':
                    value_list = [ round( e, 4 ) for e in value_list ]
                    this_param_indices = [ i for i, x in enumerate( stable_scenarios[ this_scenario_name ][ param_list[p] ][ efficiency_Params_setIndex ] ) if x == str( set_list[l] ) ]
                    stable_scenarios[ this_scenario_name ][ param_list[p] ]['value'][ this_param_indices[0]:this_param_indices[-1]+1 ] = deepcopy( value_list )

        #########################################################################################

    print('  finished, now to processing')
    # sys.exit()

    scenario_list = list( stable_scenarios.keys() ) # This applies for all other scenarios

    #print('check')
    #sys.exit()

    '''
    Control inputs:
    '''
    is_this_last_update = True
    # is_this_last_update = False
    # is_this_last_update = False
    # generator_or_executor = 'None'
    generator_or_executor = 'Both'
    # generator_or_executor = 'Generator'
    # generator_or_executor = 'Executor'
    #
    #
    #########################################################################################
    if is_this_last_update == True:
        #
        print('3: Let us store the inputs for later analysis.')
        basic_header_elements = [ 'Future.ID', 'Strategy.ID', 'Strategy', 'Fuel', 'Technology', 'Emission', 'Season', 'Year' ]
        #
        parameters_to_print = [ 'AnnualEmissionLimit',
                                'AvailabilityFactor',
                                'CapacityFactor',
                                'CapacityToActivityUnit',
                                'CapitalCost',
                                'DepreciationMethod',
                                'DiscountRate',
                                'EmissionActivityRatio',
                                'EmissionsPenalty',
                                'FixedCost',
                                'InputActivityRatio',
                                'ModelPeriodEmissionLimit',
                                'OperationalLife',
                                'OutputActivityRatio',
                                'REMinProductionTarget',
                                'ResidualCapacity',
                                'RETagFuel',
                                'RETagTechnology',
                                'SpecifiedAnnualDemand',
                                'SpecifiedDemandProfile',
                                'TotalAnnualMaxCapacity',
                                'TotalAnnualMaxCapacityInvestment',
                                'TotalAnnualMinCapacity',
                                'TotalAnnualMinCapacityInvestment',
                                'TotalTechnologyAnnualActivityLowerLimit',
                                'TotalTechnologyAnnualActivityUpperLimit',
                                'TotalTechnologyModelPeriodActivityLowerLimit',
                                'TotalTechnologyModelPeriodActivityUpperLimit',
                                'VariableCost',
                                'YearSplit']

        print('Entered Parallelization of control inputs')
        x = len(scenario_list)
        max_x_per_iter = 40 # FLAG: This is an input
        y = x / max_x_per_iter
        y_ceil = math.ceil( y )
        #
        for n in range(0,y_ceil):
            n_ini = n*max_x_per_iter
            processes = []
            #
            if n_ini + max_x_per_iter <= x:
                max_iter = n_ini + max_x_per_iter
            else:
                max_iter = x
            #    
            for n2 in range( n_ini , max_iter ):
                p = mp.Process(target=csv_printer_parallel, args=(n2, scenario_list, stable_scenarios, basic_header_elements, parameters_to_print, S_DICT_params_structure) )
                processes.append(p)
                p.start()
            #
            for process in processes:
                process.join()

    #########################################################################################
    global scenario_list_print
    scenario_list_print = deepcopy( scenario_list ) # ['BAU','OP15C','NDP']
    # scenario_list_print = ['BAU','NDP','NDP_A','OP15C'] # FLAG: This is an input
    # scenario_list_print = ['NDP']

    # print('stop before printing')
    # sys.exit()

    if generator_or_executor == 'Generator' or generator_or_executor == 'Both':
        #
        print('5: We have finished all manipulations of base scenarios. We will now print.')
        #
        print_adress = './Executables'
        #
        packaged_useful_elements = [scenario_list_print, S_DICT_sets_structure, S_DICT_params_structure, list_param_default_value_params, list_param_default_value_value,
                                    print_adress, Reference_driven_distance,
                                    Fleet_Groups_inv, time_range_vector, Blend_Shares ]
        #
        print('Entered Parallelization of .txt printing')
        x = len(scenario_list)
        max_x_per_iter = 40 # FLAG: This is an input
        y = x / max_x_per_iter
        y_ceil = math.ceil( y )
        #
        for n in range(0,y_ceil):
            n_ini = n*max_x_per_iter
            processes = []
            #
            if n_ini + max_x_per_iter <= x:
                max_iter = n_ini + max_x_per_iter
            else:
                max_iter = x
            #    
            for n2 in range( n_ini , max_iter ):
                p = mp.Process(target=function_C_mathprog, args=(n2, stable_scenarios, packaged_useful_elements) )
                processes.append(p)
                p.start()
            #
            for process in processes:
                process.join()

        # This is for the linear version
        # function_C_mathprog( stable_scenarios, packaged_useful_elements )

    #########################################################################################
    if generator_or_executor == 'Executor' or generator_or_executor == 'Both':
        #
        print('6: We have finished printing base scenarios. We must now execute.')
        #
        packaged_useful_elements = [Reference_driven_distance, Reference_occupancy_rate, Reference_op_life,
                                    Fleet_Groups_inv, time_range_vector,
                                    list_param_default_value_params, list_param_default_value_value, list_gdp_ref]
        #
        set_first_list(scenario_list_print)
        print('Entered Parallelization of model execution')
        x = len(first_list)
        max_x_per_iter = 40 # FLAG: This is an input
        y = x / max_x_per_iter
        y_ceil = math.ceil( y )
        #
        for n in range(0,y_ceil):
            n_ini = n*max_x_per_iter
            processes = []
            #
            if n_ini + max_x_per_iter <= x:
                max_iter = n_ini + max_x_per_iter
            else:
                max_iter = x
            #    
            for n2 in range( n_ini , max_iter ):
                p = mp.Process(target=main_executer, args=(n2, packaged_useful_elements, scenario_list_print) )
                processes.append(p)
                p.start()
            #
            for process in processes:
                process.join()

        # This is for the linear version
        # for n in range( len( first_list ) ):
        #     main_executer(n,packaged_useful_elements)

    end_1 = time.time()   
    time_elapsed_1 = -start1 + end_1
    print( str( time_elapsed_1 ) + ' seconds /', str( time_elapsed_1/60 ) + ' minutes' )
    print('*: For all effects, we have finished the work of this script.')
    #########################################################################################



  # Libraries
# Data
# File Management
import os # Operating system library
import pathlib # file paths
import json
import requests
import math
import numpy as np
import pandas as pd # Dataframe manipulations
import datetime
from datetime import date
from datetime import datetime, timedelta
from config_settings import *

# ----------------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------------
def load_imaging(url_data_path, local_data_path, source='url'):
    if source == 'local':
        imaging = pd.read_csv(os.path.join(local_data_path,'imaging-log-latest.csv'))
        imaging_source = 'local'
    else:
        try:
            imaging = pd.read_csv('/'.join([url_data_path,'imaging-log-latest.csv']))
            imaging_source = 'url'
        except:
            imaging = pd.DataFrame()
            imaging_source = 'unavailable'
    return imaging, imaging_source

def load_qc(url_data_path, local_data_path, source='url'):
    if source == 'local':
        qc = pd.read_csv(os.path.join(local_data_path,'qc-log-latest.csv'))
        qc_source = 'local'
    else:
        try:
            qc = pd.read_csv('/'.join([url_data_path,'qc-log-latest.csv']))
            qc_source = 'url'
        except:
            qc = pd.DataFrame()
            qc_source = 'unavailable'
    return qc, qc_source

# ----------------------------------------------------------------------------
# Discrepancies Analysis
# ----------------------------------------------------------------------------

def get_indicated_received(imaging_dataframe, validation_column = 'bids_validation', validation_value = 1):
    """The get_indicated_received(imaging_dataframe) function takes the imaging log data frame and lengthens the
    table to convert the scan into a variable while preserving columns for the indicated and received value of each scan.
    Validation columns parameter should be a lits of tuples where the first tuple value is the column name and the
    second entry is the value of 'Y' for that column"""
    df = imaging_dataframe.copy()

    # Select columns, and create long dataframes from those columns, pivoting the scan into a variable
    # Select and pivot indicated columns
    index_cols = ['site','subject_id','visit','Surgery Week','bids_validation', 'dicom']
    index_new = ['Site', 'Subject', 'Visit','Surgery Week', 'BIDS','DICOM']

    indicated_cols = ['T1 Indicated',
           'DWI Indicated',
           'fMRI Individualized Pressure Indicated',
           'fMRI Standard Pressure Indicated',
           '1st Resting State Indicated',
           '2nd Resting State Indicated']

    received_cols = ['T1 Received',
       'DWI Received',
       'fMRI Individualized Pressure Received',
       'fMRI Standard Pressure Received',
       '1st Resting State Received',
       '2nd Resting State Received']

    scan_cols_short = ['T1w','DWI','CUFF1','CUFF2','REST1','REST2']

    indicated = df[index_cols + indicated_cols]
    indicated.columns = index_cols + scan_cols_short
    indicated = pd.melt(indicated, id_vars=index_cols, value_vars = scan_cols_short)
    indicated.columns = index_new + ['Scan', 'Value']

    # Select and pivot received_cols columns
    received_cols = ['T1 Received',
       'DWI Received',
       'fMRI Individualized Pressure Received',
       'fMRI Standard Pressure Received',
       '1st Resting State Received',
       '2nd Resting State Received']

    received = df[index_cols + received_cols]
    received.columns = index_cols + scan_cols_short
    received = pd.melt(received, id_vars=index_cols, value_vars = scan_cols_short)
    received.columns = index_new + ['Scan', 'Value']

    # Merge the indicated and received dataframes into a single dataframe
    merge_on = index_new + ['Scan']
    combined = pd.merge(indicated, received, how='outer', on=index_new + ['Scan'] )
    combined.columns = index_new + ['Scan','Indicated','Received']

    return combined

def calculate_overdue(BIDS, visit, surgery_week):
    today = datetime.now().date()
    if surgery_week is pd.NaT:
        overdue='No Surgery Date'
    elif BIDS == 0 and visit == 'V1' and surgery_week < today:
        overdue = 'Yes'
    elif BIDS == 0 and visit == 'V3' and  (today-surgery_week).days > 90:
        overdue = 'Yes'
    else:
        overdue='No'

    return overdue

# ----------------------------------------------------------------------------
# Imaging Overview
# ----------------------------------------------------------------------------
def roll_up(imaging):
    cols = ['site','visit','subject_id']
    df = imaging[cols].groupby(['site','visit']).count().reset_index()
    df = df.pivot(index='site', columns = 'visit', values = 'subject_id')
    df.loc['All Sites'] = df.sum(numeric_only=True, axis=0)
    df.loc[:,'Total'] = df.sum(numeric_only=True, axis=1)
    df.reset_index(inplace=True)
    return df

# ----------------------------------------------------------------------------
# Completions
# ----------------------------------------------------------------------------
def get_completions(df):
    scan_dict = {'T1 Indicated':'T1',
       'DWI Indicated':'DWI',
       '1st Resting State Indicated':'REST1',
       'fMRI Individualized Pressure Indicated':'CUFF1',
       'fMRI Standard Pressure Indicated':'CUFF2',
       '2nd Resting State Indicated':'REST2'}

    icols = list(scan_dict.keys())
    icols2 = list(scan_dict.values())

    df['completions_id'] = df.apply(lambda x: str(x['subject_id']) + x['visit'],axis=1)
    completions = df[['completions_id']+icols].groupby(icols).count().reset_index().rename(columns=scan_dict).rename(columns={'completions_id':'Count'})
    completions['Percent'] = round(100 * completions['Count']/(completions['Count'].sum()),1)
    completions = completions.sort_values(by=['Count'], ascending=False)
    completions.loc[:, ~completions.columns.isin(['Count', 'Percent'])] = completions.loc[:, ~completions.columns.isin(['Count', 'Percent'])].replace([0,1],['N','Y'])

    return completions

def completions_label_site(imaging, site, sites_info):
    # Get completions data for data subset
    if site == 'ALL':
        df = imaging.copy()
    elif site == 'MCC1':
        df = imaging[imaging['site'].isin(list(sites_info[sites_info['mcc']==1].site))].copy()
    elif site == 'MCC2':
        df = imaging[imaging['site'].isin(list(sites_info[sites_info['mcc']==2].site))].copy()
    else:
        df = imaging[imaging['site'] == site].copy()
    completions = get_completions(df)

    # Convert to multi-index
    multi_col = []
    for col in completions.columns[0:6]:
        t = ('Scan', col)
        multi_col.append(t)
    for col in completions.columns[6:]:
        t = (site, col)
        multi_col.append(t)
    completions.columns = multi_col

    return completions

def merge_completions(sites_list, imaging, sites_info):
    c = completions_label_site(imaging, sites_list[0], sites_info)
    for site in sites_list[1:]:
        c_site = completions_label_site(imaging, site, sites_info)
        c = c.merge(c_site, how='left', on=list(c.columns[0:6]))
    c = c.dropna(axis='columns', how='all').fillna(0)
    return c

# ----------------------------------------------------------------------------
# Heat matrix
# ----------------------------------------------------------------------------

def get_heat_matrix_df(qc, site, color_mapping_list):
    color_mapping_df = pd.DataFrame(color_mapping_list)
    color_mapping_df.columns= ['value','color']
    qc_cols = ['sub','ses', 'scan','rating']
    q = qc[(qc.site == site)][qc_cols]
    if len(q) >0:
        q['sub'] = q['sub'].astype(str)
        q2 = q.merge(color_mapping_df, how='left', left_on='rating', right_on='color')
        q3 = q2.sort_values(['sub','ses','scan']).drop_duplicates(['sub','ses','scan'],keep='last')
        q3['Scan'] = q3['ses'] + '-' + q3['scan']
        q3_matrix = q3.pivot(index='sub', columns = 'Scan', values = 'value').fillna(0)
        q3_matrix_cols = ['V1-T1w', 'V1-CUFF1', 'V1-CUFF2', 'V1-REST1', 'V1-REST2',
                 'V3-T1w', 'V3-CUFF1', 'V3-CUFF2', 'V3-REST1', 'V3-REST2']
        matrix_df = q3_matrix[q3_matrix_cols]
        matrix_df.insert(5, "", [0.1] * len(matrix_df))
        matrix_df.columns.name = None
        matrix_df.index.name = None
    else:
        matrix_df = pd.DataFrame()
    return matrix_df

def get_stacked_bar_data(df, id_col, metric_col, cat_cols, count_col = None):
    if count_col:
        sb = df[cat_cols + [metric_col, id_col, count_col]].copy()
    else:
        count_col = 'count'
        sb = df[cat_cols + [metric_col, id_col]].copy()
        sb[count_col] = 1
    sb_grouped = sb[cat_cols+[metric_col, count_col]].groupby(cat_cols+[metric_col]).count()
    sb_grouped.reset_index(inplace=True)
    sb_grouped['Total N'] = sb_grouped.groupby(cat_cols)[count_col].transform('sum')
    sb_grouped['%'] = 100 * sb_grouped[count_col] / sb_grouped['Total N']
    return sb_grouped

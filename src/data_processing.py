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
# FUNCTIONS
# ----------------------------------------------------------------------------
def roll_up(imaging):
    cols = ['site','visit','subject_id']
    df = imaging[cols].groupby(['site','visit']).count().reset_index()
    df = df.pivot(index='site', columns = 'visit', values = 'subject_id')
    df.loc['All Sites'] = df.sum(numeric_only=True, axis=0)
    df.loc[:,'Total'] = df.sum(numeric_only=True, axis=1)
    df.reset_index(inplace=True)
    return df

def get_completions(imaging):
    scan_dict = {'T1 Received':'T1',
       'DWI Received':'DWI',
       '1st Resting State Received':'REST1',
       'fMRI Individualized Pressure Received':'CUFF1',
       'fMRI Standard Pressure Received':'CUFF2',
       '2nd Resting State Received':'REST2'}

    icols = list(scan_dict.keys())
    icols2 = list(scan_dict.values())

    completions = imaging[['subject_id']+icols].groupby(icols).count().reset_index().rename(columns=scan_dict).rename(columns={'subject_id':'Count'})
    completions['Percent'] = round(100 * completions['Count']/(completions['Count'].sum()),1)
    completions = completions.sort_values(by=['Count'], ascending=False)
    return completions

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
    else:
        matrix_df = None
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

# ----------------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------------
data_repository = 'https://api.a2cps.org/files/v2/download/public/system/a2cps.storage.community/reports/imaging'
def load_imaging():
    try:
        imaging = pd.read_csv('/'.join([data_repository,'imaging-log-latest.csv']))
        imaging_source = 'url'
    except:
        imaging = pd.read_csv(os.path.join(DATA_PATH,'imaging_log.csv'))
        imaging_source = 'local'
    return imaging, imaging_source

def load_qc():
    try:
        qc = pd.read_csv('/'.join([data_repository,'qc-log-latest.csv']))
        qc_source = 'url'
    except:
        qc = pd.read_csv(os.path.join(DATA_PATH,'qc_log.csv'))
        qc_source = 'local'
    return qc, qc_source

imaging, imaging_source = load_imaging()
qc, qc_source = load_qc()

sites = list(imaging.site.unique())


# ----------------------------------------------------------------------------
# PROCESS DATA
# ----------------------------------------------------------------------------
completions = get_completions(imaging)
imaging_overview = roll_up(imaging)

scan_dict = {'T1 Received':'T1',
   'DWI Received':'DWI',
   '1st Resting State Received':'REST1',
   'fMRI Individualized Pressure Received':'CUFF1',
   'fMRI Standard Pressure Received':'CUFF2',
   '2nd Resting State Received':'REST2'}

icols = list(scan_dict.keys())
icols2 = list(scan_dict.values())

color_mapping_list = [(0.0, 'white'),(0.1, 'lightgrey'),(0.25, 'red'),(0.5, 'orange'),(0.75, 'yellow'),(1.0, 'green')]
stacked_bar_df = get_stacked_bar_data(qc, 'sub', 'rating', ['site','ses'])

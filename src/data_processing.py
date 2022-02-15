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
imaging_datafile = 'imaging_log.csv'
imaging_data_filepath = os.path.join(DATA_PATH,imaging_datafile)

qc_datafile = 'qc_log.csv'
qc_data_filepath = os.path.join(DATA_PATH,qc_datafile)

bold_datafile = 'group_bold.csv'
bold_data_filepath = os.path.join(DATA_PATH,bold_datafile)

imaging = pd.read_csv(imaging_data_filepath)
qc = pd.read_csv(qc_data_filepath)
bold = pd.read_csv(bold_data_filepath)

sites = list(imaging.site.unique())

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

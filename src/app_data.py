# # ----------------------------------------------------------------------------
# # PYTHON LIBRARIES
# # ----------------------------------------------------------------------------
# import datetime
# from urllib.error import HTTPError
# import pandas as pd
# import json

# ----------------------------------------------------------------------------
# PYTHON LIBRARIES
# ----------------------------------------------------------------------------
# Dash Framework
import dash_bootstrap_components as dbc
from dash import Dash, callback, clientside_callback, html, dcc, dash_table as dt, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate

# import local modules
from config_settings import *
from data_processing import *
from make_components import *
from styling import *


# ----------------------------------------------------------------------------
# APP Settings
# ----------------------------------------------------------------------------

external_stylesheets_list = [dbc.themes.SANDSTONE] #  set any external stylesheets

app = Dash(__name__,
                external_stylesheets=external_stylesheets_list,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
                assets_folder=ASSETS_PATH,
                requests_pathname_prefix=REQUESTS_PATHNAME_PREFIX,
                )

def update_api_data(api_data, file_url_root, api):
    if api not in api_data.keys():
        print('Please check the url for this api.')
    else:
        api_data[api]['date_request'] = datetime.datetime.now()
        try:
            df = pd.read_csv('/'.join([file_url_root,api]))
            api_data[api]['request_status'] = 200
            api_data[api]['date_data'] = datetime.datetime.now()
            api_data[api]['data'] = df.to_dict('records')
        except HTTPError:
            api_data[api]['request_status'] = HTTPError
    return api_data

# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------
# def serve_layout():
#     # try:
#     api_data = init_api_data
#     for api in api_data.keys():
#         api_data = update_api_data(api_data, data_url_root, api)
#     page_layout = html.Div([
#         html.Div([file
#             # html.P(api_data[api]),
#             # html.P(api_data[api]['date_request']),
#             # html.P(api_data[api]['request_status']),
#             # html.P(api_data[api]['date_data']),
#         ]) for file in file_list
#     ])
#     # except: 'date_request':None, 'request_status': None, 'date_data':None
#     #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
#     return page_layout

def serve_data_stores():
    imaging, imaging_source = load_imaging()
    qc, qc_source = load_qc()
    completions = get_completions(imaging)
    imaging_overview = roll_up(imaging)
    stacked_bar_df = get_stacked_bar_data(qc, 'sub', 'rating', ['site','ses'])
    data_dictionary = {
        'imaging': imaging.to_dict('records'),
        'imaging_source': imaging_source,
        'qc': qc.to_dict('records'),
        'qc_source': qc_source,
        'completions': completions.to_dict('records'),
        'imaging_overview' : imaging_overview.to_dict('records'),

    }

    # try:

    data_stores = html.Div([
    html.H1('Local Data Store'),
        dcc.Store(id='session_data', storage_type='session', data = data_dictionary),
        html.Div([html.P(key) for key in data_dictionary.keys()])
        # dcc.Store(id='local_data_qc', storage_type='session', data = qc.to_dict('records')),
    ])
    return data_stores
    # except:
    #     page_layout = html.Div('There is a problem accessing the data at this time. Please try again in a few minutes.')
    #     return page_layout

app.layout = serve_data_stores
#
# html.Div([
#         html.H1('Local Data Store'),
#         serve_data_stores
#         # dcc.Store(id='local_data', storage_type='local'),
#         # # dcc.Store(id='local_data_imaging', storage_type='local'),
#         # # dcc.Store(id='local_data_qc', storage_type='local'),
#         # # html.H1('Local Data Store'),
#         # dcc.Store(id='session_data', storage_type='session'),
#         # html.Div(id='content_div'),
#         # dcc.Interval(
#         #     id='interval-component',
#         #     interval=10*1000 # 5 minutes in milliseconds: 5*60*1000
#         # ),
#         # serve_layout()
# ])


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------

# @app.callback(
#     Output('local_data', 'data'),
#     Input('interval-component', 'n_intervals'),
#     State('local_data', 'data')
# )
# def update_global_data(n_intervals, existing_data):
#     if existing_data:
#         data = {'data':'yes'}
#     else:
#         data = {'data':'no'}
#     return data
#
# @app.callback(
#     Output('content_div', 'children'),
#     Input('local_data_imaging', 'data')
# )
# def update_global_data(data):
#     return json.dumps(data)

# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
else:
    server = app.server

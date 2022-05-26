# ----------------------------------------------------------------------------
# PYTHON LIBRARIES
# ----------------------------------------------------------------------------
# Dash Framework
import dash_bootstrap_components as dbc
from dash import Dash, callback, clientside_callback, html, dcc, dash_table as dt, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_daq as daq

import plotly.figure_factory as ff
import os

# import local modules
from config_settings import *
from data_processing import *
from make_components import *
from styling import *

from dateutil.relativedelta import relativedelta

# Bar Chart options
bar_chart_options = {'None':'None', 'MCC':'mcc', 'Site':'site','Visit':'ses','Scan':'scan'}

# Load local / asset data
sites_filepath = os.path.join(DATA_PATH,'sites.csv')
sites_info = pd.read_csv(sites_filepath)

# ----------------------------------------------------------------------------
# PROCESS DATA
# ----------------------------------------------------------------------------
# completions = get_completions(imaging)
# imaging_overview = roll_up(imaging)
mcc_dict = {'mcc': [1,1,1,2,2,2],
            'site':['UI','UC','NS','UM', 'WS','SH'],
            'site_facet': [1,2,3,1,2,3]
            }


scan_dict = {'T1 Received':'T1',
   'DWI Received':'DWI',
   '1st Resting State Received':'REST1',
   'fMRI Individualized Pressure Received':'CUFF1',
   'fMRI Standard Pressure Received':'CUFF2',
   '2nd Resting State Received':'REST2'}

icols = list(scan_dict.keys())
icols2 = list(scan_dict.values())

color_mapping_list = [(0.0, 'white'),(0.1, 'lightgrey'),(0.25, 'red'),(0.5, 'orange'),(0.75, 'yellow'),(1.0, 'green')]

# ----------------------------------------------------------------------------
# APP Settings
# ----------------------------------------------------------------------------

external_stylesheets_list = [dbc.themes.SANDSTONE, 'https://codepen.io/chriddyp/pen/bWLwgP.css'] #  set any external stylesheets

app = Dash(__name__,
                external_stylesheets=external_stylesheets_list,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
                assets_folder=ASSETS_PATH,
                requests_pathname_prefix=REQUESTS_PATHNAME_PREFIX,
                suppress_callback_exceptions=True
                )

# ----------------------------------------------------------------------------
# DASH APP COMPONENT FUNCTIONS
# ----------------------------------------------------------------------------
def overview_heatmap(imaging):
    scan_dict = {'T1 Indicated':'T1',
       'DWI Indicated':'DWI',
       '1st Resting State Indicated':'REST1',
       'fMRI Individualized Pressure Indicated':'CUFF1',
       'fMRI Standard Pressure Indicated':'CUFF2',
       '2nd Resting State Indicated':'REST2',
                }

    icols = list(scan_dict.keys())
    icols2 = list(scan_dict.values())

    other_cols = ['site', 'subject_id', 'visit']
    i2 = pd.melt(imaging[other_cols + icols], id_vars=other_cols, value_vars = icols)
    hm = i2.groupby(['site','variable'])['value'].sum().reset_index()

    subjects = imaging[['subject_id','visit','site']].groupby(['site']).count().reset_index()
    subjects['Site'] = subjects['site'] + ' [' + subjects['visit'].astype('str') + ']'

    figdf = hm.merge(subjects, how='left', on='site')
    figdf['normed'] = 100 * figdf['value']/figdf['subject_id']
    figdf = figdf[['Site','variable','normed']].pivot(index='Site', columns='variable', values='normed')
    figdf.columns = ['REST1','REST2','DWI','T1','CUFF1','CUFF2']
    figdf = figdf[['T1','DWI','REST1','CUFF1','CUFF2','REST2']]
    figdf2 = figdf.applymap(lambda x: str(int(x)) + '%')

    heatmap_fig = ff.create_annotated_heatmap(figdf.to_numpy(),
                                  x=list(figdf.columns),
                                     y=list(figdf.index),
                                     annotation_text=figdf2.to_numpy(), colorscale='gray')

    return heatmap_fig

def create_image_overview(imaging_overview):
    overview_div = html.Div([
        dbc.Row([dbc.Col([
            html.H3('Overview')
        ])]),
        dbc.Row([
            dbc.Col([
                dt.DataTable(
                    id='tbl-overview', data=imaging_overview.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in imaging_overview.columns],
                    style_data_conditional=[
                        {
                            'if': {
                                'column_id': 'Total',
                            },
                            'backgroundColor': 'SteelBlue',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'row_index': imaging_overview.index[imaging_overview['site']=='All Sites'],
                            },
                            'backgroundColor': 'blue',
                            'color': 'white'
                        },
                    ]

                ),
            ],width=6),

        ]),

    ])
    return overview_div

def completions_div(completions_cols, completions_data, imaging):
    completions_div = [
        dbc.Row([dbc.Col([
            html.H3('Percent of imaged subjects completing a particular scan by site')
        ])]),
        dbc.Row([
            dbc.Col([
                # html.Div(overview_heatmap(imaging))
                dcc.Graph(id='graph-overview-heatmap', figure = overview_heatmap(imaging))
            ]),
        ]),
        dbc.Row([dbc.Col([
            html.H3('Overall completion of scans Y/N for each scan in acquisition order: T1, DWI, REST1, CUFF1, CUFF2, REST2)')
        ])]),
        dbc.Row([
            dbc.Col([
                dt.DataTable(
                    id='tbl',
                    columns = completions_cols,
                    data = completions_data,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    merge_duplicate_headers=True,
                ),
            ])
        ]),
    ]
    return completions_div

def create_pie_charts(completions):
    pie_charts = [

        dbc.Row([dbc.Col([
            html.H3('Percent of returns by Scan type')
        ])]),
        dbc.Row([
            build_pie_col(completions, col) for col in icols2[0:3]
        ])        ,
        dbc.Row([
            build_pie_col(completions, col) for col in icols2[3:6]
        ]),
    ]
    return pie_charts

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------



# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------

def create_content(sites):
    # if len(sites) > 0:
    content = html.Div([
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.P(date.today().strftime('%B %d, %Y')),
                                html.P('Version Date: 03/10/22'),
                            ], width=3),
                            dbc.Col([
                                html.H1('Imaging Overview Report', style={'textAlign': 'center'})
                            ], width={"size": 6}),
                            dbc.Col([
                                html.P('Add dates to limit report range '),
                                dcc.DatePickerRange(
                                    id='report-date-picker-range',
                                    # start_date = '2021-03-29',
                                    # end_date=datetime.now().date(),
                                    initial_visible_month = date.today() + relativedelta(months=-2),
                                    min_date_allowed = '2021-03-29',
                                    number_of_months_shown = 3,
                                    show_outside_days = True,
                                ),
                            ], width=2),
                            dbc.Col([
                                html.Br(),
                                dbc.Button('Rerun Report', id='btn-rerun-dates',n_clicks=0),],width=1)
                            ]),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.P([' '], style={'background-color':'ForestGreen', 'height': '20px', 'width':'20px','float':'left'}),
                                    html.P(['no known issues'], style={'padding-left': '30px', 'margin': '0px'})
                                ]),
                                    html.Div([
                                        html.P([' '], style={'background-color':'Gold', 'height': '20px', 'width':'20px','float':'left', 'clear':'both'}),
                                        html.P(['minor variations/issues; correctable'], style={'padding-left': '30px', 'margin': '0px'})
                                    ]),
                                    html.Div([
                                        html.P([' '], style={'background-color':'FireBrick', 'height': '20px', 'width':'20px','float':'left', 'clear':'both'}),
                                        html.P(['significant variations/issues; not expected to be usable'], style={'padding-left': '30px', 'margin': '0px'})
                                    ]),
                            ],width=2),
                        ], style={'border':'1px solid black'}),

                        dbc.Row([
                            dbc.Col([
                                dbc.Tabs(id="tabs", active_tab='tab-overview', children=[
                                    dbc.Tab(label='Overview', tab_id='tab-overview', children=[
                                        html.Div([
                                            dbc.Row([
                                                dbc.Col([html.Div(id='overview_div')])
                                            ]),
                                            dbc.Row([
                                                dbc.Col([html.Div(id='graph_stackedbar_div')], width=10),
                                                    dbc.Col([
                                                        html.H3('Bar Chart Settings'),
                                                        html.Label('Chart Type'),
                                                        daq.ToggleSwitch(
                                                                id='toggle_stackedbar',
                                                                label=['Count','Stacked Percent'],
                                                                value=False
                                                            ),
                                                        html.Label('Separate by Visit'),
                                                        daq.ToggleSwitch(
                                                                id='toggle_visit',
                                                                label=['Combined','Split'],
                                                                value=False
                                                            ),

                                                        html.Label('Chart Selection'),
                                                        dcc.Dropdown(
                                                            id='dropdown-bar',
                                                           options=[
                                                               {'label': ' Site and MCC', 'value': 1},
                                                               {'label': ' Site', 'value': 2},
                                                               {'label': ' MCC', 'value': 3},
                                                               {'label': ' Combined', 'value': 4},
                                                           ],
                                                           multi=False,
                                                           clearable=False,
                                                           value=1
                                                        ),
                                                        ],width=2),
                                                ]),
                                        ])

                                    ]),
                                    dbc.Tab(label='Discrepancies', tab_id='tab-discrepancies', children=[html.Div([
                                            dbc.Row([
                                                dbc.Col([html.Div(id='discrepancies_section')])
                                            ]),
                                        ])]),
                                    dbc.Tab(label='Completions', tab_id='tab-completions', children=[html.Div(id='completions_section')]),
                                    dbc.Tab(label='Pie Charts', tab_id='tab-pie', children=[html.Div(id='pie_charts')]),
                                    dbc.Tab(label='Heat Map', tab_id='tab-heatmap', children=[html.Div(id='heatmap')]),
                                ]),
                            ],width=10),

                            dbc.Col([
                                dcc.Dropdown(
                                    id='dropdown-sites',
                                    options=[
                                        {'label': 'All Sites', 'value': (',').join(sites)},
                                        {'label': 'MCC1', 'value': 'UI,UC,NS'},
                                        {'label': 'MCC2', 'value': 'UM,WS,SH' },
                                        {'label': 'MCC1: University of Illinois at Chicago', 'value': 'UI' },
                                        {'label': 'MCC1: University of Chicago', 'value': 'UC' },
                                        {'label': 'MCC1: NorthShore', 'value': 'NS' },
                                        {'label': 'MCC2: University of Michigan', 'value': 'UM' },
                                        {'label': 'MCC2: Wayne State University (pending)', 'value': 'WS' },
                                        {'label': 'MCC2: Spectrum Health (pending)', 'value': 'SH' }
                                    ],
                                    # value = 'NS'
                                    multi=False,
                                    clearable=False,
                                    value=(',').join(sites)
                                ),
                            ], id='dropdown-sites-col',width=2),
                        ]),
                        dbc.Row([
                            dbc.Col([html.Div(id='tab-content')], className='delay')
                        ])

                    ]
                    , style={'border':'1px solid black', 'padding':'10px'}
                )
            ])
    # else:
    #     content = html.Div([
    #         dbc.Alert("There has been a problem accessing the data API at this time. Please try again in a few minutes.", color="warning")
    #     ])
    return content

def serve_data_stores(url_data_path, local_data_path, source):
    imaging, imaging_source = load_imaging(url_data_path, local_data_path, source)
    qc, qc_source = load_qc(url_data_path, local_data_path, source)

    if imaging.empty or qc.empty:
        completions = pd.DataFrame()
        imaging_overview =  pd.DataFrame()
        indicated_received =  pd.DataFrame()
        stacked_bar_df =  pd.DataFrame()
        sites = []
    else:
        completions = get_completions(imaging)
        imaging_overview = roll_up(imaging)
        indicated_received = get_indicated_received_discrepancy(imaging)
        stacked_bar_df = get_stacked_bar_data(qc, 'sub', 'rating', ['site','ses'])
        sites = list(imaging.site.unique())

    data_dictionary = {
        'imaging': imaging.to_dict('records'),
        'imaging_source': imaging_source,
        'sites': sites,
        'qc': qc.to_dict('records'),
        'qc_source': qc_source,
        'completions': completions.to_dict('records'),
        'imaging_overview' : imaging_overview.to_dict('records'),
        'indicated_received' : indicated_received.to_dict('records'),
    }

    data_stores = html.Div([
        dcc.Store(id='session_data', storage_type='session', data = data_dictionary),
        dcc.Store(id='filtered_data'),
        html.Div(id='content_div'),
        create_content(sites)
    ])
    # data_stores = html.Div([
    #     dcc.Store(id='session_data', storage_type='session', data = data_dictionary),
    #
    #     # html.P('Imaging Source: ' + data_dictionary['imaging_source']),
    #     # html.P('QC Source: ' + data_dictionary['qc_source']),
    #     create_content(sites)
    # ])
    return data_stores

def serve_layout():
    # api_data = get_imaging_api()
    # imaging_api = api_data['data']['imaging']
    # qc_api = api_data['data']['qc']

    # try:
    page_layout =  html.Div([
            html.Div(id='test-div'),
            html.Div(id='test-div2'),
            # serve_data_store_raw(data_url_root, DATA_PATH, 'url'),
            serve_data_stores(data_url_root, DATA_PATH, 'url'),
            ], className='delay')

    # except:
    #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout

# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------
# Update filtered data section if button clicked
@app.callback(
    Output('filtered_data', 'data'),
    Output('test-div','children'),
    Input('btn-rerun-dates','n_clicks'),
    State('session_data', 'data'),
    State('report-date-picker-range', 'start_date'),
    State('report-date-picker-range', 'end_date')
)
def filter_data(n_clicks, data, start_date, end_date):
    if start_date or end_date:
        imaging = pd.DataFrame.from_dict(data['imaging'])
        qc = pd.DataFrame.from_dict(data['qc'])

        filtered_imaging = filter_imaging(imaging, start_date, end_date)
        completions = get_completions(filtered_imaging)
        imaging_overview = roll_up(filtered_imaging)
        indicated_received = get_indicated_received_discrepancy(filtered_imaging)
        sites = list(filtered_imaging.site.unique())

        filtered_qc = filter_qc(qc, filtered_imaging)
        stacked_bar_df = get_stacked_bar_data(filtered_qc, 'sub', 'rating', ['site','ses'])

        filtered_data_dictionary = {
            'imaging': filtered_imaging.to_dict('records'),
            'sites': sites,
            'qc': filtered_qc.to_dict('records'),
            'completions': completions.to_dict('records'),
            'imaging_overview' : imaging_overview.to_dict('records'),
            'indicated_received' : indicated_received.to_dict('records'),
        }
        kids = html.Div(html.P(start_date))
    else:
        filtered_data_dictionary = {}
        kids = 'empty dict'

    return filtered_data_dictionary,  kids


# Build Tabs
@app.callback(
    Output('dropdown-sites-col','style'),
    Input("tabs", "active_tab"))
def switch_tab(at):
    if at == "tab-overview":
        return {'display': 'none'}
    elif at == "tab-discrepancies":
        return {'display': 'block'}
    elif at == "tab-completions":
        return {'display': 'block'}
    elif at == "tab-pie":
        return {'display': 'block'}
    elif at == "tab-heatmap":
        return {'display': 'block'}
    return {'display': 'block'}


@app.callback(
    Output('overview_div', 'children'),
    Input('filtered_data', 'data'),
    Input('btn-rerun-dates','n_clicks'),
    State('session_data', 'data')
)
def update_overview_section(filtered_data, n_clicks, all_data):
    try:
        if len(filtered_data) > 0:
            data = filtered_data
        else:
            data = all_data
    except:
        data = all_data
    imaging_overview = pd.DataFrame.from_dict(data['imaging_overview'])
    return create_image_overview(imaging_overview)

# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True, port=8030)
else:
    server = app.server

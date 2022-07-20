# ----------------------------------------------------------------------------
# PYTHON LIBRARIES
# ----------------------------------------------------------------------------
# Dash Framework
import dash_bootstrap_components as dbc
from dash import Dash, callback, clientside_callback, html, dcc, dash_table as dt, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_daq as daq

import plotly.figure_factory as ff

# import local modules
from config_settings import *
from data_processing import *
from make_components import *
from styling import *


# Bar Chart options
bar_chart_options = {'None':'None', 'MCC':'mcc', 'Site':'site','Visit':'ses','Scan':'scan'}

# Set Version date
version_msg = 'Version Date: 07/13/22'
LOCAL_DATA_DATE = '07/19/2022'

# Load local / asset data
sites_filepath = os.path.join(DATA_PATH,'sites.csv')
sites_info = pd.read_csv(sites_filepath)

# Get rescinded patients from local file until subjects API is working
rescinded_date = '07/11/2022'
rescinded_filepath = os.path.join(DATA_PATH,'rescinded.csv')
rescinded = pd.read_csv(rescinded_filepath)

# ----------------------------------------------------------------------------
# PROCESS DATA
# ----------------------------------------------------------------------------
# completions = get_completions(imaging)
# imaging_overview = roll_up(imaging)
mcc_dict = {'mcc': [1,1,1,2,2,2],
            'site':['UI','UC','NS','UM', 'WS','SH'],
            'site_facet': [1,2,3,1,2,3]
            }


scan_dict = {
    'DWI Received':'DWI',
    'T1 Received':'T1',
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
# DASH HTML COMPONENTS
# ----------------------------------------------------------------------------

offcanvas_content = html.Div([
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
        html.P(['significant variations/issues; not expected to be comparable'], style={'padding-left': '30px', 'margin': '0px'})
    ]),
])

offcanvas = html.Div([
    dbc.Button("Legend", id="open-offcanvas", n_clicks=0),
    dbc.Offcanvas(
        offcanvas_content,
        id="offcanvas",
        title="Title",
        is_open=False,
    ),
])

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


def build_boxplot(df):
    fig=go.Figure()

    data_length = (len(df['site'].unique()))

    for i, visit in enumerate(df['visit'].unique()):
        df_plot=df[df['visit']==visit]
        #print(df_plot.head())

        fig.add_trace(go.Box(x=df_plot['site'],
                             y=df_plot['Cuff1 Applied Pressure'],
                             meta = visit,
#                              boxmean="sd",
                             line=dict(color=px.colors.qualitative.Plotly[i]),
                             boxpoints='suspectedoutliers',
                             name=visit,
                             offsetgroup=visit,
                            ))


        ## loop through the values you want to label and add them as annotations
    for i, visit in enumerate(df['visit'].unique()):
        for s in df['site'].unique():
            # Get settings for annotation
            xshift = 25
            if i == 0:
                xshift = -xshift
            else:
                xshift = xshift
            y_point = df[(df['site']==s) & (df['visit']==visit)]['Cuff1 Applied Pressure'].median()
            records = len(df[(df['site']==s) & (df['visit']==visit)]['Cuff1 Applied Pressure'])
            if records > 0:
                text = '<b>' + str(len(df[(df['site']==s) & (df['visit']==visit)]['Cuff1 Applied Pressure'])) + '</b>'

            else:
                text =''

            fig.add_annotation(
                    x=s,
                    y=y_point,
                    text=text,
                    showarrow=False,
                    xshift = xshift,
                    yshift=10,

            )

    fig.update_layout(boxmode='group',
                      xaxis_tickangle=0,
        autosize=False,
        width=1000,
        height=800,legend=dict(
                orientation="h"))

    return fig
# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------
def load_data_source(url_data_path, local_data_path, source):
    imaging, imaging_source = load_imaging(url_data_path, local_data_path, source)
    qc, qc_source = load_qc(url_data_path, local_data_path, source)

    return imaging, imaging_source, qc, qc_source

def get_filtered_data_store(raw_data_store, start_date: datetime = None, end_date = None):
    imaging = pd.DataFrame.from_dict(raw_data_store['imaging'])
    qc = pd.DataFrame.from_dict(raw_data_store['qc'])

    if imaging.empty or qc.empty:
        completions = pd.DataFrame()
        imaging_overview =  pd.DataFrame()
        indicated_received =  pd.DataFrame()
        stacked_bar_df =  pd.DataFrame()
        sites = []
    else:
        imaging = filter_imaging(imaging, start_date = start_date, end_date = end_date)
        qc = filter_qc(qc, imaging)

        completions = get_completions(imaging)
        imaging_overview = roll_up(imaging)
        indicated_received = get_indicated_received(imaging)
        ratings = indicated_received.merge(qc, how='outer', left_on = ['Site','Subject','Visit','Scan'], right_on=['site','sub','ses','scan']).fillna('N/A')

        stacked_bar_df = get_stacked_bar_data(qc, 'sub', 'rating', ['site','ses'])
        sites = list(imaging.site.unique())

    processed_data_dictionary = {
        'imaging': imaging.to_dict('records'),
        'qc': qc.to_dict('records'),
        'sites': sites,
        'completions': completions.to_dict('records'),
        'imaging_overview' : imaging_overview.to_dict('records'),
        'ratings' : ratings.to_dict('records'),
        'indicated_received' : indicated_received.to_dict('records'),
    }

    return processed_data_dictionary

def serve_raw_data_store(url_data_path, local_data_path, source):
    imaging, imaging_source, qc, qc_source = load_data_source(url_data_path, local_data_path, source)

    if imaging.empty or qc.empty:
        # completions = pd.DataFrame()
        # imaging_overview =  pd.DataFrame()
        # indicated_received =  pd.DataFrame()
        # stacked_bar_df =  pd.DataFrame()
        sites = []
    else:
        # completions = get_completions(imaging)
        # imaging_overview = roll_up(imaging)
        # indicated_received = get_indicated_received(imaging)
        # stacked_bar_df = get_stacked_bar_data(qc, 'sub', 'rating', ['site','ses'])
        sites = list(imaging.site.unique())

    raw_data_dictionary = {
        'imaging': imaging.to_dict('records'),
        'qc': qc.to_dict('records'),
        'imaging_source': imaging_source,
        'qc_source': qc_source,
        'sites': sites,
        # 'completions': completions.to_dict('records'),
        # 'imaging_overview' : imaging_overview.to_dict('records'),
        # 'indicated_received' : indicated_received.to_dict('records'),
    }

    data_stores = html.Div([
        dcc.Store(id='session_data',  data = raw_data_dictionary), #storage_type='session',
        dcc.Store(id='filtered_data'),
        # html.P('Imaging Source: ' + data_dictionary['imaging_source']),
        # html.P('QC Source: ' + data_dictionary['qc_source']),
        create_content(source, sites)
    ])
    return data_stores



def create_content(source, sites):
    if source == 'local':
        source_msg = 'Data loaded from local files dated ' + LOCAL_DATA_DATE
    else:
        source_msg = 'Data from API'
    if len(sites) > 0:
        content = html.Div([
                    html.Div([
                        dbc.Row(id='content'),
                        dbc.Row([
                            dbc.Col([
                                html.H1('Imaging Overview Report', style={'textAlign': 'center'})
                            ])
                            ], justify='center', align='center'),
                        dbc.Row([
                            dbc.Col([
                                html.P(date.today().strftime('%B %d, %Y')),
                                html.P(version_msg),
                                html.P(source_msg)
                                ],
                            width=10),
                            dbc.Col([
                                # offcanvas
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
                                        html.P(['significant variations/issues; not expected to be comparable'], style={'padding-left': '30px', 'margin': '0px'})
                                    ]),
                            ],width=2),
                        ], style={'border':'1px solid black'}),

                        dbc.Row([
                            dbc.Col([
                                dbc.Tabs(id="tabs", active_tab='tab-overview', children=[
                                    dbc.Tab(label='Overview', tab_id='tab-overview'),
                                    dbc.Tab(label='Discrepancies', tab_id='tab-discrepancies'),
                                    dbc.Tab(label='Completions', tab_id='tab-completions'),
                                    dbc.Tab(label='Pie Charts', tab_id='tab-pie'),
                                    dbc.Tab(label='Heat Map', tab_id='tab-heatmap'),
                                    dbc.Tab(label='Cuff Pressure', tab_id='tab-cuff'),
                                ]),
                            ],width=10),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='dropdown-sites',
                                    options=[  #'UI', 'UC', 'NS', 'N/A', 'UM', 'WS'
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
    else:
        content = html.Div([
            dbc.Alert("There has been a problem accessing the data API at this time. Please try again in a few minutes.", color="warning")
        ])
    return content

def serve_layout():
    # try:
    page_layout =  html.Div([
    # change to 'url' before deploy
            # serve_data_stores('url'),
            serve_raw_data_store(data_url_root, DATA_PATH, DATA_SOURCE),
            ], className='delay')

    # except:
    #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------
# Filter
@app.callback(
    Output('filtered_data', 'data'),
    Input('session_data', 'data')
)
def filtered(raw_data):
    filtered_data = get_filtered_data_store(raw_data)
    return filtered_data

# Filter
@app.callback(
    Output('test-row','children'),
    Input('filtered_data', 'data')
)
def see_filtering(filtered_data):
    kids = html.Div()
    # kids = html.Div(json.dumps(filtered_data['qc']))
    return kids

@app.callback(Output("tab-content", "children"),
    Output('dropdown-sites-col','style'),
    Input("tabs", "active_tab"))
def switch_tab(at):
    if at == "tab-overview":
        overview = dcc.Loading(
                    id="loading-overview",
                    children=[
                        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3('Scan sessions for pre-surgery (V1) and 3 month post surgery (V3) visits'),
                    html.Div(id='overview_div')
                ])
            ]),
            dbc.Row([
                dbc.Col([html.H3('Quality ratings for individual scans (up to six scans per session: T1, DWI, REST1, CUFF1, CUFF2, REST2)')]),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div(id='graph_stackedbar_div')
                    ], width=10),
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
                    ],
                    type="circle",
                )
        style = {'display': 'none'}
        return overview, style
    elif at == "tab-discrepancies":
        discrepancies = dcc.Loading(
                    id="loading-discrepancies",
                    children=[
                        html.Div([
            dbc.Row([
                dbc.Col([html.Div(id='discrepancies_section')])
            ]),
        ])
                    ],
                    type="circle",
                )
        return discrepancies, {'display': 'block'}
    elif at == "tab-completions":
        completions = dcc.Loading(
                    id="loading-completions",
                    children=[
                        html.Div([
                            html.Div(id='completions_section')
                        ])
                    ],
                    type="circle",
                )
        return completions, {'display': 'block'}
    elif at == "tab-pie":
        pies = dcc.Loading(
                    id="loading-pie",
                    children=[
                        html.Div(id='pie_charts')
                        ],
                    type="circle",
                )
        return pies, {'display': 'block'}
    elif at == "tab-heatmap":
        heatmap = html.Div(id='heatmap')
        return heatmap, {'display': 'block'}
    elif at == "tab-cuff":
        cuff = dcc.Loading(
                    id="loading-heatmap",
                    children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([html.Div(id='cuff_section')])
                            ]),
                        ])
                    ],
                type="circle",
            )
        return cuff, {'display': 'block'}

    return html.P("This shouldn't ever be displayed...")
# Define callback to update graph_stackedbar

# Toggle Stacked bar toggle_stackedbar graph_stackedbar
@app.callback(
    Output('overview_div', 'children'),
    Input('filtered_data', 'data')
)
def update_overview_section(data):
    imaging_overview = pd.DataFrame.from_dict(data['imaging_overview'])
    return create_image_overview(imaging_overview)

@app.callback(
    Output('discrepancies_section', 'children'),
    Input('filtered_data', 'data')
)
def update_discrepancies_section(data):
    # Load imaging data from data store
     imaging = pd.DataFrame.from_dict(data['imaging'])
     df = pd.DataFrame.from_dict(data['indicated_received'])

     # Rescinded patients in imaging
     cols = ['site', 'subject_id', 'visit',  'dicom',
       'bids', 'bids_validation', 'acquisition_week', 'Surgery Week']
     rescinded_imaging = imaging[imaging['subject_id'].isin(list(rescinded['main_record_id']))][cols]
     rescind_msg = 'Subjects who rescinded prior to ' + rescinded_date + ' but have records in the imaging file'

     # Get data for tables
     # df = get_indicated_received(imaging)
     df = pd.DataFrame.from_dict(data['indicated_received'])
     index_cols = ['Site','Subject','Visit']
     no_bids = df[df['BIDS']==0].sort_values(by=index_cols+['Scan'])
     mismatch = df[(df['DICOM']==1) & (df['Indicated'] != df['Received'])]

     no_bids_table = dt.DataTable(
                    id='tbl-no_bids', data=no_bids.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in no_bids.columns],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    )

     mismatch_table = dt.DataTable(
                    id='tbl-mismatch', data=mismatch.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in mismatch.columns],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    )

     rescinded_table = dt.DataTable(
                    id='tbl-rescinded', data=rescinded_imaging.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in rescinded_imaging.columns],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    )


     discrepancies_div = html.Div([
             dbc.Col([
                 html.H3("BIDS value = 0"),
                 no_bids_table
             ],width=6),
           dbc.Col([
               html.H3('Records with mismatch between indicated and received'),
               mismatch_table
           ],width=6),
           dbc.Col([
               html.H3(rescind_msg),
               rescinded_table
           ],width=6),
     ])
     return discrepancies_div

@app.callback(
    Output('cuff_section', 'children'),
    Input('filtered_data', 'data')
)
def update_cuff_section(data):
    # Load imaging data from data store
     imaging = pd.DataFrame.from_dict(data['imaging'])
     fig = build_boxplot(imaging)
     cuff_div = html.Div([
             dbc.Col([
                 html.H3("Cuff1 Applied Pressure"),
                 dcc.Graph(id='boxplot_cuff1', figure=fig)
             ]),
     ])
     return cuff_div

@app.callback(
    Output('graph_stackedbar_div', 'children'),
    Input('filtered_data', 'data'),
    Input('toggle_stackedbar', 'value'),
    Input('toggle_visit', 'value'),
    Input('dropdown-bar', 'value'),
)
def update_stackedbar(filtered_data, type, visit, chart_selection):
    global mcc_dict
    # False = Count and True = Percent
    # return json.dumps(mcc_dict)
    if type:
        type = 'Percent'
    else:
        type = 'Count'

    qc = pd.DataFrame.from_dict(filtered_data['qc'])
    count_col='sub'
    color_col = 'rating'

    if chart_selection == 1:
        if visit:
            facet_row = 'ses'
        else:
            facet_row = None
        fig = bar_chart_dataframe(qc, mcc_dict, count_col, 'site', color_col, 'mcc', facet_row,  chart_type=type)
    else:
        if visit:
            x_col = 'ses'
        else:
            x_col = None
        if chart_selection == 2:
            fig = bar_chart_dataframe(qc, mcc_dict, count_col, x_col, color_col, 'site', chart_type=type)

        elif chart_selection == 3:
            fig = bar_chart_dataframe(qc, mcc_dict, count_col, x_col, color_col, 'mcc', chart_type=type)

        else:
            fig = bar_chart_dataframe(qc, mcc_dict, count_col, x_col, color_col, chart_type=type)

    return [html.P(visit), dcc.Graph(id='graph_stackedbar', figure=fig)]

@app.callback(
    Output('completions_section', 'children'),
    Input('dropdown-sites', 'value'),
    State('filtered_data', 'data')
)
def update_image_report(sites, data):
    imaging = pd.DataFrame.from_dict(data['imaging'])
    sites_list = ['ALL', 'MCC1', 'MCC2'] + list(imaging.site.unique())
    completions = merge_completions(sites_list, imaging, sites_info)

    # Conver tuples to multiindex then prepare data for dash data table
    completions.columns = pd.MultiIndex.from_tuples(completions.columns)
    completions_cols, completions_data = datatable_settings_multiindex(completions)
    ct = completions_div(completions_cols, completions_data, imaging)
    # kids = [html.P(c) for c in list(completions.columns)]
    # return kids
    return ct

@app.callback(
    Output('pie_charts', 'children'),
    Input('dropdown-sites', 'value'),
    Input('filtered_data', 'data'),
    State('dropdown-sites', 'options')
)
def update_pie(sites, filtered_data, options):
    sites_list = sites.split(",")
    ratings = pd.DataFrame.from_dict(filtered_data['ratings'])
    site_label = [x['label'] for x in options if x['value'] == sites]
    pie_df = ratings[ratings['Site'].isin(sites_list)]

    pie_charts = [
        dbc.Row([dbc.Col([
            html.H3('Percent of returns by Scan type'),
        ])]),
        dbc.Row([
            html.H4(site_label),
            dcc.Graph(id='pie_main', figure=make_pie_chart(pie_df))
        ])
    ]

    if len(sites_list) > 1:
        fig_height = len(sites_list) * 300
        fig=make_pie_chart(pie_df, facet_row='Site')
        fig.update_layout(
            autosize=False,
            width =1500,
            height=fig_height)

        add_div =dbc.Row([
            html.H4('Breakout by Site'),
            dcc.Graph(id='pie_main', figure=fig)
        ])
        pie_charts.append(add_div)

    return pie_charts



@app.callback(
    Output('heatmap', 'children'),
    Input('dropdown-sites', 'value'),
    State('filtered_data', 'data')
)
def update_heatmap(sites, data):
    global color_mapping_list
    sites_list = sites.split(",")
    qc = pd.DataFrame.from_dict(data['qc'])

    if len(sites_list) == 1:
        df  = get_heat_matrix_df(qc, sites, color_mapping_list)
        if not df.empty:
            fig_heatmap = generate_heat_matrix(df, color_mapping_list)
            heatmap = html.Div([
                dcc.Graph(id='graph_heatmap', figure=fig_heatmap)
            ])
        else:
            heatmap = html.Div([
                html.H4('There is not yet data for this site')
            ], style={'padding': '50px', 'font-style': 'italic'})
    else:
        heatmap = html.Div([
            html.H4('Please select a single site from the dropdown above to see a Heatmap of Image Quality')
        ], style={'padding': '50px', 'font-style': 'italic'})    # f = generate_heat_matrix(get_heat_matrix_df(qc, sites), colors)
    # heatmap = dcc.Graph(figure=f)

    return heatmap


# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True,)
else:
    server = app.server

# ----------------------------------------------------------------------------
# PYTHON LIBRARIES
# ----------------------------------------------------------------------------
# Dash Framework
import dash_bootstrap_components as dbc
from dash import Dash, callback, clientside_callback, html, dcc, dash_table as dt, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_daq as daq

# import local modules
from config_settings import *
from data_processing import *
from make_components import *
from styling import *


# Bar Chart options
bar_chart_options = {'None':'None', 'MCC':'mcc', 'Site':'site','Visit':'ses','Scan':'scan'}

# ----------------------------------------------------------------------------
# APP Settings
# ----------------------------------------------------------------------------

external_stylesheets_list = [dbc.themes.SANDSTONE] #  set any external stylesheets

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
def create_image_overview(df):
    overview_div = html.Div([
        dbc.Row([dbc.Col([
            html.H3('Overview')
        ])]),
        dbc.Row([
            dbc.Col([
                dt.DataTable(
                    id='tbl-overview', data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
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
                                'row_index': df.index[df['site']=='All Sites'],
                            },
                            'backgroundColor': 'blue',
                            'color': 'white'
                        },
                    ]

                ),
            ], width = 6)
        ]),
    ])
    return overview_div

def completions_table(completions):
    completions_div = [
        dbc.Row([dbc.Col([
            html.H3('Overall completion of scans Y/N for each scan in acquisition order: T1, DWI, REST1, CUFF1, CUFF2, REST2)')
        ])]),
        dbc.Row([
            dbc.Col([
                dt.DataTable(
                    id='tbl', data=completions.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in completions.columns],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
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
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------
def serve_data_stores(source):
    imaging, imaging_source = load_imaging(source)
    qc, qc_source = load_qc(source)
    completions = get_completions(imaging)
    imaging_overview = roll_up(imaging)
    stacked_bar_df = get_stacked_bar_data(qc, 'sub', 'rating', ['site','ses'])
    data_dictionary = {
        'imaging': imaging.to_dict('records'),
        'imaging_source': imaging_source,
        'sites':  list(imaging.site.unique()),
        'qc': qc.to_dict('records'),
        'qc_source': qc_source,
        'completions': completions.to_dict('records'),
        'imaging_overview' : imaging_overview.to_dict('records'),

    }
    data_stores = html.Div([
        dcc.Store(id='session_data', storage_type='local', data = data_dictionary),
        # html.P('Imaging Source: ' + data_dictionary['imaging_source']),
        # html.P('QC Source: ' + data_dictionary['qc_source']),
        create_content(list(imaging.site.unique()))
    ])
    return data_stores

def create_content(sites):
    content = html.Div([
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.H1('Imaging Overview Report', style={'textAlign': 'center'})
                        ])
                        ], justify='center', align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.P(date.today().strftime('%B %d, %Y')),
                            html.P('Version Date: 03/03/22')], width=10),
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
                        ], width=2),
                            # dbc.Col([filter_box],width=2)]),
                        ], style={'border':'1px solid black'}),
                    dbc.Tabs(id="tabs", active_tab='tab-overview', children=[
                        dbc.Tab(label='Overview', tab_id='tab-overview'),
                        dbc.Tab(label='Completions', tab_id='tab-completions'),
                        dbc.Tab(label='Pie Charts', tab_id='tab-pie'),
                        dbc.Tab(label='Heat Map', tab_id='tab-heatmap'),
                    ]),
                    html.Div(id='tab-content'),
                ]
                , style={'border':'1px solid black', 'padding':'10px'}
            )
        ])
    return content

def serve_layout():
    # try:
    page_layout = html.Div([
            serve_data_stores('url'), # change to 'url' before deploy
    ])
    # except:
    #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------

@app.callback(Output("tab-content", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-overview":
        overview = html.Div([
            dbc.Row([
                dbc.Col([html.Div(id='overview_div')], width=8),

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
                        # html.Label('Split MCC groups'),
                        # daq.ToggleSwitch(
                        #         id='toggle_mcc',
                        #         label=['Combined','Split'],
                        #         value=False
                        #     ),
                        html.Label('X-axis Category'),
                        dcc.Dropdown(
                            id='dropdown-xaxis',
                            options=[
                                {'label': i, 'value': bar_chart_options[i]} for i in bar_chart_options.keys()
                                ],
                            multi=False,
                            clearable=False,
                            value='None'
                        ),
                        html.Label('Facet Column:'),
                        dcc.Dropdown(
                            id='dropdown-facet-col',
                            options=[
                                {'label': i, 'value': bar_chart_options[i]} for i in bar_chart_options.keys()
                                ],
                            multi=False,
                            clearable=False,
                            value='None'
                        ),
                        html.Label('Facet Row:'),
                        dcc.Dropdown(
                            id='dropdown-facet-row',
                            options=[
                                {'label': i, 'value': bar_chart_options[i]} for i in bar_chart_options.keys()
                                ],
                            multi=False,
                            clearable=False,
                            value='None'
                        ),
                        ],width=2),
                ])
        ])
        return overview
    elif at == "tab-completions":
        completions = html.Div([
                html.Div(id='completions_section')
            ])
        return completions
    elif at == "tab-pie":
        pies = html.Div(id='pie_charts')
        return pies
    elif at == "tab-heatmap":
        heatmap = html.Div(id='heatmap')
        return heatmap
    return html.P("This shouldn't ever be displayed...")
# Define callback to update graph_stackedbar

# Toggle Stacked bar toggle_stackedbar graph_stackedbar
@app.callback(
    Output('overview_div', 'children'),
    Input('session_data', 'data')
)
def update_overview_section(data):
    return create_image_overview(pd.DataFrame.from_dict(data['imaging_overview']))

@app.callback(
    Output('graph_stackedbar_div', 'children'),
    Input('toggle_stackedbar', 'value'),
    Input('dropdown-xaxis', 'value'),
    Input('dropdown-facet-col', 'value'),
    Input('dropdown-facet-row', 'value'),
    State('session_data', 'data')
)
def update_stackedbar(type, xaxis, col, row, data):
    global mcc_dict
    # False = Count and True = Percent
    if type:
        type = 'Percent'
    else:
        type = 'Count'

    if xaxis =='None':
        x_col = None
    else:
        x_col = xaxis

    if col =='None':
        facet_col = None
    else:
        facet_col = col

    if row =='None':
        facet_row = None
    else:
        facet_row = row
    if (x_col and (facet_col or facet_row)) and (x_col == facet_col or x_col == facet_row) or (facet_col and facet_row and facet_col == facet_row):
        kids=[dbc.Alert("Chart dropdown selections can not be the same except for 'None'", color="warning")]
    else:
        qc = pd.DataFrame.from_dict(data['qc'])
        count_col='sub'
        color_col = 'rating'

        fig = bar_chart_dataframe(qc, mcc_dict, count_col, x_col, color_col, facet_col, facet_row = facet_row, chart_type=type)
        kids = [dcc.Graph(id='graph_stackedbar', figure=fig)]
    return kids


@app.callback(
    Output('completions_section', 'children'),
    Input('dropdown-sites', 'value'),
    State('session_data', 'data')
)
def update_image_report(sites, data):
    imaging = pd.DataFrame.from_dict(data['imaging'])
    df = imaging[imaging['site'].isin(sites.split(","))]
    completions = get_completions(df)
    return completions_table(completions)

@app.callback(
    Output('pie_charts', 'children'),
    Input('dropdown-sites', 'value'),
    State('session_data', 'data')
)
def update_pie(sites, data):
    imaging = pd.DataFrame.from_dict(data['imaging'])
    df = imaging[imaging['site'].isin(sites.split(","))]
    completions = get_completions(df)
    return create_pie_charts(completions)

@app.callback(
    Output('heatmap', 'children'),
    Input('dropdown-sites', 'value'),
    State('session_data', 'data')
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
                dcc.Graph(id='graph_heatmap', figure=fig_heatmap, style={'border':'1px solid blue'})
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
    app.run_server(debug=True, port=8030)
else:
    server = app.server

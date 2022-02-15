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
                suppress_callback_exceptions=True
                )

# ----------------------------------------------------------------------------
# DASH APP COMPONENT FUNCTIONS
# ----------------------------------------------------------------------------
def pie_scan(df, col):
    fig = px.pie(df, values='count', names=col, title=col,
         color_discrete_sequence=['SteelBlue','lightgrey']
        )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)
    return fig

def build_pie_col(df, col):
    figure_id = 'pie_' + col
    pie_col = dbc.Col([
        dcc.Graph(figure = pie_scan(df, col), id = figure_id)
    ], width = 4)
    return pie_col

def create_image_overview(df):
    overview_div = html.Div([
        dbc.Row([dbc.Col([
            html.H3('Overview')
        ])]),
        dbc.Row([
            dbc.Col([
                dt.DataTable(
                    id='tbl', data=df.to_dict('records'),
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

def create_image_reports(completions):
    image_reports_children = [
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
        dbc.Row([dbc.Col([
            html.H3('Percent of returns by Scan type')
        ])]),
        dbc.Row([
            build_pie_col(imaging, col) for col in icols[0:3]
        ])        ,
        dbc.Row([
            build_pie_col(imaging, col) for col in icols[3:6]
        ]),
    ]
    return image_reports_children

# build page parts
filter_box = html.Div(
    [
        dbc.Button("Filters", id="open-offcanvas", n_clicks=0),
        dbc.Offcanvas(
            html.P(
                "This is the content of the Offcanvas. "
                "Close it by clicking on the close button, or "
                "the backdrop."
            ),
            id="offcanvas",
            title="Filter Data",
            is_open=False,
            placement='end'
        ),
    ]
)


# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------
def create_content():
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
                            html.P('Version 1')], width=10),
                        dbc.Col([
                            dcc.Dropdown(
                                id='dropdown-sites',
                                options=[
                                    {'label': 'All Sites', 'value': ",".join(sites)},
                                    {'label': 'MCC1', 'value': 'UIC,UC,NS'},
                                    {'label': 'MCC2', 'value': 'UM, WS, NS' },
                                    {'label': 'University of Illinois at Chicago', 'value': 'UIC' },
                                    {'label': 'University of Chicago', 'value': 'UC' },
                                    {'label': 'NorthShore', 'value': 'NS' },
                                    {'label': 'University of Michigan', 'value': 'UM' },
                                    {'label': 'Wayne State University', 'value': 'WS' },
                                    {'label': 'Spectrum Health', 'value': 'NS' }
                                ],
                                value=",".join(sites)
                            ),
                        ], width=2),
                            # dbc.Col([filter_box],width=2)]),
                ], style={'border':'1px solid black'}),

                create_image_overview(imaging_overview),


                # dbc.Row([
                #     dbc.Col([html.H2('Image Reports')], width=2),
                #     dbc.Col([html.H5('for:')], width=1),
                #     dbc.Col([
                #         dcc.Dropdown(
                #             id='dropdown-sites',
                #             options=[
                #                 {'label': 'All Sites', 'value': ",".join(sites)},
                #                 {'label': 'MCC1', 'value': 'UIC,UC,NS'},
                #                 {'label': 'MCC2', 'value': 'UM, WS, NS' },
                #                 {'label': 'University of Illinois at Chicago', 'value': 'UIC' },
                #                 {'label': 'University of Chicago', 'value': 'UC' },
                #                 {'label': 'NorthShore', 'value': 'NS' },
                #                 {'label': 'University of Michigan', 'value': 'UM' },
                #                 {'label': 'Wayne State University', 'value': 'WS' },
                #                 {'label': 'Spectrum Health', 'value': 'NS' }
                #             ],
                #             value=",".join(sites)
                #         ),
                #     ], width=2),
                # ]),

                dbc.Row([
                    dbc.Col([
                        html.Div(id='image_reports')  ,
                    ],width=8),
                    dbc.Col([
                        dbc.Row([
                            html.Div(id='heatmap')
                        ])
                    ],width=4),
                ]),


            ]
                    , style={'border':'1px solid black', 'padding':'10px'}
                    )
                ])
    return content

def serve_layout():
    # try:
    page_layout = html.Div(
        create_content()
    )
    # except:
    #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------

# @app.callback(
#     Output("offcanvas", "is_open"),
#     Input("open-offcanvas", "n_clicks"),
#     [State("offcanvas", "is_open")],
# )
# def toggle_offcanvas(n1, is_open):
#     if n1:
#         return not is_open
#     return is_open

# Define callback to update graph
@app.callback(
    Output('image_reports', 'children'),
    [Input('dropdown-sites', 'value')]
)
def update_image_report(sites):
    df = imaging[imaging['site'].isin(sites.split(","))]
    completions = get_completions(df)
    return create_image_reports(completions)

@app.callback(
    Output('heatmap', 'children'),
    [Input('dropdown-sites', 'value')]
)
def update_image_report(sites):
    # f = generate_heat_matrix(get_heat_matrix_df(qc, sites), colors)
    # heatmap = dcc.Graph(figure=f)
    heatmap = html.Div(html.H3(sites))
    return heatmap


# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
else:
    server = app.server

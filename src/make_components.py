# Libraries
# Data
import pandas as pd # Dataframe manipulations
import math

# Dash Framework
import dash_bootstrap_components as dbc
# import dash_daq as daq #not currently installed on local
from dash import Dash, callback, clientside_callback, html, dcc, dash_table, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate

# Data Visualization
import plotly.express as px
from styling import *

# ----------------------------------------------------------------------------
# CUSTOM FUNCTIONS FOR DASH UI COMPONENTS
# ----------------------------------------------------------------------------

def pie_scan(df, value_col, col):
    fig = px.pie(df, values=value_col, names=col, title=col,
         color_discrete_sequence=['SteelBlue','lightgrey']
        )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)
    return fig

def build_pie_col(df, col):
    figure_id = 'pie_' + col
    pie_col = dbc.Col([
        dcc.Graph(figure = pie_scan(df, 'Count', col), id = figure_id)
    ], width = 4)
    return pie_col

def bar_chart_dataframe(df, mcc_dict, count_col, x_col, color_col = None, facet_col = None, facet_row = None, chart_type='Count'):
    # Get grouping cols for stacked bar
    if x_col is None:
        df['all'] = 1
        x_col ='all'
    bar_cols = [x_col]
    for col in [facet_col, facet_row]:
        if col:
            bar_cols.append(col)

    # Add color col to group cols
    group_cols = bar_cols.copy()
    if color_col:
        group_cols.append(color_col)
    df = df.merge(pd.DataFrame(mcc_dict), how='left', on='site')
    df = df[[count_col] + group_cols].groupby(group_cols).count().reset_index()
    df['N'] = df[[count_col] + bar_cols].groupby(bar_cols)[count_col].transform('sum')
    df['Percent'] = 100 * df[count_col] / df['N']

    col_rename_dict = {'site':'Site', 'mcc':'MCC', 'rating': 'Image Rating',
                       'sub':'Scan Count', 'N':'Category Count', 'scan':'Scan'}

    df.rename(columns = col_rename_dict, inplace=True)

    # cnvert variables
    fig_settings = {'count_col': count_col,
                    'y': count_col,
                    'x': x_col,
                    'color': color_col,
                    'facetcol': facet_col,
                    'facetrow': facet_row}
    for col in list(fig_settings.keys()):
        if fig_settings[col] and fig_settings[col] in list(col_rename_dict.keys()):
            fig_settings[col] = col_rename_dict[fig_settings[col]]

    if chart_type == 'Percent':
        fig_settings['y'] = 'Percent'

    fig = px.bar(df, y=fig_settings['y'], x=fig_settings['x'], color=fig_settings['color'],
                    facet_col = fig_settings['facetcol'], facet_row = fig_settings['facetrow'],
                     text=df[fig_settings['count_col']],
                     color_discrete_map={'red':'FireBrick',
                                         'yellow':'Gold',
                                         'green':'ForestGreen',
                                         'unavailable':'grey'},
                  category_orders={"Scan": ["T1w", "CUFF1", "CUFF2", "REST1", 'REST2'],
                                  'Image Rating': ["green","yellow","red"]}
                )

    # Update display text of legend
    rating_legend = {'green':'no known issues',
                      'yellow':'minor variations/issues; correctable' ,
                      'red':'significant variations/issues; not expected to be usable'}
    fig.for_each_trace(lambda t: t.update(name = rating_legend[t.name],
                                          legendgroup = rating_legend[t.name]
                                         ))
    fig.update_xaxes(title_text=' ')
    fig.update_xaxes(matches=None)
    fig.update_layout(legend=dict( orientation = 'h'))
    fig.update_layout(legend_title_text='')

    return fig

def generate_heat_matrix(df, colors):
    cut = len(df)
    fig = px.imshow(
            df.T,
            # height=cut*55,
            color_continuous_scale = colors,
            contrast_rescaling =  'infer'
    )
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=0, b=0, l=0, r=0),
        xaxis_nticks=cut + 1,
        yaxis_nticks=cut + 1,
        xaxis_side='top',
        xaxis_tickangle=-45
    ).update_xaxes(
        automargin=True,
    ).update_yaxes(
        automargin=True,
    )
    fig.update_traces(
        xgap = 3,
        ygap = 3
    )
    return fig

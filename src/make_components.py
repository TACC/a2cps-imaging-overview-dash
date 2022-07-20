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
import plotly.graph_objects as go
import plotly.express as px
from styling import *

# ----------------------------------------------------------------------------
# CUSTOM FUNCTIONS FOR DASH UI COMPONENTS
# ----------------------------------------------------------------------------

def make_pie_chart(pie_df, facet_col='Scan', facet_row=None):
    fig = px.pie(pie_df, values='BIDS', names='rating', color='rating',
                     facet_col = facet_col, facet_row = facet_row, 
                     color_discrete_map={'green':'ForestGreen',
                                 'yellow':'Gold',
                                 'red':'FireBrick',
                                 'N/A':'grey'},
                     category_orders={"Scan": ["T1", "REST1", "CUFF1", "CUFF2", "REST2", 'DWI'],
                                      "site": ["UI", "UC",'NS', 'UM','WS','SH','N/A']}
            )
    fig.update_traces(textinfo='percent', hoverinfo='value')

    if facet_col:
        fig.for_each_annotation(lambda a: a.update(text=a.text.replace(facet_col +"=", "")))

    if facet_row:
        fig.for_each_annotation(lambda a: a.update(text=a.text.replace(facet_row +"=", "")))
    fig.update_layout(showlegend=False)
    fig.update_traces(sort=False)

    return fig


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
                      'red':'significant variations/issues; not expected to be comparable'}
    fig.for_each_trace(lambda t: t.update(name = rating_legend[t.name],
                                          legendgroup = rating_legend[t.name]
                                         ))
    fig.update_xaxes(title_text=' ')
    fig.update_xaxes(matches=None)
    fig.update_layout(legend=dict( orientation = 'h'))
    fig.update_layout(legend_title_text='')

    return fig

def datatable_settings_multiindex(df, flatten_char = '_'):
    ''' Plotly dash datatables do not natively handle multiindex dataframes. This function takes a multiindex column set
    and generates a flattend column name list for the dataframe, while also structuring the table dictionary to represent the
    columns in their original multi-level format.

    Function returns the variables datatable_col_list, datatable_data for the columns and data parameters of
    the dash_table.DataTable'''
    datatable_col_list = []

    levels = df.columns.nlevels
    if levels == 1:
        for i in df.columns:
            datatable_col_list.append({"name": i, "id": i})
    else:
        columns_list = []
        for i in df.columns:
            col_id = flatten_char.join(i)
            datatable_col_list.append({"name": i, "id": col_id})
            columns_list.append(col_id)
        df.columns = columns_list

    datatable_data = df.to_dict('records')

    return datatable_col_list, datatable_data

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

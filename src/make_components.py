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

def generate_heat_matrix(df, colors):
    cut = len(df)
    fig = px.imshow(
            df,
            height=cut*55,
            color_continuous_scale = colors,
            contrast_rescaling =  'infer'
    )
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=0, b=0, l=0, r=0),
        # xaxis_nticks=cut + 1,
        # yaxis_nticks=cut + 1,
        xaxis_side='top',
        xaxis_tickangle=-45
    ).update_xaxes(
        automargin=True, visible=False
    ).update_yaxes(
        automargin=True,
    )
    fig.update_traces(
        xgap = 3,
        ygap = 3
    )
    return fig

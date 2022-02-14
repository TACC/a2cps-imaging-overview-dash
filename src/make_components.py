# Libraries
# Data
import pandas as pd # Dataframe manipulations
import math

# Dash Framework
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Dash, callback, clientside_callback, html, dcc, dash_table, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate

# Data Visualization
import plotly.express as px
from styling import *

# ----------------------------------------------------------------------------
# CUSTOM FUNCTIONS FOR DASH UI COMPONENTS
# ----------------------------------------------------------------------------

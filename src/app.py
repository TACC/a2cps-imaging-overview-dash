# ----------------------------------------------------------------------------
# PYTHON LIBRARIES
# ----------------------------------------------------------------------------
# Dash Framework
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Dash, callback, clientside_callback, html, dcc, dash_table, Input, Output, State, MATCH, ALL
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


# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------
def create_content():
    content = html.Div([
        html.P('The content of your App will go here.')
    ])
    return content

def serve_layout():
    try:
        page_layout = html.Div(
            create_content()
        )
    except:
        page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------

# Add callbacks to respond to user input here

# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
else:
    server = app.server

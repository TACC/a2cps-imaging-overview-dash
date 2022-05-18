import os # Operating system library
import pathlib # file paths

# ----------------------------------------------------------------------------
# CONFIG SETTINGS
# ----------------------------------------------------------------------------
DATA_PATH = pathlib.Path(__file__).parent.joinpath("data")
ASSETS_PATH = pathlib.Path(__file__).parent.joinpath("assets", "/assets")
REQUESTS_PATHNAME_PREFIX = os.environ.get("REQUESTS_PATHNAME_PREFIX", "/")
DATASTORE_URL = os.environ.get("DATASTORE_URL","http://a2cps_datastore:8050/api")
print("DATASTORE_URL:", DATASTORE_URL)

data_url_root ='https://api.a2cps.org/files/v2/download/public/system/a2cps.storage.community/reports/imaging'
# data_repository = 'https://api.a2cps.org/files/v2/download/public/system/a2cps.storage.community/reports/imaging'

init_api_data = {
        'imaging-log-latest.csv':{'date_request':None, 'request_status': None, 'date_data':None, 'data':None},
        'qc-log-latest.csv':{'date_request':None, 'request_status': None, 'data':None},
        # 'mriqc-group-bold-latest.csv':{'date_request':None, 'request_status': None, 'data':None}
           }

file_list = ['imaging-log-latest.csv', 'qc-log-latest.csv']

# ----------------------------------------------------------------------------
# SECURITY FUNCTION
# ----------------------------------------------------------------------------
def get_django_user():
    """
    Utility function to retrieve logged in username
    from Django
    """
    DJANGO_LOGIN_HOST = os.environ.get("DJANGO_LOGIN_HOST", None)
    SESSIONS_API_KEY = os.environ.get("SESSIONS_API_KEY", None)
    try:
        if not DJANGO_LOGIN_HOST:
            return True
        session_id = request.cookies.get('sessionid')
        if not session_id:
            raise Exception("sessionid cookie is missing")
        if not SESSIONS_API_KEY:
            raise Exception("SESSIONS_API_KEY not configured")
        api = "{django_login_host}/api/sessions_api/".format(
            django_login_host=DJANGO_LOGIN_HOST
        )
        response = requests.get(
            api,
            params={
                "session_key": session_id,
                "sessions_api_key": SESSIONS_API_KEY
            }
        )
        return response.json()
    except Exception as e:
        print(e)
        return None

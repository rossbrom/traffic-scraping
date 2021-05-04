# See api info at https://webtris.highwaysengland.co.uk/api/swagger/ui/index
#
# The API is located at http://webtris.highwaysengland.co.uk/api/{version}/{resource} where {version} is the version of the API (currently v1.0) and {resource} is the API resource requested.
#
# See worked example at https://github.com/departmentfortransport/ds-highwaysEnglandAPI-example/blob/master/python-example.ipynb



import datetime
import requests
import pandas as pd
import numpy as np
import plotly
import plotly.offline as py
import plotly.graph_objs as go
#import seaborn as sns
import folium
#from fbprophet import Prophet

# matplotlib inline
#plotly.offline.init_notebook_mode(connected=True)


def site_info(site_id):
    # Returns a dictionary giving info on the specified site
    r = requests.get('http://webtris.highwaysengland.co.uk/api/v1.0/sites/' +
                     str(site_id))
    return(r.json()['sites'][0])




def site_data(site , start_date, end_date ):
    # Returns a pandas dataframe containing traffic data in 15 minute chunks. Dates are string of the format ddmmyyyy
    more_pages = True
    page_num = 1
    data = []
    # Need to go through many pages. The returned json has a nextPage item if there is anothe page to collect
    while more_pages:
        r = requests.get('http://webtris.highwaysengland.co.uk/api/v1.0/reports/daily',
                         params = {'sites': str(site),
                                   'start_date': start_date,
                                   'end_date': end_date,
                                   'page': page_num,
                                   'page_size': 20000})     # 20000 data points per page
        json_response = r.json()
        invalid_response = 'Report Request Invalid. Please ensure all parameters are valid in line with API documentation.'
        if json_response == invalid_response:
            raise Exception('The API did not return any data. Check the site has data for the given dates' +
                            'and the arguments were supplied correctly. ' +
                            'Dates should be given as a string in ddmmyyyy format')
        for item in json_response['Rows']:
            data.append(item)
        print('Fetched ' + str(len(data)) + ' data points')
        page_num += 1
        links = [item['rel'] for item in json_response['Header']['links']]
        more_pages = 'nextPage' in links

    df = pd.DataFrame(data)
    # Make blanks -99, fill in later
    df = df.apply(lambda x: np.where(x == '', '-99', x))
    df_clean = pd.DataFrame({
        'Date': pd.to_datetime(df['Report Date']),
        'SiteId': site,
        'TotalFlow':  df['Total Volume'].astype(int),
        'LargeVehicleFlow': df['1160+ cm'].astype(int),
        'AverageSpeedMPH': df['Avg mph'].astype(int)
        })
    # Work out the start and end time of the period
    def extract_time_delta(str_time):
        hour = int(str_time.split(':')[0])
        minute = int(str_time.split(':')[1])
        offset = pd.Timedelta(hours = hour, minutes = minute)
        return(offset)

    mins_offset = [extract_time_delta(x) for x in df['Time Period Ending']]
    df_clean['EndTime'] = df_clean['Date'] + mins_offset
    df_clean['StartTime'] = df_clean['EndTime'] - pd.Timedelta(minutes = 15)
    # Make nans explicit
    df_clean.loc[df_clean['TotalFlow'] == -99 , 'TotalFlow'] = np.nan
    df_clean.loc[df_clean['LargeVehicleFlow'] == -99 , 'LargeVehicleFlow'] = np.nan
    df_clean.loc[df_clean['AverageSpeedMPH'] == -99 , 'AverageSpeedMPH'] = np.nan
    return(df_clean)

site = 6479
start_date = '01012008' # 01 Jan 2008
end_date = '31122016' # 31 Dec 2016

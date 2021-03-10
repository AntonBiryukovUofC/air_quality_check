import streamlit as st
import os
#import requests
import altair as alt
import numpy as np
import pandas as pd
#from dotenv import find_dotenv, load_dotenv


#def fetch_data_from_aq(city='Calgary', api_key=''):
#    query = f'https://api.waqi.info/feed/{city}/?token={api_key}'
#    data = requests.get(url=query,
#                        params={'token': api_key})
#
#    return data.json()


# load env variables

#load_dotenv(find_dotenv())
#AQ_TOKEN = os.getenv('AQ_API_KEY', None)
#N_IMG = int(os.getenv('N_IMG', "10"))


#emoji_json = requests.get(url="https://api.github.com/emojis").json()
#img_source = pd.DataFrame({"name": list(emoji_json.keys()), "url": list(emoji_json.values()),
#                           'x': np.random.uniform(-50, 50, len(emoji_json)),
#                           'y': np.random.uniform(-50, 50, len(emoji_json))})
#img_subset =img_source.sample(N_IMG)
#ch = alt.Chart(img_subset,width=500,height=500).mark_image(width=20,height=20).encode(
#    x='x',
#    y='y',
#    url='url'
#)

url = 'https://raw.githubusercontent.com/AntonBiryukovUofC/air_quality_check/luis-testing/src/data/waqi-covid19-airqualitydata-filtered.csv'
df = pd.read_csv(url,sep=",")
cities = df.City.unique()
df_cities = pd.DataFrame(cities, columns=['City'])
df_cities = df_cities.sort_values(by=['City'])
df_cities = df_cities.reset_index(drop=True)

option = st.selectbox(
    'Select City',
     df_cities['City'])

'You selected: ', option

mask = df['City'] == option


subset = df[mask]
subset = subset[["Date", "no2"]]
subset['Date']=pd.to_datetime(df['Date'])
#subset = subset.set_index('Date')


st.title('Air Quality check webapp')

st.markdown('This app is a skeleton for what my SPE 2021 Data Science mentees will work on.'
            'Specifically, we would like to compare the air quality levels pre/post COVID in a year-over-year plot '
            'as a baseline')
# get the api key

#data = fetch_data_from_aq(city='Houston', api_key=AQ_TOKEN)
#st.altair_chart(ch)
#st.write(data)
                 
#st.line_chart(subset)

ch = alt.Chart(subset).mark_line().encode(
    x='Date',
    y='no2'
)
st.altair_chart(ch)
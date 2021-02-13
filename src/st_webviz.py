import streamlit as st
import os
import requests
from dotenv import find_dotenv, load_dotenv

# load env variables

load_dotenv(find_dotenv())


def fetch_data_from_aq(city='Calgary', api_key=''):
    query = f'https://api.waqi.info/feed/{city}/?token={api_key}'
    data = requests.get(url=query,
                        params={'token': api_key})

    return data.json()


st.title('Air Quality check webapp')

st.markdown('This app is a skeleton for what my SPE 2021 Data Science mentees will work on.'
            'Specifically, we would like to compare the air quality levels pre/post COVID in a year-over-year plot '
            'as a baseline')
# get the api key
qa_api_key = os.getenv('AQ_API_KEY', None)

data = fetch_data_from_aq(city='Houston',api_key=qa_api_key)
st.write(data)
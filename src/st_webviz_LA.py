import streamlit as st
#import requests
import altair as alt
import numpy as np
import pandas as pd

import os
import psycopg2

from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import find_dotenv, load_dotenv
# You can generate a Token from the "Tokens Tab" in the UI
load_dotenv(find_dotenv())


def get_cities(conn):
    query_api = conn.query_api()
    query= '''
    from(bucket:"ts_spe")
        |> range(start: 2014-01-01T23:30:00Z, stop: 2020-12-31T00:00:00Z)
        |> filter(fn: (r) => r["_measurement"] == "luis-airquality")
        |> group(columns:["City"])
        |> distinct(column:"City")
        |> keep(columns: ["_value"])
        '''
    df = query_api.query_data_frame(org=os.environ['INFLUX_ORG'], query=query)
    return(df)



def get_aq_data(conn,city,metric):
    query_api = conn.query_api()
    query= '''
    from(bucket:"ts_spe")
        |> range(start: 2014-01-01T23:30:00Z, stop: 2020-12-31T00:00:00Z)
        |> filter(fn: (r) => r["_measurement"] == "luis-airquality")
        |> filter(fn: (r) => r["City"] == "{selection}")
        |> filter(fn: (r) => r["_field"] == "{field}")
        |> yield(name: "mean")
        '''.format(field=metric,selection=city)
    
    df = query_api.query_data_frame(org=os.environ['INFLUX_ORG'], query=query)
    return df

# Connect to influxDB with AQ data
influx_conn = InfluxDBClient(url=os.environ['INFLUX_HOST'], token=os.environ['INFLUX_TOKEN'])



# Obtain list of cities in DB
df_cities = get_cities(influx_conn)
# st.dataframe(df_cities)

# User selection of one city to display
option = st.selectbox(
    'Select City',
     df_cities['_value'])

'You selected: ', option

# # Obtain Air quality data of selected city
df = get_aq_data(influx_conn,option,'no2')
# st.dataframe(df.head(10))

# # Display chart of selected city
st.title('Air Quality check webapp')

st.markdown('This app is a skeleton for what my SPE 2021 Data Science mentees will work on.'
            'Specifically, we would like to compare the air quality levels pre/post COVID in a year-over-year plot '
            'as a baseline')


ch = alt.Chart(df).mark_line().encode(
    x='_time',
    y='_value'
)
st.altair_chart(ch)
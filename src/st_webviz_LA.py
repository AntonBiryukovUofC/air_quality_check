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

class InfluxWrapper:
    def __init__(
        self,
        hostname: str,
        token: str,
        org: str,
        bucket: str,
        **kwargs,
    ):
        self.hostname = hostname
        self.token = token
        self.org = org
        self.bucket = bucket
        self.conn = InfluxDBClient(url=self.hostname, token=self.token)
        self.query_api = self.conn.query_api()
    
    def get_cities(self):
        query= '''
        from(bucket:"{table}")
            |> range(start: 2014-01-01T23:30:00Z, stop: 2050-12-31T00:00:00Z)
            |> filter(fn: (r) => r["_measurement"] == "luis-airquality")
            |> group(columns:["City"])
            |> distinct(column:"City")
            |> keep(columns: ["_value"])
        '''.format(table=self.bucket)
        df = self.query_api.query_data_frame(org=self.org, query=query)
        return(df)
    
    def get_aq_data(self, city:str, metric:str):
        query= '''
        from(bucket:"{table}")
            |> range(start: 2014-01-01T23:30:00Z, stop: 2050-12-31T00:00:00Z)
            |> filter(fn: (r) => r["_measurement"] == "luis-airquality")
            |> filter(fn: (r) => r["City"] == "{selection}")
            |> filter(fn: (r) => r["_field"] == "{field}" or r["_field"] == "timeshift")
            |> yield(name: "mean")
        '''.format(table=self.bucket,field=metric,selection=city)
    
        df = self.query_api.query_data_frame(org=self.org, query=query)
        df = df.pivot(index="_time", columns="_field", values="_value")
        df["date"] = df.index -  pd.to_timedelta(df['timeshift'], unit='d')
        return df

ts_spe = InfluxWrapper(os.environ['INFLUX_HOST'] ,os.environ['INFLUX_TOKEN'], os.environ['INFLUX_ORG'],os.environ['INFLUX_BUCKET'])

# Obtain list of cities in DB
df_cities = ts_spe.get_cities()
# st.dataframe(df_cities)

# User selection of one city to display
option = st.selectbox(
    'Select City',
     df_cities['_value'])

'You selected: ', option

# # Obtain Air quality data of selected city
df = ts_spe.get_aq_data(option,'no2')
# st.dataframe(df.head(10))

# # Display chart of selected city
st.title('Air Quality check webapp')

st.markdown('This app is a skeleton for what my SPE 2021 Data Science mentees will work on.'
            'Specifically, we would like to compare the air quality levels pre/post COVID in a year-over-year plot '
            'as a baseline')


ch = alt.Chart(df).mark_line().encode(
    x='date',
    y='no2'
)
st.altair_chart(ch)
import streamlit as st
#import requests
import altair as alt
import numpy as np
import pandas as pd

from streamlit_folium import folium_static
import folium
from branca.colormap import linear, LinearColormap

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
        return df
    
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
        # workaround to avoid InfluxDB 30d timestamp age restriction
        df['date'] = df.index -  pd.to_timedelta(df['timeshift'], unit='d')
        df['year'] = pd.DatetimeIndex(df['date']).year
        df['month'] = pd.DatetimeIndex(df['date']).month
        df['DOY'] = df['date'].dt.dayofyear
        return df.loc[(df['year']>2015) & (df['year']<2021)]

ts_spe = InfluxWrapper(os.environ['INFLUX_HOST'] ,os.environ['INFLUX_TOKEN'], os.environ['INFLUX_ORG'],os.environ['INFLUX_BUCKET'])

# Obtain cities data for map
city_stats = pd.read_csv('..\src\data\city_stats.csv')
# st.dataframe(city_stats)

# Obtain list of cities in DB
df_cities = ts_spe.get_cities()
# st.dataframe(df_cities)

# # Display chart of selected city
st.title('Air Quality Check Webapp')

st.markdown('This app is a skeleton for what my SPE 2021 Data Science mentees will work on.'
            'Specifically, we would like to compare the air quality levels pre/post COVID in a year-over-year plot '
            'as a baseline. We are using free public data sources. For air quality data: https://aqicn.org/data-platform/covid19/, and for general information on world cities: https://simplemaps.com/data/world-cities')

# Map colored by metric
st.header('World Map of Air Pollution Changes in 2020')

st.markdown('This interactive chart shows the average drop in pollution levels (%) in major cities around the world in 2020 during COVID vs prior years. The larger drops are shown in red, the smallest changes in blue.'
            'Hovering the mouse over the city shows the name of the city and the drop in pollution.'
            'The map can be panned and zoomed.')
def make_map(field_to_color_by):
    main_map = folium.Map(location=(39, -77), zoom_start=1)
    colormap = linear.RdYlBu_08.scale(city_stats[field_to_color_by].quantile(0.05),
                                      city_stats[field_to_color_by].quantile(0.95))
    # if reverse_colormap[field_to_color_by]:
    #     colormap = LinearColormap(colors=list(reversed(colormap.colors)),
    #                               vmin=colormap.vmin,
    #                               vmax=colormap.vmax)
    colormap.add_to(main_map)
    # metric_desc = metric_descs[field_to_color_by]
    metric_desc = '% change 2020 vs baseline'
    # metric_unit = metric_units[field_to_color_by]
    colormap.caption = metric_desc
    colormap.add_to(main_map)
    for _, city in city_stats.iterrows():
        icon_color = colormap(city[field_to_color_by])
        # city_graph = city_graphs['for_map'][city.station_id][field_to_color_by]
        folium.CircleMarker(location=[city.lat, city.lng],
                    tooltip=f"{city.City}\n  value: {city[field_to_color_by]} %",
                    fill=True,
                    fill_color=icon_color,
                    # color=None,
                    color="gray",
                    weight=0.5,
                    fill_opacity=0.7,
                    radius=5,
                    # popup = folium.Popup().add_child(
                                            # folium.features.VegaLite(city_graph)
                                            # )
                    ).add_to(main_map)
    return main_map

main_map = make_map('no2')

folium_static(main_map)

# User selection of one city to display details
st.header('How Air Pollution Looks Like in your City')
option = st.selectbox(
    'Select City',
     df_cities['_value'])

'You selected: ', option

# # Obtain Air quality data of selected city
df = ts_spe.get_aq_data(option,'no2')
df_baseline = df.loc[df['year'] < 2020]
df_2020 = df.loc[df['year'] == 2020]
# st.dataframe(df.head(10))

# Line plot colored by year
st.header('Line Plot')

st.markdown('This interactive chart compares the daily pollution levels in the selected city over the years. The legend is clickable.'
            'When a year is selected, the corresponding line is highlighted in the plot. Multiple years can be '
            'selected for comparison by doing shift-click.')
st.markdown('In general, it can be observed that daily pollutant concentrations vary widely, but they tend to rise in the colder months and drop during the summer.'
            'Due to this seasonal effect, the pollution levels of 2020 are overlaid with previous years for a like to like comparison.')

highlight = alt.selection_multi(fields=['year'], bind='legend')

ch = alt.Chart(df).mark_line().encode(
    alt.X('DOY:Q', title='Day of the Year'),
    y=alt.Y('no2', title='no2 concentration'),
    color='year:N',
    opacity=alt.condition(highlight, alt.value(1), alt.value(0.2)),
).properties(
    width=650,
    height=300
).add_selection(
    highlight
)

st.altair_chart(ch)


# Plot of Baseline vs 2020 with CI band
st.header('Line Plot with CI Band')

st.markdown('This interactive chart compares the pollution levels in 2020 vs baseline. The red line represents 2020 daily pollution. The shadow area in blue is the baseline; it represents the'
            ' bootstrapped 95% confidence interval of the pollution levels observed from 2015-2019. The chart can be zoomed in/out using mouse scroller, or panned by click-drag the mouse left-button')

resize = alt.selection_interval(bind='scales')

line = alt.Chart(df_2020).mark_line().encode(
    alt.X('DOY:Q', title='Day of the Year'),
    y='mean(no2)',
    color=alt.value('red'),
).add_selection(
    resize
)

band = alt.Chart(df_baseline).mark_errorband(extent='ci').encode(
    alt.X('DOY:Q', title='Day of the Year'),
    y=alt.Y('no2', title='no2 concentration'),
).add_selection(
    resize
).properties(
    width=600,
    height=300
)

band + line


# Scatter plot of no2 vs DOY
st.header('Scatter Plot with Window Averages')

st.markdown('This chart provides an interactive exploration of pollution levels over the years. '
            'It includes a one-axis brush selection to easily compare the pollution averages in a particular time of the year, with previous years.')

brush = alt.selection_interval(encodings=['x'])

points2 = alt.Chart(df).mark_point().encode(
    alt.X('DOY:Q', title='Day of the Year'),
    alt.Y('no2:Q',
        title='no2 concentration',
    ),
    color=alt.condition(brush, 'year:N', alt.value('lightgray')),
).properties(
    width=550,
    height=300
).add_selection(
    brush
)

bars = alt.Chart(df).mark_bar().encode(
    x='mean(no2)',
    y='year:N',
    color='year:N',
).transform_filter(
    brush
).properties(
    width=550,
)

st.altair_chart(points2 & bars)

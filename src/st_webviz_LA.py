import streamlit as st
#import requests
import altair as alt
import numpy as np
import pandas as pd

import os
import psycopg2

#DATABASE_URL = os.environ['DATABASE_URL']
DATABASE_URL = 'postgres://zcnfhwcgogldfu:ddb669eda26b1ebba6acfae9b0be68da7de1254c7c48446c2181b0e017878e26@ec2-54-161-239-198.compute-1.amazonaws.com:5432/dbluphji0qouqq'

conn = psycopg2.connect(DATABASE_URL, sslmode='require')


def get_cities(conn):
    """
    Tranform a SELECT query into a pandas dataframe
    """
    cursor = conn.cursor()
    try:
        cursor.execute("select distinct city from aqdata order by city")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        cursor.close()
        return 1
    
    # Naturally we get a list of tupples
    tupples = cursor.fetchall()
    cursor.close()
    
    # We just need to turn it into a pandas dataframe
    df = pd.DataFrame(tupples, columns=['city'])
    return df


def get_air_data(conn,city,metric):
    """
    Tranform a SELECT query into a pandas dataframe
    """
    cursor = conn.cursor()
    sql_statement = "Select date, {field} from aqdata where city = '{selection}' order by date".format(
                field=metric,
                selection=city)
    try:
        cursor.execute(sql_statement)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        cursor.close()
        return 1
    
    # Naturally we get a list of tupples
    tupples = cursor.fetchall()
    cursor.close()
    
    # We just need to turn it into a pandas dataframe
    df = pd.DataFrame(tupples, columns=['date',metric])
    return df

# Execute the "SELECT *" query
df_cities = get_cities(conn)
#df_cities.head()

#url = 'https://raw.githubusercontent.com/AntonBiryukovUofC/air_quality_check/luis-testing/src/data/waqi-covid19-airqualitydata-filtered.csv'
#df = pd.read_csv(url,sep=",")
#cities = df.City.unique()
#df_cities = pd.DataFrame(cities, columns=['City'])
#df_cities = df_cities.sort_values(by=['City'])
#df_cities = df_cities.reset_index(drop=True)

option = st.selectbox(
    'Select City',
     df_cities['city'])

'You selected: ', option


df = get_air_data(conn,option,'no2')

#mask = df['City'] == option

#df = postgresql_to_dataframe(conn, "Select date, no2 from aqdata where city = option order by date", column_names)

#subset = df[mask]
#subset = subset[["Date", "no2"]]
#subset['Date']=pd.to_datetime(df['Date'])
#subset = subset.set_index('Date')


st.title('Air Quality check webapp')

st.markdown('This app is a skeleton for what my SPE 2021 Data Science mentees will work on.'
            'Specifically, we would like to compare the air quality levels pre/post COVID in a year-over-year plot '
            'as a baseline')

#st.dataframe(df)

ch = alt.Chart(df).mark_line().encode(
    x='date',
    y='no2'
)
st.altair_chart(ch)
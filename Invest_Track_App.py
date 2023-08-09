import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import numpy as np
from datetime import datetime

st.set_page_config(page_title='Raghus Folio Dashboard')
st.title('My Folio Dashboard 📊')
st.sidebar.subheader('Load the Invest Tracker File')
uploaded_file=st.sidebar.file_uploader('Select the Folio Data File', type='xlsx')

@st.cache_data
def get_price_data(df):
    for i in range(len(df)):
        cp= yf.download(df.at[i,'Symbol'],period="1d",interval="1d")['Adj Close']
        df.loc[i,'Current_Price']=round(cp.sum(),2)
    return df

if uploaded_file:
    st.markdown('----')
    df=pd.read_excel(uploaded_file,engine='openpyxl')
    
    folio_list=df["Folio"].unique().tolist()
    folio_list.insert(0,'All')
    select_folio=st.sidebar.selectbox('Select Folio',folio_list,index=0)
    
    if select_folio=="All":
        grouping_fields=["Folio","Hold Time","Sector","MSTAR"]
    else:
        grouping_fields=["Symbol","Hold Time","Sector","MSTAR"]
    groupby_column=st.sidebar.selectbox('Select Grouping Field',grouping_fields,index=0)
    
    if select_folio=='All':
        df_folio=df
    else:
        df_folio=(df.loc[df['Folio'] == select_folio])
    df_folio.reset_index(drop=True, inplace=True)
    no_of_stocks=len(df_folio)
    
    df_folio=get_price_data(df_folio)
       
    df_folio["Investment"]=df_folio["Quantity"]*df_folio["Purchase Price"]
    df_folio['Present_Value']=df_folio['Quantity']*df_folio['Current_Price']
    df_folio['Gain_Loss']=df_folio['Present_Value']-df_folio['Investment']
        
    output_columns=['Investment','Present_Value','Gain_Loss']
    df_grouped = df_folio.groupby(by=[groupby_column],as_index=False)[output_columns].sum()
    df_grp_sorted=df_grouped.sort_values("Investment").reset_index(drop=True)
        
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("**:red[Number of Stocks Held]**",df_grouped.shape[0])
    col2.metric("**:red[Total Investment Made]**","${:,.0f}".format(df_folio["Investment"].sum()))
    col3.metric("**:red[Total Present value]**","${:,.0f}".format(df_folio["Present_Value"].sum()))
    col4.metric("**:red[Net Gain_Loss]**","${:,.0f}".format(df_folio["Gain_Loss"].sum()))

    fig=px.bar(df_grp_sorted,
        x=groupby_column,
        y='Gain_Loss',
        color='Gain_Loss',
        color_continuous_scale=['red','yellow','green'],
        template='plotly_white',
        title=f'<b style="color: cyan;"> Gain_Loss by {groupby_column}</b>'
    )
    st.plotly_chart(fig)
    st.markdown('----')
    st.markdown("**:red[Investment and Gain/Loss Summary by Stock]**")
    st.dataframe(df_grp_sorted)

if st.sidebar.checkbox("Clear All"):
    st.cache_data.clear()
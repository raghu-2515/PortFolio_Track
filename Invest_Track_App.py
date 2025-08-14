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

# Function to fetch stock details using yfinance
def fetch_stock_data(tickers):
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            data[ticker] = {
                'Current_Price': info.get('currentPrice'),  # Current price
                'Prev_Close': info.get('regularMarketPreviousClose'),  # Previous close price
                'Sector': info.get('sector'),
                'Industry': info.get('industry'),
                'Analyst_Target': info.get('targetMeanPrice')  # Analyst price target
                }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    return pd.DataFrame.from_dict(data, orient='index')

if uploaded_file:
    st.markdown('----')
    df=pd.read_excel(uploaded_file,engine='openpyxl')
    
    folio_list=df["Folio"].unique().tolist()
    folio_list.insert(0,'All')
    select_folio=st.sidebar.selectbox('Select Folio',folio_list,index=0)
    
    if select_folio=="All":
        grouping_fields=["Folio","Hold Time","Sector","Industry"]
    else:
        grouping_fields=["Symbol","Hold Time","Sector","Industry"]
    groupby_column=st.sidebar.selectbox('Select Grouping Field',grouping_fields,index=0)
    
    if select_folio=='All':
        df_folio=df
    else:
        df_folio=(df.loc[df['Folio'] == select_folio])
    df_folio.reset_index(drop=True, inplace=True)
    no_of_stocks=len(df_folio)

    unique_tickers = df_folio['Symbol'].unique()
    stock_data = fetch_stock_data(unique_tickers)

    df_folio = df_folio.merge(stock_data, left_on='Symbol', right_index=True, how='left')
    
    #df_folio=get_price_data(df_folio)
    #st.dataframe(df_folio)
       
    df_folio["Investment"]=df_folio["Quantity"]*df_folio["Purchase Price"]
    df_folio['Present_Value']=df_folio['Quantity']*df_folio['Current_Price']
    df_folio['Gain_Loss']=df_folio['Present_Value']-df_folio['Investment']
    df_folio['Net_Gain_Loss']=np.where(df_folio['Hold Time']<1,df_folio['Gain_Loss']*0.75,df_folio['Gain_Loss']*0.85)
    df_folio['Net_Present_Value']=df_folio['Investment']+df_folio['Net_Gain_Loss']
    df_folio['Daily_Change']=(df_folio['Current_Price']-df_folio['Prev_Close'])*df_folio['Quantity']
    df_folio['Expect_Gain']=df_folio['Quantity']*df_folio['Analyst_Target']-df_folio['Investment']
    df_folio.loc[df_folio['Hold Time']<0.25,'Hold Time']=0.25
    df_folio['Net_CAGR']=round(((df_folio['Net_Present_Value']/df_folio['Investment'])**(1/(df_folio['Hold Time']))-1)*100,1)

    #st.dataframe(df_folio[['Symbol','Investment','Present_Value','Net_Present_Value','Net_Gain_Loss','Hold Time','Net_CAGR']])

    Weighted_Hold_Time = df_folio.groupby(by=[groupby_column],as_index=True).apply(lambda x: np.average(x['Hold Time'],weights=x['Investment'])).reset_index(drop=True)
        
    output_columns=['Investment','Net_Present_Value','Net_Gain_Loss','Expect_Gain','Daily_Change']
    df_grouped = round(df_folio.groupby(by=[groupby_column],as_index=False)[output_columns].sum(),0)
    df_grouped['Avg_Hold_Time'] = Weighted_Hold_Time.values.round(2)
    df_grouped['Net_CAGR'] = round(((df_grouped['Net_Present_Value']/df_grouped['Investment'])**(1/(df_grouped['Avg_Hold_Time']))-1)*100,1)

    df_grp_sorted=df_grouped.sort_values("Investment",ascending=False).reset_index(drop=True)
    col1, col2, col3, col4 = st.columns(4)
   
    col1.metric("**:red[# of Holdings]**",df_grouped.shape[0])
    col2.metric("**:red[Total Investment]**","${:,.0f}".format(df_folio["Investment"].sum()))
    col3.metric("**:red[Total Present value]**","${:,.0f}".format(df_folio["Net_Present_Value"].sum()),round(df_folio["Daily_Change"].sum(),0))

    col4.metric("**:red[Net Gain_Loss]**","${:,.0f}".format(df_folio["Net_Gain_Loss"].sum()))
    
    fig=px.bar(
        df_grp_sorted,
        x=groupby_column,
        y=["Net_Gain_Loss", "Expect_Gain"],
        barmode='group',
        #color='Net_Gain_Loss',
        #color_continuous_scale=['red', 'yellow', 'green'],
        template='plotly_white',
        title=f'<b style="color: cyan;"> Gain_Loss by {groupby_column}</b>',
    )


    st.plotly_chart(fig)
    st.markdown('----')
    
    def bubble_chart():
        fig = px.scatter(
        df_grp_sorted,
        x=groupby_column,                # X-axis: category
        y='Net_Gain_Loss',               # Y-axis: Gain loss values
        size='Investment',           # Bubble size: Investment column
        color='Net_CAGR',           # Bubble color gradient based on Gain loss
        color_continuous_scale='RdYlGn',  # Red to Green color gradient
        hover_name=groupby_column,       # Bubble names: category column
        title="Bubble Chart: Investment vs Gain Loss",
        size_max=60,                     # Maximum bubble size
        labels={'category':groupby_column,'Gain/Loss':'Net_Gain_Loss','Investment':'Investment'}
        )
        
        st.plotly_chart(fig)
        st.markdown('----')

    #bubble_chart()

    # Create an area chart (treemap) using Plotly Express
    fig = px.treemap(
    df_grp_sorted,
    path=[groupby_column],  # Hierarchical path (only Stock here)
    values="Investment",  # Determines box sizes
    color="Net_Gain_Loss",  # Determines box colors
    # color values below Zero on a red scale and above Zero on a green scale
    color_continuous_midpoint=0,  # Midpoint for color scale
    color_continuous_scale=px.colors.diverging.RdYlGn,  # Red-Yellow-Green scale
    #color_continuous_scale="RdYlGn",  # Red-Yellow-Green scale
    hover_data={
        "Investment": True,
        "Net_Gain_Loss": True,
    },
    labels={
        "Stock": groupby_column,
        "Investment": "Investment",
        "Net Gain/Loss": "Net_Gain_Loss",
    },
    title="Area Chart: Present Values vs Investment vs Gain Loss"
    )

    # Display the treemap in Streamlit
    st.plotly_chart(fig)

    #bubble_chart()

    st.markdown('----')
    st.markdown("**:red[Investment and Gain/Loss Details by Holding]**")
    st.dataframe(df_grp_sorted[[groupby_column,'Investment','Net_Present_Value','Daily_Change','Net_Gain_Loss','Avg_Hold_Time','Net_CAGR']].sort_values('Investment',ascending=False).reset_index(drop=True))

    if st.sidebar.checkbox("Clear All"):
        st.cache_data.clear()
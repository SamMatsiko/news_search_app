import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from afinn import Afinn
import matplotlib.pyplot as plt

# Replace 'your_api_key_here' with your actual NewsAPI key
API_KEY = '4cf74a050be14bdfaae4f38c7d23cd27'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

def fetch_news(keyword):
    params = {
        'qInTitle': keyword,  # This will search for the keyword in the title
        'apiKey': API_KEY,
        'sortBy': 'relevancy',
        'language': 'en',
        'pageSize': 100  # Number of results per request
    }
    response = requests.get(NEWS_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get('articles', [])
    else:
        st.error(f"Failed to fetch news articles: {response.json().get('message', 'Unknown error')}")
        return []



afn = Afinn()



def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

st.title("AKAS News Search App")

keyword = st.text_input("Enter a keyword to search for news:")

if keyword:
    st.write(f"Results for '{keyword}' in title:")
    news_results = fetch_news(keyword)
    if news_results:
        articles_data = [{
            'Source': article['source']['name'],
            'Published At': article['publishedAt'],
            'Title': article['title'],
            'Description': article['description'],
            'URL': article['url']          
            
            
        } for article in news_results]
        
        df = pd.DataFrame(articles_data)
        df=df[df['Source']!='[Removed]']        
        df.loc[:,'Sentiment'] = [afn.score(str(article)) for article in df.loc[:,'Title']]
        
        st.dataframe(df)


        # Time-series plot of publication dates
        df['Published At'] = pd.to_datetime(df['Published At'])
        df['Date'] = df['Published At'].dt.date
        date_counts = df['Date'].value_counts().sort_index()
        
        # Calculate average sentiment per day
        daily_sentiment = df.groupby('Date')['Sentiment'].mean()

        st.subheader("Volume of News Articles and Average Sentiment Over Time")
        fig, ax = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

        # Volume of articles plot
        ax[0].plot(date_counts.index, date_counts.values, marker='o', linestyle='-', color='b')
        ax[0].set_ylabel('Number of Articles')
        ax[0].set_title(f'Volume of News Articles for "{keyword}" Over Time')
        ax[0].grid(True)

        # Average sentiment plot
        ax[1].plot(daily_sentiment.index, daily_sentiment.values, marker='o', linestyle='-', color='g')
        ax[1].set_xlabel('Date')
        ax[1].set_ylabel('Average Sentiment')
        ax[1].set_title('Average Sentiment Over Time')
        ax[1].grid(True)

        plt.xticks(rotation=45)
        st.pyplot(fig)
        
        
        
        
        
        
        # Convert DataFrame to Excel and add download button
        exceldf=df[['Source','Date','Title','URL','Sentiment']]
        excel_data = convert_df_to_excel(exceldf)
        st.download_button(
            label="Download data as Excel",
            data=excel_data,
            file_name='news_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("No news articles found.")

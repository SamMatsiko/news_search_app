import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from textblob import TextBlob

# Replace 'your_api_key_here' with your actual NewsAPI key
API_KEY = '4cf74a050be14bdfaae4f38c7d23cd27'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

def fetch_news(keywords, search_in_title):
    query = ' OR '.join(keywords)
    params = {
        'qInTitle' if search_in_title else 'q': query,  # Search in title or anywhere
        'apiKey': API_KEY,
        'sortBy': 'publishedAt',  # Sort by publication date
        'language': 'en',
        'pageSize': 100  # Number of results per request
    }
    response = requests.get(NEWS_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get('articles', [])
    else:
        st.error(f"Failed to fetch news articles: {response.json().get('message', 'Unknown error')}")
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

st.title("News Search App")

keywords_input = st.text_input("Enter keywords to search for news (separated by spaces or commas):")
search_type = st.radio("Search in:", ("Title", "Anywhere"))

if keywords_input:
    keywords = [keyword.strip() for keyword in keywords_input.replace(',', ' ').split()]
    st.write(f"Results for keywords in {search_type.lower()}: {', '.join(keywords)}")
    
    search_in_title = search_type == "Title"
    news_results = fetch_news(keywords, search_in_title)
    
    if news_results:
        articles_data = [{
            'Title': article['title'],
            'Description': article['description'],
            'URL': article['url'],
            'Published At': article['publishedAt'],
            'Source': article['source']['name'],
            'Sentiment Polarity': analyze_sentiment(article['description'])[0] if article['description'] else None,
            'Sentiment Subjectivity': analyze_sentiment(article['description'])[1] if article['description'] else None
        } for article in news_results]
        
        df = pd.DataFrame(articles_data)
        
        # Add a multiselect for news outlet filter
        news_outlets = df['Source'].unique().tolist()
        selected_outlets = st.multiselect('Select news outlets to filter:', ['All'] + news_outlets, default=['All'])
        
        if 'All' not in selected_outlets:
            df = df[df['Source'].isin(selected_outlets)]
        
        st.dataframe(df)

        # Time-series plot of publication dates
        df['Published At'] = pd.to_datetime(df['Published At'])
        df['Date'] = df['Published At'].dt.date
        date_counts = df['Date'].value_counts().sort_index()
        
        # Calculate average sentiment per day
        daily_sentiment = df.groupby('Date')['Sentiment Polarity'].mean()

        st.subheader("Volume of News Articles and Average Sentiment Over Time")
        fig, ax = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

        # Volume of articles plot
        ax[0].plot(date_counts.index, date_counts.values, marker='o', linestyle='-', color='b')
        ax[0].set_ylabel('Number of Articles')
        ax[0].set_title(f'Volume of News Articles for keywords in {search_type.lower()}: {", ".join(keywords)} Over Time')
        ax[0].grid(True)

        # Average sentiment plot
        ax[1].plot(daily_sentiment.index, daily_sentiment.values, marker='o', linestyle='-', color='g')
        ax[1].set_xlabel('Date')
        ax[1].set_ylabel('Average Sentiment Polarity')
        ax[1].set_title('Average Sentiment Polarity Over Time')
        ax[1].grid(True)

        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Convert DataFrame to Excel and add download button
        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="Download data as Excel",
            data=excel_data,
            file_name='news_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("No news articles found.")

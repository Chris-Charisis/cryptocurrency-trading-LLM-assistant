import requests
import json
from datetime import datetime, timedelta
from newsplease import NewsPlease

# Functions for function calling tool of Assistants API
def get_detailed_crypto_data(crypto_id):
    """
    Fetches detailed data of a cryptocurrency in JSON format from CoinGecko.
    """
    try:
        crypto_id = crypto_id[0].lower()
        # Base URL for CoinGecko API
        base_url = "https://api.coingecko.com/api/v3"

        # Get general market data including current price, market cap, and volume
        market_data_url = f"{base_url}/coins/{crypto_id}"
        market_data_response = requests.get(market_data_url)
        market_data = market_data_response.json()

        # Get historical data (e.g., 30 days ago)
        date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime('%d-%m-%Y')
        historical_data_url = f"{base_url}/coins/{crypto_id}/history?date={date_30_days_ago}"
        historical_data_response = requests.get(historical_data_url)
        historical_data = historical_data_response.json()

        # Prepare the detailed data dictionary
        detailed_data = {
            'current_price': market_data['market_data']['current_price']['usd'],
            'market_cap': market_data['market_data']['market_cap']['usd'],
            '24h_volume': market_data['market_data']['total_volume']['usd'],
            'price_change_percentage': {
                '24h': market_data['market_data']['price_change_percentage_24h'],
                '7d': market_data['market_data']['price_change_percentage_7d'],
                '14d': market_data['market_data']['price_change_percentage_14d'],
                '30d': market_data['market_data']['price_change_percentage_30d'],
                '60d': market_data['market_data']['price_change_percentage_60d'],
                '1y': market_data['market_data']['price_change_percentage_1y'],
            },
            'historical_data': {
                'price_usd_30_days_ago': historical_data.get('market_data', {}).get('current_price', {}).get('usd', None)
            },
            'community_data': market_data['community_data'],
            'status_updates': market_data['status_updates']
        }

        # Token information (if applicable)
        if 'contract_address' in market_data:
            detailed_data['token_info'] = {
                'platform': market_data.get('asset_platform_id'),
                'contract_address': market_data.get('contract_address')
            }
    # handle the exception            
    except Exception as error:
        print(error) 
        detailed_data = ""
    
    return detailed_data


def get_crypto_news(news_api_url):
    """
    Collects the URL from latest news related to one or more cryptocurrencies using News API.
    Then, it iterates all the URLs to collect the full text and appends it to the final message.
    """
    # Collect the URLs
    response = requests.get(news_api_url[0])
    articles = response.json().get('articles', [])
    
    full_article_text = ""
    for article in articles:
        # Check if the final message exceeds a safe length for the model input token limitation. Rule-of-thumb 3 words = 4 tokens. Limitation is 4096 input tokens.
        if len((full_article_text).split(" "))>2700:
            break
        # Collect the full text of the news URL
        extracted_article = NewsPlease.from_url(article["url"])
        # Cases where there is a problem with the extracted text, either to small or no accessible
        try:
            if not extracted_article or len((extracted_article.maintext).split(" "))<200:
                continue
        except:
            continue
            
        full_article_text += article["url"] + "\n" + extracted_article.maintext + "\n\n"

    return full_article_text
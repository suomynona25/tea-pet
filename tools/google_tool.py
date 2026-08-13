from langchain_core.tools import tool
from dotenv import load_dotenv
import json
import os
import serpapi

@tool
def google_tool(search_query:str) -> str:
    """
    Performs a google search given a search query.

    Args:
        search_query: Search terms to use in google search
    """
    clean_results = []
    try:
        load_dotenv()
        searcher = serpapi.Client(api_key = os.getenv('SERPAPI_API_KEY'))
        results = searcher.search({
            'engine':'google',
            'q': search_query
        })
        #Only take the title, link, snippet from the organic results
        for res in results['organic_results']:
            clean_res = {
                'title': res.get('title'),
                'link': res.get('link'),
                'snippet': res.get('snippet')
            }
            clean_results.append(clean_res)
    except serpapi.HTTPError as e:
        if e.status_code == 401: # Invalid API key
            print(e.error)
        elif e.status_code == 400: # Missing required parameter
            pass
        elif e.status_code == 429: # Exceeds the hourly throughput limit OR account run out of searches
            pass
    except serpapi.TimeoutError as e:
        # Handle timeout
        print(f"The request timed out: {e}")
    return json.dumps(clean_results)

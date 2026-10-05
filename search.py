import urllib.request
import json
import urllib.parse

def search_papers(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={encoded_query}&per-page=10"
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:test@example.com'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        for w in data.get("results", []):
            print(f"- *{w.get('title')}* ({w.get('publication_year')}) - [doi:{w.get('doi')}]({w.get('doi')})")

print("--- Grade Prediction ---")
search_papers("Educational Data Mining Grade Prediction Student Performance Machine Learning")
print("\n--- Clustering ---")
search_papers("Educational Data Mining Student Profiling Clustering Unsupervised")

import urllib.request
import json

dois = [
    "10.1186/s40561-022-00192-z",
    "10.1155/2024/4067721",
    "10.3389/fpsyg.2021.698490",
    "10.1007/s10639-020-10189-1",
    "10.1007/s40745-021-00341-0",
    "10.3390/sym15091679",
    "10.1109/access.2023.3332818",
    "10.1088/1757-899x/263/3/032002",
    "10.1007/s11423-012-9235-8",
    "10.23919/mipro.2017.7973517"
]

def devert_abstract(inv_idx):
    if not inv_idx: return ""
    words = max([max(pos) for pos in inv_idx.values()]) + 1
    out = [""] * words
    for word, positions in inv_idx.items():
        for pos in positions:
            if pos < words: out[pos] = word
    return " ".join(out)

for doi in dois:
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:test@example.com'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            print(f"--- {data.get('title')} ---")
            print("Abstract:", devert_abstract(data.get('abstract_inverted_index')))
            print("")
    except Exception as e:
        print(f"Error fetching {doi}: {e}")

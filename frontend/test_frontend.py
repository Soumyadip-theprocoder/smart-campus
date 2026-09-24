import urllib.request
import re

try:
    html = urllib.request.urlopen("https://smart-campus-1-rrf1.onrender.com/").read().decode("utf-8")
    js_match = re.search(r'src="/assets/(index-[^"]+\.js)"', html)
    if js_match:
        js_url = f"https://smart-campus-1-rrf1.onrender.com/assets/{js_match.group(1)}"
        js_content = urllib.request.urlopen(js_url).read().decode("utf-8")
        
        backend_match = re.search(r'https://[a-zA-Z0-9-]+\.onrender\.com', js_content)
        if backend_match and "smart-campus-1-rrf1" not in backend_match.group(0):
            print(f"Backend URL found: {backend_match.group(0)}")
        else:
            print("No backend Render URL found in JS bundle.")
            
        if "localhost:8000" in js_content:
            print("Localhost URL found in JS bundle.")
    else:
        print("Could not find JS bundle.")
except Exception as e:
    print(f"Error: {e}")

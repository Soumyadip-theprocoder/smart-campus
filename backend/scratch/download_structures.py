import urllib.request
import os
import time

base_url = 'https://makautexam.net/aicte_details/'
os.makedirs('scratch/pdfs', exist_ok=True)

pdf_files = [
    'Syllabus/BTECH.pdf',
    'CourseStructure/CSE.pdf',
    'CourseStructure/IT.pdf',
    'CourseStructure/ECE.pdf',
    'CourseStructure/EE.pdf',
    'CourseStructure/ME.pdf',
    'CourseStructure/CE.pdf',
    'CourseStructure/AIML20.pdf',
    'CourseStructure/AIDS20.pdf',
    'CourseStructure/CSBS20.pdf',
    'CourseStructure/CSEDS20.pdf',
    'CourseStructure/CSECS22.pdf',
    'CourseStructure/CSEIOT22.pdf',
    'CourseStructure/BT.pdf',
    'CourseStructure/CHE.pdf',
    'CourseStructure/AE.pdf',
    'CourseStructure/BME.pdf',
    'CourseStructure/AEIE.pdf',
    'CourseStructure/EEE.pdf',
    'CourseStructure/FT.pdf',
    'CourseStructure/TT.pdf',
    'CourseStructure/LT.pdf',
    'CourseStructure/APM.pdf',
    'CourseStructure/CVE.pdf',
    'CourseStructure/RBT20.pdf',
    'CourseStructure/EECE25.pdf',
]

for rel_path in pdf_files:
    fname = os.path.basename(rel_path)
    dest = os.path.join('scratch/pdfs', fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"Already exists: {fname} ({os.path.getsize(dest)} bytes)")
        continue
    url = base_url + rel_path
    print(f"Downloading {url} -> {dest}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(dest, 'wb') as f:
            f.write(data)
        print(f"  Saved {fname} ({len(data)} bytes)")
        time.sleep(0.5)
    except Exception as e:
        print(f"  Failed to download {rel_path}: {e}")

import urllib.request
import pypdf
import re
import os

base_url = 'https://makautexam.net/aicte_details/'
os.makedirs('scratch/pdfs', exist_ok=True)

def inspect_dept_structure(pdf_rel_path, dept_title):
    url = base_url + pdf_rel_path
    local_path = os.path.join('scratch/pdfs', os.path.basename(pdf_rel_path))
    if not os.path.exists(local_path):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
            with open(local_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return
            
    reader = pypdf.PdfReader(local_path)
    print(f"\n=== {dept_title} ({pdf_rel_path}) : {len(reader.pages)} pages ===")
    text = ''
    for p in reader.pages:
        text += '\n' + p.extract_text()
        
    print(f"Total characters: {len(text)}")
    for line in text.splitlines():
        if any(w in line.lower() for w in ['semester i', 'semester ii', 'semester iii', 'semester iv', 'semester v', 'semester vi', 'semester vii', 'semester viii', 'first semester', 'second semester', 'third semester', 'fourth semester', 'fifth semester', 'sixth semester', 'seventh semester', 'eighth semester']):
            print("  [SEM HEADER]:", line.strip())

targets = [
    ('CourseStructure/CSE.pdf', 'CSE'),
    ('CourseStructure/IT.pdf', 'IT'),
    ('CourseStructure/ECE.pdf', 'ECE'),
    ('CourseStructure/EE.pdf', 'EE'),
    ('CourseStructure/ME.pdf', 'ME'),
    ('CourseStructure/CE.pdf', 'CE'),
    ('CourseStructure/BT.pdf', 'Biotech'),
    ('CourseStructure/CHE.pdf', 'Chemical'),
    ('CourseStructure/AIML20.pdf', 'AIML'),
    ('CourseStructure/AEIE.pdf', 'AEIE'),
]

for rel, title in targets:
    inspect_dept_structure(rel, title)

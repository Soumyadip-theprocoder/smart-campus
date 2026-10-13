import pypdf
import re
import os

ROMAN_SEMS = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
    'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4, 'FIFTH': 5, 'SIXTH': 6, 'SEVENTH': 7, 'EIGHTH': 8,
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8
}

def clean_code(code_str):
    code_str = re.sub(r'\s+', '', code_str).strip()
    return code_str

def parse_pdf_courses(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    full_text = ''
    for p in reader.pages:
        full_text += '\n' + p.extract_text()
        
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    courses = []
    current_sem = None
    
    # regex for semester header
    sem_re = re.compile(r'(?:Semester\s+([0-9IVX]+)|([A-Za-z]+)\s+Semester)', re.IGNORECASE)
    
    # regex for course code pattern:
    # E.g.: PCC-CS301, ESC 301, BSC 301, HSMC 301, PCC-CS 402, PC-EC301, PC-EE301, PC-ME301, etc.
    code_re = re.compile(
        r'^(?:[0-9]{1,2}\s+)?(?:[A-Za-z &,/]+\s+)?'
        r'((?:BS|ES|HM|PC|PE|OE|MC|PW|PCC|ESC|BSC|HSMC|PEC|OEC|PROJ)[ -]+(?:[A-Z]{1,4}\s*)?[0-9]{3}[A-Z0-9/]*|[A-Z]{2,4}[0-9]{3}[A-Z0-9/]*)'
        r'\s+(.+?)(?:\s+([0-9\.\-]+)\s+([0-9\.\-]+)\s+([0-9\.\-]+)\s+([0-9\.]+))?$',
        re.IGNORECASE
    )
    
    for idx, line in enumerate(lines):
        # Check semester header
        m_sem = sem_re.search(line)
        if m_sem:
            val = m_sem.group(1) or m_sem.group(2)
            val_clean = val.upper()
            if val_clean in ROMAN_SEMS:
                current_sem = ROMAN_SEMS[val_clean]
            continue
            
        if not current_sem:
            continue
            
        m_code = code_re.search(line)
        if m_code:
            raw_code = m_code.group(1).strip()
            title = m_code.group(2).strip()
            credits_str = m_code.group(6)
            
            # Avoid headers like "Code Course Title"
            if 'COURSE' in raw_code.upper() or 'TITLE' in title.upper():
                continue
                
            code = clean_code(raw_code)
            
            # Check next line for wrapped title if title is very short or ends with & or preposition
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                if not code_re.search(next_line) and not sem_re.search(next_line) and not re.match(r'^[0-9]\s+[0-9]', next_line):
                    if len(next_line) < 40 and not any(k in next_line.lower() for k in ['total', 'credits', 'theory', 'practical']):
                        title += ' ' + next_line
                        
            try:
                credits_val = float(credits_str) if credits_str else 3.0
            except:
                credits_val = 3.0
                
            is_lab = '9' in code or 'lab' in title.lower() or 'workshop' in title.lower() or 'practice' in title.lower()
            subject_type = 'lab' if is_lab else ('seminar' if 'project' in title.lower() or 'internship' in title.lower() else 'lecture')
            
            courses.append({
                'semester': current_sem,
                'code': code,
                'name': title,
                'credits': credits_val,
                'type': subject_type,
            })
            
    return courses

for f in ['scratch/pdfs/CSE.pdf', 'scratch/pdfs/IT.pdf', 'scratch/pdfs/ECE.pdf', 'scratch/pdfs/EE.pdf', 'scratch/pdfs/ME.pdf', 'scratch/pdfs/CE.pdf']:
    c = parse_pdf_courses(f)
    print(f"\n{os.path.basename(f)} -> {len(c)} courses parsed")
    sems_found = sorted(list(set(x['semester'] for x in c)))
    print(f"  Semesters found: {sems_found}")
    for item in c[:4]:
        print(f"    Sem {item['semester']} | {item['code']:15} | {item['name']:35} | {item['credits']} cr | {item['type']}")

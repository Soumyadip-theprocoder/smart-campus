import pypdf
import re
import os

ROMAN_MAP = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4, 'FIFTH': 5, 'SIXTH': 6, 'SEVENTH': 7, 'EIGHTH': 8,
    '1ST': 1, '2ND': 2, '3RD': 3, '4TH': 4, '5TH': 5, '6TH': 6, '7TH': 7, '8TH': 8
}

PDF_DEPT_MAP = {
    'CSE.pdf': 'B.Tech in Computer Science & Engineering',
    'IT.pdf': 'B.Tech in Information Technology',
    'ECE.pdf': 'B.Tech in Electronics & Communication Engineering',
    'EE.pdf': 'B.Tech in Electrical Engineering',
    'ME.pdf': 'B.Tech in Mechanical Engineering',
    'CE.pdf': 'B.Tech in Civil Engineering',
    'AIML20.pdf': 'B.Tech in Artificial Intelligence & Machine Learning',
    'AIDS20.pdf': 'B.Tech in Artificial Intelligence & Data Science',
    'CSBS20.pdf': 'B.Tech in Computer Science & Business Systems',
    'CSEDS20.pdf': 'B.Tech in Computer Science & Engineering (Data Science)',
    'CSECS22.pdf': 'B.Tech in Computer Science & Engineering (Cyber Security)',
    'CSEIOT22.pdf': 'B.Tech in Computer Science & Engineering (Internet of Things)',
    'BT.pdf': 'B.Tech in Biotechnology',
    'CHE.pdf': 'B.Tech in Chemical Engineering',
    'AE.pdf': 'B.Tech in Automobile Engineering',
    'BME.pdf': 'B.Tech in Biomedical Engineering',
    'AEIE.pdf': 'B.Tech in Applied Electronics & Instrumentation Engineering',
    'EEE.pdf': 'B.Tech in Electrical & Electronics Engineering',
    'FT.pdf': 'B.Tech in Food Technology',
    'TT.pdf': 'B.Tech in Textile Technology',
    'LT.pdf': 'B.Tech in Leather Technology',
    'APM.pdf': 'B.Tech in Apparel & Production Management',
    'CVE.pdf': 'B.Tech in Civil & Environmental Engineering',
    'RBT20.pdf': 'B.Tech in Robotics',
    'EECE25.pdf': 'B.Tech in Electrical & Computer Engineering',
}

def extract_sem(line):
    # e.g. "Semester III", "SemesterIV", "3rd Semester", "Second Year Third Semester", "2nd Year: 3rd Semester"
    m = re.search(r'(?:Semester\s*([0-9IVX]+|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth)|([0-9](?:st|nd|rd|th)?|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|[IVX]+)\s*Semester)', line, re.IGNORECASE)
    if m:
        token = (m.group(1) or m.group(2)).upper().strip()
        # Clean ordinals
        token = re.sub(r'(ST|ND|RD|TH)$', '', token)
        return ROMAN_MAP.get(token)
    return None

def extract_courses_from_pdf(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    full_text = ''
    for p in reader.pages:
        full_text += '\n' + p.extract_text()

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    courses = []
    current_sem = None
    
    # Combined regex to match all AICTE MAKAUT course code variations
    code_pattern = re.compile(
        r'^(?:[0-9]{1,2}[\.\)]\s*)?'                               # optional sl no (1., 2), 1)
        r'(?:(?:Basic Science|Engineering Science|Professional|Humanities|Mandatory|Open Elective|Project)[A-Za-z &,/]*\s+)?' # optional category
        r'('                                                      # Capture group 1: Course Code
        r'(?:BS|ES|HM|PC|PE|OE|MC|PW|PCC|ESC|BSC|HSMC|PEC|OEC|PROJ)[ -]*(?:[A-Z]{1,4}[ -]*)?[0-9]{3}[A-Z0-9/]*'
        r'|[A-Z]{2,4}\s*\([A-Z]+\)\s*[0-9]{3}[A-Z0-9/]*'
        r'|(?:EC|EE|ME|CE|CS|IT|BT|CH|CHE|AE|FT|TT|LT)[0-9]{3}[A-Z0-9/]*'
        r')'
        r'\s+'
        r'([A-Za-z0-9 &(),.\-\'\"]+?)'                            # Capture group 2: Course Title
        r'(?:\s+([0-9\.\-]+)\s+([0-9\.\-]+)\s+([0-9\.\-]+)(?:\s+[0-9\.\-]+)?\s+([0-9\.]+))?$', # L T P [Total] Credits
        re.IGNORECASE
    )

    for idx, line in enumerate(lines):
        sem_found = extract_sem(line)
        if sem_found:
            current_sem = sem_found
            continue

        if not current_sem:
            continue

        m = code_pattern.search(line)
        if m:
            raw_code = m.group(1).strip()
            raw_title = m.group(2).strip()
            credits_str = m.group(6)

            if 'CODE' in raw_code.upper() or 'FIELD' in raw_title.upper() or 'THEORY' in raw_title.upper() or 'PRACTICAL' in raw_title.upper():
                continue

            # Clean code
            clean_code = re.sub(r'\s+', '', raw_code)

            # Check for multi-line title append
            title = raw_title
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                if not code_pattern.search(next_line) and not extract_sem(next_line):
                    if len(next_line) < 45 and not any(k in next_line.lower() for k in ['total', 'credits', 'theory', 'practical', 'contact', 'sl no']):
                        title += ' ' + next_line

            try:
                credits_val = float(credits_str) if credits_str else 3.0
            except:
                credits_val = 3.0

            is_lab = '9' in clean_code or 'lab' in title.lower() or 'workshop' in title.lower() or 'practice' in title.lower()
            subject_type = 'lab' if is_lab else ('seminar' if 'project' in title.lower() or 'internship' in title.lower() else 'lecture')

            courses.append({
                'semester': current_sem,
                'code': clean_code,
                'name': title.strip(),
                'credits': credits_val,
                'type': subject_type,
            })

    return courses

total_parsed = 0
for fname, dept_name in PDF_DEPT_MAP.items():
    fpath = os.path.join('scratch/pdfs', fname)
    if not os.path.exists(fpath):
        continue
    c = extract_courses_from_pdf(fpath)
    sems = sorted(list(set(x['semester'] for x in c)))
    print(f"{fname:15} -> {len(c):3} courses | Sems: {sems} | {dept_name}")
    total_parsed += len(c)

print(f"\nTotal courses parsed across all branch PDFs: {total_parsed}")

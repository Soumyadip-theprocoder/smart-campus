from html.parser import HTMLParser
import re

html_path = r'C:\Users\Soumy\.gemini\antigravity-ide\brain\9f186b82-7747-4758-8b0d-0d83de658881\.system_generated\steps\1120\content.md'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Simple regex-based table row parser
row_pattern = re.compile(r'<tr>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
tag_cleaner = re.compile(r'<[^>]+>')

rows = row_pattern.findall(html)
print(f'Total <tr> found: {len(rows)}')

programs = []
for r in rows:
    cells = cell_pattern.findall(r)
    if len(cells) >= 12:
        clean_cells = [tag_cleaner.sub('', c).strip() for c in cells]
        name = clean_cells[1]
        code = clean_cells[2]
        session = clean_cells[3]
        
        # Course structure link
        struct_match = href_pattern.search(cells[4])
        struct_link = struct_match.group(1) if struct_match else None
        
        # Semester links
        sem_links = {}
        for s_idx in range(1, 9):
            if len(cells) > 4 + s_idx:
                sem_match = href_pattern.search(cells[4 + s_idx])
                if sem_match:
                    sem_links[s_idx] = sem_match.group(1)
                    
        programs.append({
            'name': name,
            'code': code,
            'session': session,
            'struct': struct_link,
            'sems': sem_links,
        })

print(f'Parsed {len(programs)} program rows.')

latest_progs = {}
for p in programs:
    name = p['name']
    session = p['session']
    if not name or name.startswith('Program'):
        continue
    if name not in latest_progs:
        latest_progs[name] = p
    elif any(yr in session for yr in ['2018', '2019', '2020', '2021', '2022', '2023', '2024']):
        if p['struct'] or p['sems']:
            latest_progs[name] = p

print(f'\nUnique programs: {len(latest_progs)}')
for name, p in sorted(latest_progs.items()):
    c = p['code']
    s = p['session']
    st = str(p['struct'])
    sems = list(p['sems'].keys())
    print(f"{c:4} | {s:10} | {name:55} | struct: {st:30} | sems: {sems}")

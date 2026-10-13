import urllib.request
import os
import time

base_url = 'https://makautexam.net/aicte_details/'
os.makedirs('scratch/pdfs', exist_ok=True)

pdf_files = [
    # Core Structures
    'Syllabus/BTECH.pdf',
    'CourseStructure/CSE.pdf',
    'CourseStructure/CSE20.pdf',
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
    'CourseStructure/CSEAIML20.pdf',
    'CourseStructure/CSEITCS20.pdf',
    'CourseStructure/CSD21.pdf',
    'CourseStructure/DS20.pdf',
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
    'CourseStructure/CVE23.pdf',
    'CourseStructure/RBT20.pdf',
    'CourseStructure/EECE25.pdf',
    'CourseStructure/BTECH_ECS23.pdf',
    'CourseStructure/ICE.pdf',
    'CourseStructure/CurriculumBAE26.pdf',
    # Architecture, Pharmacy, Hotel Mgmt, BBA, BCA
    'CourseStructure/BARCH.pdf',
    'CourseStructure/BHMCT.pdf',
    'CourseStructure/BPHARM21.pdf',
    'CourseStructure/BPHARM20.pdf',
    'CourseStructure/BPHARM.pdf',
    'CourseStructure4/BBA23.pdf',
    'CourseStructure/BBA25.pdf',
    'CourseStructure4/BCA23.pdf',
    'CourseStructure4/CURRICULUM_BCA.pdf',
    'CourseStructure/BCA25.pdf',
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

success = 0
failed = 0

for rel_path in pdf_files:
    fname = os.path.basename(rel_path)
    # Use distinct fname if conflicts (like BBA23 vs BBA25)
    dest = os.path.join('scratch/pdfs', fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"[EXISTS] {fname} ({os.path.getsize(dest)} bytes)")
        success += 1
        continue

    url = base_url + rel_path
    print(f"[DOWNLOAD] {url} -> {dest}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) > 1000:
            with open(dest, 'wb') as f:
                f.write(data)
            print(f"  Saved {fname} ({len(data)} bytes)")
            success += 1
        else:
            print(f"  Empty or too small ({len(data)} bytes)")
            failed += 1
        time.sleep(0.3)
    except Exception as e:
        print(f"  Failed to download {rel_path}: {e}")
        failed += 1

print(f"\nDone: {success} succeeded, {failed} failed.")

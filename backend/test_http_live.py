import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

def run_live_http_verification():
    print("=" * 80)
    print("LIVE HTTP BACKEND INTEGRATION VERIFICATION")
    print("=" * 80)

    # Step 1: Login to get JWT access token
    login_url = f"{BASE_URL}/api/auth/login/"
    login_data = json.dumps({
        "email": "admin@smartcampus.edu",
        "password": "admin123"
    }).encode("utf-8")

    req = urllib.request.Request(
        login_url,
        data=login_data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            login_resp = json.loads(resp.read().decode("utf-8"))
            access_token = login_resp.get("access") or login_resp.get("token") or login_resp.get("tokens", {}).get("access")
            print(f"[OK] Logged in successfully. Token received (length={len(str(access_token))})")
    except Exception as e:
        print(f"[ERROR] Failed to log in via HTTP: {e}")
        return

    auth_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Helper function
    def get_api(endpoint):
        url = f"{BASE_URL}{endpoint}"
        r = urllib.request.Request(url, headers=auth_headers)
        with urllib.request.urlopen(r, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    # Step 2: Fetch departments
    print("\n[Test 1] GET /api/scheduler/departments/")
    status, depts_data = get_api("/api/scheduler/departments/")
    print(f"  Status: {status} | Total Departments: {depts_data.get('count')}")
    sample_dept = depts_data.get("results", [])[0]
    print(f"  Sample: [{sample_dept.get('dept_id')}] {sample_dept.get('name')} | Faculty: {sample_dept.get('faculty_count')} | Students: {sample_dept.get('student_count')} | Courses: {sample_dept.get('subject_count')}")

    # Step 3: Fetch all departments (all=true)
    print("\n[Test 2] GET /api/scheduler/departments/?all=true")
    status, all_depts = get_api("/api/scheduler/departments/?all=true")
    print(f"  Status: {status} | Departments list length: {len(all_depts)}")

    # Step 4: Fetch subjects (Page 1)
    print("\n[Test 3] GET /api/scheduler/subjects/?page=1")
    status, sub_data = get_api("/api/scheduler/subjects/?page=1")
    print(f"  Status: {status} | Total subjects in catalog: {sub_data.get('count')}")
    for s in sub_data.get("results", [])[:3]:
        print(f"    - [{s.get('code')}] {s.get('name')} | Sem {s.get('semester')} | Credits: {s.get('credits')} | Type: {s.get('subject_type')}")

    # Step 5: Filter subjects by CSE department (ID: 206, DEP-0151)
    print("\n[Test 4] GET /api/scheduler/subjects/?department=206 (CSE)")
    status, cse_subs = get_api("/api/scheduler/subjects/?department=206")
    print(f"  Status: {status} | CSE Courses Count: {cse_subs.get('count')}")
    for s in cse_subs.get("results", [])[:3]:
        print(f"    - [{s.get('code')}] {s.get('name')} (Sem {s.get('semester')})")

    # Step 6: Filter subjects by Mechanical Engineering (DEP-0167)
    mech_dept = next((d for d in all_depts if d.get("dept_id") == "DEP-0167"), None)
    if mech_dept:
        mech_id = mech_dept.get("id")
        print(f"\n[Test 5] GET /api/scheduler/subjects/?department={mech_id} (Mechanical)")
        status, mech_subs = get_api(f"/api/scheduler/subjects/?department={mech_id}")
        print(f"  Status: {status} | Mechanical Courses Count: {mech_subs.get('count')}")
        for s in mech_subs.get("results", [])[:3]:
            print(f"    - [{s.get('code')}] {s.get('name')} (Sem {s.get('semester')})")

    # Step 7: Filter subjects by Semester 3
    print("\n[Test 6] GET /api/scheduler/subjects/?semester=3")
    status, sem3_subs = get_api("/api/scheduler/subjects/?semester=3")
    print(f"  Status: {status} | Semester 3 Courses Count: {sem3_subs.get('count')}")

    # Step 8: Search subjects by query "Machine Learning"
    print("\n[Test 7] GET /api/scheduler/subjects/?search=Machine+Learning")
    status, ml_subs = get_api("/api/scheduler/subjects/?search=Machine%20Learning")
    print(f"  Status: {status} | 'Machine Learning' Search Results: {ml_subs.get('count')}")
    for s in ml_subs.get("results", [])[:3]:
        print(f"    - [{s.get('code')}] {s.get('name')} (Sem {s.get('semester')})")

    print("\n" + "=" * 80)
    print("ALL LIVE HTTP INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_live_http_verification()

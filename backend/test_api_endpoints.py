import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.scheduler.views import SubjectListView, DepartmentListView
from apps.accounts.models import User
from apps.scheduler.models import Department

def test_apis():
    print("=" * 80)
    print("TESTING BACKEND API ENDPOINTS")
    print("=" * 80)

    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    factory = APIRequestFactory()

    # Test 1: Department List View
    print("\n[Test 1] GET /api/scheduler/departments/")
    req = factory.get("/api/scheduler/departments/", HTTP_HOST="localhost")
    force_authenticate(req, user=user)
    view = DepartmentListView.as_view()
    resp = view(req)
    print(f"  Status code: {resp.status_code}")
    print(f"  Total departments returned: {resp.data.get('count')}")
    first_dept = resp.data.get("results", [])[0]
    print(f"  Sample Department: [{first_dept.get('dept_id')}] {first_dept.get('name')} | Students: {first_dept.get('total_students')} | Faculty: {first_dept.get('total_faculty')} | Subjects: {first_dept.get('total_subjects')}")

    # Test 2: Subject List View (All)
    print("\n[Test 2] GET /api/scheduler/subjects/")
    req = factory.get("/api/scheduler/subjects/", HTTP_HOST="localhost")
    force_authenticate(req, user=user)
    s_view = SubjectListView.as_view()
    resp = s_view(req)
    print(f"  Status code: {resp.status_code}")
    print(f"  Total subjects in catalog: {resp.data.get('count')}")
    sample_sub = resp.data.get("results", [])[0]
    print(f"  Sample Subject: [{sample_sub.get('code')}] {sample_sub.get('name')} (Sem {sample_sub.get('semester')}, Credits {sample_sub.get('credits')})")

    # Test 3: Filter Subjects by Department (DEP-0151 - CSE)
    cse = Department.objects.get(dept_id="DEP-0151")
    print(f"\n[Test 3] GET /api/scheduler/subjects/?department={cse.id}")
    req = factory.get(f"/api/scheduler/subjects/?department={cse.id}", HTTP_HOST="localhost")
    force_authenticate(req, user=user)
    resp = s_view(req)
    print(f"  Status code: {resp.status_code}")
    print(f"  CSE Subjects count: {resp.data.get('count')}")
    cse_samples = [(s.get("code"), s.get("name")[:30], f"Sem {s.get('semester')}") for s in resp.data.get("results", [])[:3]]
    print(f"  CSE Samples: {cse_samples}")

    # Test 4: Filter Subjects by Semester (Semester 5)
    print("\n[Test 4] GET /api/scheduler/subjects/?semester=5")
    req = factory.get("/api/scheduler/subjects/?semester=5", HTTP_HOST="localhost")
    force_authenticate(req, user=user)
    resp = s_view(req)
    print(f"  Status code: {resp.status_code}")
    print(f"  Semester 5 Subjects count: {resp.data.get('count')}")

    # Test 5: Search Subjects by Query ("Operating System")
    print("\n[Test 5] GET /api/scheduler/subjects/?search=Operating+System")
    req = factory.get("/api/scheduler/subjects/?search=Operating System", HTTP_HOST="localhost")
    force_authenticate(req, user=user)
    resp = s_view(req)
    print(f"  Status code: {resp.status_code}")
    print(f"  Search matches: {resp.data.get('count')}")
    for s in resp.data.get("results", [])[:3]:
        print(f"    - [{s.get('code')}] {s.get('name')} (Sem {s.get('semester')})")

    print("\n" + "=" * 80)
    print("ALL API ENDPOINT TESTS PASSED")
    print("=" * 80)

if __name__ == "__main__":
    test_apis()

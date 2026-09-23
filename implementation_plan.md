# Smart Campus — Error Audit & Fix Plan

After a comprehensive review of the entire codebase (backend + frontend), I've identified the following errors and issues that need to be rectified.

---

## 🔴 Critical Errors (Build-Breaking / Runtime Crashes)

### 1. Frontend Build Script Fails — `tsc` with No TypeScript Files

**File:** [`package.json`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/package.json)

The `build` script runs `tsc && vite build`, but the project uses **`.jsx` files** (plain JavaScript + JSX), not TypeScript `.tsx` files. The `tsconfig.json` has no JSX configuration, and `react`/`react-dom` are not even listed in `package.json`, so `tsc` finds zero inputs and fails immediately:

```
error TS18003: No inputs were found in config file 'tsconfig.json'.
Specified 'include' paths were '["src"]' and 'exclude' paths were '[]'.
```

**Fix:** Remove `tsc` from the build command since this is a pure JS project. The Vite build alone (`npx vite build`) succeeds.

---

### 2. Missing `react` and `react-dom` in `package.json` Dependencies

**File:** [`package.json`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/package.json)

`react` and `react-dom` are **not listed** as dependencies, even though they are core requirements. The project works currently because they happen to be installed as transitive dependencies of `react-router-dom`, but this is fragile — a `npm ci` in a clean environment or a future dependency update could break the entire app.

**Fix:** Add `react` and `react-dom` to `dependencies`.

---

### 3. Missing `vite.config.js` — No React JSX Plugin

**Root:** [`frontend/`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend)

There is **no `vite.config.js`** file at all. While Vite has built-in JSX support via esbuild for `.jsx` files, the standard React Vite setup requires `@vitejs/plugin-react` for:
- Fast Refresh (HMR in development)
- Proper JSX runtime configuration

Without it, `npm run dev` **won't have Hot Module Replacement** — every change requires a full reload, and certain JSX edge cases may fail.

**Fix:** Add a `vite.config.js` with the React plugin, and add `@vitejs/plugin-react` to devDependencies.

---

### 4. Missing `__init__.py` Files Could Cause Import Errors

**Files:** Various app directories

Need to verify `__init__.py` files exist in all Django app directories and their subdirectories. Missing ones would cause `ModuleNotFoundError` when Django tries to discover apps.

---

## 🟡 Significant Bugs (Logic / Data Errors)

### 5. `StudentClassAttendancePage` — Week Navigation Uses Broken Date Math

**File:** [`StudentClassAttendancePage.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/attendance/StudentClassAttendancePage.jsx#L15-L23)

```jsx
const d = new Date();
const day = d.getDay() || 7;
if (day !== 1) {
  d.setHours(-24 * (day - 1)); // ← BUG: setHours with negative values
}
```

`setHours(-24 * (day - 1))` is an unreliable way to subtract days. It sets the **hours** field to a negative value, which JavaScript then normalizes, but this approach breaks across DST transitions and is semantically wrong. The correct approach is `d.setDate(d.getDate() - (day - 1))`.

**Fix:** Replace with proper date subtraction using `setDate()`.

---

### 6. `FacultyDashboard` — Filtering Timetable by String Name is Fragile

**File:** [`FacultyDashboard.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/dashboard/FacultyDashboard.jsx#L50-L52)

```jsx
const myTimetable = (timetableRes.data...).filter(
  t => t.faculty_name === `${user.first_name} ${user.last_name}`
);
```

This compares against a **concatenated string** of `user.first_name + " " + user.last_name`, but the API returns `faculty_name` from `get_full_name()` which trims/handles names differently. If a faculty member has a middle name, extra spaces, or the name format changes, this filter silently returns zero results. The correct approach would be to filter by `faculty_id` from the profile.

**Fix:** Use `faculty_id` from the profile to match timetable entries by the `subject.faculty` ID instead of name comparison.

---

### 7. `FacultyDashboard` & `FacultySubjectsPage` — Subject Filtering by `faculty` ID Mismatch

**Files:** [`FacultyDashboard.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/dashboard/FacultyDashboard.jsx#L44-L46), [`FacultySubjectsPage.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/dashboard/FacultySubjectsPage.jsx#L34-L36)

```jsx
const mySubjects = subjects.filter(s => s.faculty === facultyId);
```

The `SubjectSerializer` returns `faculty` as the faculty profile's **PK** (integer), and `facultyId` comes from `meRes.data.profile?.id`. This is correct in principle, but the subject serializer's `faculty` field is a write-field for the FK. The serializer includes `faculty` which is the FK integer — so this works. However, if the `MeView` profile shape ever changes, this breaks silently.

> **Verdict:** This is fragile but **currently works**. I'll note it but won't change the logic.

---

### 8. `tsconfig.json` — Leftover TypeScript Config With No Purpose

**File:** [`tsconfig.json`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/tsconfig.json)

The tsconfig has settings like `verbatimModuleSyntax`, `erasableSyntaxOnly`, `noUnusedLocals`, and `noUnusedParameters` — none of which apply to `.jsx` files. This file is inert (Vite ignores it for `.jsx`) but it creates confusion and makes the build fail.

**Fix:** Remove `tsconfig.json` entirely since the project is pure JavaScript, or replace it with a minimal `jsconfig.json` for IDE support.

---

## 🟢 Minor Issues (Best Practices / Robustness)

### 9. `AdminDashboard` — Hardcoded Mock Chart Data

**File:** [`AdminDashboard.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/dashboard/AdminDashboard.jsx#L63-L64)

```jsx
const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const chartData = [85, 92, 78, 88, 95]; // Mock data!
```

The weekly attendance chart shows **hardcoded** values, not real data from the API. This is misleading. Since the backend doesn't have a per-day breakdown endpoint, we should at least mark this visually as "sample data" or remove it.

**Fix:** Add "(Sample)" label to the chart title to indicate mock data.

---

### 10. `LoginPage` — Redirects Admin to `/admin/courses` Instead of `/admin`

**File:** [`LoginPage.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/auth/LoginPage.jsx#L22)

After admin login, the redirect is `navigate('/admin/courses')` but the sidebar's first link is "Dashboard" pointing to `/admin`. This is inconsistent with the UI hierarchy.

**Fix:** Change admin redirect to `/admin`.

---

### 11. Communication Serializer — Missing `posted_by_name` Field

**File:** [`communication/serializers.py`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/backend/apps/communication/serializers.py)

The frontend references `notice.posted_by_name` in `AdminDashboard.jsx` line 207, but the `NoticeSerializer` doesn't include this field. Need to check if it's there.

---

## Proposed Changes

### Frontend

---

#### [MODIFY] [`package.json`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/package.json)
- Add `react` and `react-dom` to dependencies
- Add `@vitejs/plugin-react` to devDependencies
- Fix build script: change `"tsc && vite build"` to `"vite build"`
- Remove `typescript` from devDependencies

#### [NEW] [`vite.config.js`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/vite.config.js)
- Create Vite config with React plugin for proper HMR/Fast Refresh

#### [DELETE] [`tsconfig.json`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/tsconfig.json)
- Remove dead TypeScript config; replace with `jsconfig.json` for IDE support

#### [NEW] [`jsconfig.json`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/jsconfig.json)
- Minimal config for IDE path resolution and IntelliSense

#### [MODIFY] [`StudentClassAttendancePage.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/attendance/StudentClassAttendancePage.jsx)
- Fix week calculation: replace `setHours()` hack with proper `setDate()` arithmetic

#### [MODIFY] [`LoginPage.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/auth/LoginPage.jsx)
- Change admin redirect from `/admin/courses` to `/admin`

#### [MODIFY] [`AdminDashboard.jsx`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src/features/dashboard/AdminDashboard.jsx)
- Add "(Sample)" label to hardcoded chart

---

### Backend

---

#### [MODIFY] [`communication/serializers.py`](file:///c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/backend/apps/communication/serializers.py)
- Add `posted_by_name` field to `NoticeSerializer` so frontend can display it

---

## Verification Plan

### Automated Tests
```bash
# Frontend: Verify build succeeds
cd frontend && npm install && npm run build

# Backend: Verify Django check passes
cd backend && python manage.py check --deploy 2>&1 || python manage.py check
```

### Manual Verification
- Confirm `npm run build` succeeds without errors
- Confirm `npm run dev` starts with HMR working
- Verify all identified bugs are fixed

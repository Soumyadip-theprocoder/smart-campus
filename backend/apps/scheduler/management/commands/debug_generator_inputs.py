"""
Management Command: debug_generator_inputs

Inspect, audit, validate, and replay generator input payloads sent from the frontend.
Eliminates the need for slow browser subagents during scheduler development and debugging.

Usage:
    python manage.py debug_generator_inputs --last
    python manage.py debug_generator_inputs --list
    python manage.py debug_generator_inputs --task <task_id>
    python manage.py debug_generator_inputs --json
    python manage.py debug_generator_inputs --replay
    python manage.py debug_generator_inputs --validate
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.scheduler.models import SchedulerInputLog, SchedulerTaskProgress
from apps.scheduler.debug_layer import analyze_generator_payload


class Command(BaseCommand):
    help = "Inspect, audit, validate, or replay timetable generator inputs from the frontend middle layer."

    def add_arguments(self, parser):
        parser.add_argument(
            "--last",
            action="store_true",
            help="Show the most recently captured generator input payload.",
        )
        parser.add_argument(
            "--task",
            type=str,
            help="Show input payload for a specific task ID.",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List recent captured generator input payloads.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output the raw input payload as JSON to stdout.",
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            help="Run pre-flight validation checks on the captured payload.",
        )
        parser.add_argument(
            "--replay",
            action="store_true",
            help="Re-run the solver directly using the captured payload (no browser needed).",
        )
        parser.add_argument(
            "--async-mode",
            action="store_true",
            help="When replaying, dispatch to background queue instead of running synchronously.",
        )
        parser.add_argument(
            "--rename-version",
            type=int,
            help="Rename a timetable version by its ID (pair with --new-name).",
        )
        parser.add_argument(
            "--new-name",
            type=str,
            help="New name for the timetable version.",
        )

    def handle(self, *args, **options):
        # 0. Rename Timetable Version if requested
        if options.get("rename_version"):
            vid = options["rename_version"]
            new_name = options.get("new_name")
            if not new_name:
                self.stderr.write(self.style.ERROR("Error: --new-name is required when renaming a version."))
                return
            from apps.scheduler.models import TimetableVersion
            ver = TimetableVersion.objects.filter(id=vid).first()
            if not ver:
                self.stderr.write(self.style.ERROR(f"Error: Timetable version #{vid} not found."))
                return
            old_name = ver.name
            ver.name = new_name.strip()
            ver.save(update_fields=["name"])
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Renamed Timetable #{vid} from '{old_name}' to '{ver.name}'!"))
            return

        # 1. List Recent Payloads
        if options["list"]:
            self._list_recent()
            return

        # 2. Retrieve target log entry
        task_id = options.get("task")
        log_entry = None

        if task_id:
            log_entry = SchedulerInputLog.objects.filter(task_id=task_id).first()
            if not log_entry:
                # Also check SchedulerTaskProgress
                prog = SchedulerTaskProgress.objects.filter(task_id=task_id).first()
                if prog and prog.input_payload:
                    summary = analyze_generator_payload(prog.input_payload)
                    log_entry = SchedulerInputLog(
                        task_id=task_id,
                        endpoint="generate",
                        draft_name=summary.get("draft_name", ""),
                        scope_type=summary.get("scope_type", "department"),
                        scope_label=summary.get("scope_label", ""),
                        raw_payload=prog.input_payload,
                        summary=summary,
                    )
            if not log_entry:
                self.stderr.write(self.style.ERROR(f"No captured inputs found for task ID: {task_id}"))
                return
        else:
            log_entry = SchedulerInputLog.objects.first()

        # Fallback to file dump if DB table has no records yet
        raw_payload = {}
        summary = {}
        if log_entry:
            raw_payload = log_entry.raw_payload
            summary = log_entry.summary
            task_id = log_entry.task_id
        else:
            dump_path = Path(settings.BASE_DIR) / "latest_generator_input.json"
            if dump_path.exists():
                try:
                    with open(dump_path, "r", encoding="utf-8") as f:
                        file_dump = json.load(f)
                        raw_payload = file_dump.get("raw_payload", {})
                        summary = file_dump.get("summary", {})
                        task_id = file_dump.get("task_id", "")
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Could not read latest_generator_input.json: {e}"))

        if not raw_payload:
            self.stderr.write(self.style.WARNING("No generator input payloads have been captured yet."))
            self.stdout.write("Submit a timetable generation from the frontend to populate the middle layer,")
            self.stdout.write("or pass an existing payload with --replay.")
            return

        # 3. Output as JSON if requested
        if options["json"]:
            self.stdout.write(json.dumps(raw_payload, indent=2, ensure_ascii=False))
            return

        # 4. Replay Solver
        if options["replay"]:
            self._replay_payload(raw_payload, is_async=options.get("async_mode", False))
            return

        # 5. Display Formatted Summary & Pre-flight Diagnostics
        self._display_summary(log_entry, summary, raw_payload, validate_only=options.get("validate", False))

    def _display_summary(self, log_entry, summary, raw_payload, validate_only=False):
        c = summary.get("counts", {})
        ct = summary.get("constraints", {})
        created_at_str = log_entry.created_at.strftime("%Y-%m-%d %H:%M:%S") if (log_entry and log_entry.created_at) else "Recent dump"
        user_str = log_entry.user_username if log_entry else "anonymous"

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(self.style.SUCCESS("[DEBUG-LAYER] FRONTEND GENERATOR INPUT PAYLOAD INSPECTION"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))

        self.stdout.write(f"  * Captured At:       {created_at_str}")
        self.stdout.write(f"  * User / Client:     {user_str} ({getattr(log_entry, 'ip_address', None) or '127.0.0.1'})")
        self.stdout.write(f"  * Task Tracking ID:  {summary.get('draft_name') or 'N/A'}")
        self.stdout.write(f"  * Scope:             {summary.get('scope_label')} (type: {summary.get('scope_type')})")
        if summary.get("department_name"):
            self.stdout.write(f"  * Department:        {summary.get('department_name')} [ID: {summary.get('department_id')}]")
        if summary.get("block_name"):
            self.stdout.write(f"  * Academic Block:    {summary.get('block_name')}")
        if summary.get("semester"):
            self.stdout.write(f"  * Semester / Term:   Sem {summary.get('semester')} ({summary.get('term') or 'all'})")

        self.stdout.write(self.style.MIGRATE_HEADING("-" * 72))
        self.stdout.write(self.style.MIGRATE_LABEL("RESOURCE COUNTS:"))
        self.stdout.write(
            f"    Subjects: {c.get('subjects', 0):<5} | Rooms: {c.get('rooms', 0):<5} | "
            f"Timeslots: {c.get('timeslots', 0):<5} | Breaks: {c.get('breaks', 0)}"
        )
        self.stdout.write(
            f"    Excluded Slots: {c.get('excluded_slots', 0):<3} | "
            f"Preferred Rooms: {c.get('preferred_room_types', 0):<3} | "
            f"Locked Entries: {c.get('locked_entries', 0)}"
        )

        self.stdout.write(self.style.MIGRATE_HEADING("-" * 72))
        self.stdout.write(self.style.MIGRATE_LABEL("SOLVER CONSTRAINTS & FLAGS:"))
        for key, val in ct.items():
            color = self.style.SUCCESS if val else self.style.NOTICE
            self.stdout.write(f"    {key:<28} : {color(str(val))}")

        warnings = summary.get("warnings", [])
        self.stdout.write(self.style.MIGRATE_HEADING("-" * 72))
        if warnings:
            self.stdout.write(self.style.WARNING(f"PRE-FLIGHT DIAGNOSTICS ({len(warnings)} found):"))
            for w in warnings:
                clean_w = (
                    str(w)
                    .replace("⚠️", "[WARN]")
                    .replace("❌", "[ERROR]")
                    .replace("ℹ️", "[INFO]")
                    .encode("ascii", "replace")
                    .decode("ascii")
                )
                self.stdout.write(f"    {clean_w}")
        else:
            self.stdout.write(self.style.SUCCESS("PRE-FLIGHT DIAGNOSTICS: All checks passed! No constraint issues detected."))

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(
            "Tip: Replay this payload directly in the terminal with:\n"
            "   python manage.py debug_generator_inputs --replay\n"
            "   Or pipe raw JSON with: python manage.py debug_generator_inputs --json\n"
        )

    def _list_recent(self):
        logs = SchedulerInputLog.objects.all()[:15]
        if not logs:
            self.stdout.write(self.style.WARNING("No generator input logs recorded yet."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 82))
        self.stdout.write(self.style.SUCCESS(f"RECENT CAPTURED GENERATOR INPUTS ({SchedulerInputLog.objects.count()} total)"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 82))
        self.stdout.write(f"{'TIMESTAMP':<20} | {'SCOPE':<24} | {'DRAFT NAME':<20} | {'SUBJ':<4} | {'ROOM':<4} | {'SLOTS'}")
        self.stdout.write("-" * 82)

        for l in logs:
            counts = l.summary.get("counts", {})
            ts_str = l.created_at.strftime("%Y-%m-%d %H:%M:%S")
            scope_str = l.scope_label[:23]
            draft_str = (l.draft_name or "Untitled")[:19]
            sub_count = counts.get("subjects", 0)
            rm_count = counts.get("rooms", 0)
            slot_count = counts.get("timeslots", 0)
            self.stdout.write(
                f"{ts_str:<20} | {scope_str:<24} | {draft_str:<20} | {sub_count:<4} | {rm_count:<4} | {slot_count}"
            )
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 82))

    def _replay_payload(self, payload, is_async=False):
        import uuid
        import time
        from apps.scheduler.tasks import generate_timetable_task
        from apps.scheduler.models import SchedulerTaskProgress

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(self.style.SUCCESS(">>> REPLAYING TIMETABLE GENERATION FROM CAPTURED INPUTS"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))

        # Clone payload with fresh tracking ID
        config = dict(payload)
        tracking_id = uuid.uuid4().hex
        config["tracking_id"] = tracking_id
        config["draft_name"] = f"[REPLAY] {config.get('draft_name', 'Test Run')}"

        self.stdout.write(f"Draft:    {config['draft_name']}")
        self.stdout.write(f"Scope:    {config.get('scope_type')} (Dept: {config.get('department_id')}, Block: {config.get('block_name')})")
        self.stdout.write(f"Task ID:  {tracking_id}")

        if is_async:
            from django_q.tasks import async_task
            SchedulerTaskProgress.objects.create(
                task_id=tracking_id,
                status="queued",
                scope_type=config.get("scope_type", "department"),
                scope_label="[REPLAY] Direct Terminal Run",
                input_payload=config,
            )
            q_id = async_task("apps.scheduler.tasks.generate_timetable_task", config, timeout=-1)
            self.stdout.write(self.style.SUCCESS(f"Task dispatched to background worker! Q Task ID: {q_id}"))
            self.stdout.write(f"Track with: python manage.py debug_generator_inputs --task {tracking_id}")
            return

        self.stdout.write("Executing solver synchronously in terminal...")
        t0 = time.time()
        try:
            result = generate_timetable_task(config)
            elapsed = round(time.time() - t0, 2)
            if result.get("success"):
                count = result.get("count", 0)
                version_id = result.get("version_id")
                self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Replay Succeeded in {elapsed}s! Generated {count} sessions."))
                if version_id:
                    self.stdout.write(f"Saved Timetable Version ID: {version_id}")
            else:
                err = result.get("error", "Unknown solver failure")
                self.stdout.write(self.style.ERROR(f"[FAIL] Replay Failed in {elapsed}s: {err}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"[ERROR] Exception during solver replay: {e}"))

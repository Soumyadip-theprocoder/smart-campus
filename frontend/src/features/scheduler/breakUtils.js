/**
 * Break helpers for the timetable.
 *
 * A break is a time range `{ start: 'HH:MM', end: 'HH:MM', label?: string }`.
 *  - Continuous break: one range covering several hours (e.g. 12:00-15:00).
 *  - Discrete breaks: several independent ranges (e.g. 10:00-11:00 and 15:00-16:00).
 *
 * Legacy values (plain 'HH:MM' strings meaning a one-hour break) are accepted everywhere.
 */

export const toMinutes = (time) => {
  if (typeof time !== 'string') return NaN;
  const [h, m] = time.split(':');
  const hours = parseInt(h, 10);
  const mins = parseInt(m ?? '0', 10);
  if (Number.isNaN(hours) || Number.isNaN(mins)) return NaN;
  return hours * 60 + mins;
};

export const fromMinutes = (total) => {
  const clamped = Math.max(0, Math.min(24 * 60, total));
  const h = Math.floor(clamped / 60);
  const m = clamped % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
};

/** Convert one raw entry (string or object) to `{ start, end, label }` or null if invalid. */
const toRange = (entry) => {
  if (typeof entry === 'string') {
    const start = toMinutes(entry);
    if (Number.isNaN(start)) return null;
    return { start, end: Math.min(start + 60, 24 * 60), label: '' };
  }
  if (entry && typeof entry === 'object') {
    const start = toMinutes(entry.start);
    const end = toMinutes(entry.end);
    if (Number.isNaN(start) || Number.isNaN(end) || end <= start) return null;
    return { start, end, label: entry.label || '' };
  }
  return null;
};

/**
 * Normalize raw breaks into a sorted list of non-overlapping ranges.
 * Overlapping or touching ranges are merged (first label wins).
 */
export const normalizeBreaks = (raw) => {
  const ranges = (Array.isArray(raw) ? raw : [])
    .map(toRange)
    .filter(Boolean)
    .sort((a, b) => a.start - b.start || a.end - b.end);

  const merged = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (last && r.start <= last.end) {
      last.end = Math.max(last.end, r.end);
      if (!last.label && r.label) last.label = r.label;
    } else {
      merged.push({ ...r });
    }
  }
  return merged.map((r) => ({ start: fromMinutes(r.start), end: fromMinutes(r.end), label: r.label }));
};

/** The break range containing `time` (start <= time < end), or null. */
export const findBreakAt = (time, breaks) => {
  const t = toMinutes(time);
  if (Number.isNaN(t)) return null;
  return normalizeBreaks(breaks).find((b) => t >= toMinutes(b.start) && t < toMinutes(b.end)) || null;
};

export const isTimeInBreak = (time, breaks) => findBreakAt(time, breaks) !== null;

/** True when [slotStart, slotEnd) overlaps any break. */
export const slotOverlapsBreak = (slotStart, slotEnd, breaks) => {
  const s = toMinutes(slotStart?.substring(0, 5));
  const e = toMinutes(slotEnd?.substring(0, 5));
  if (Number.isNaN(s) || Number.isNaN(e)) return false;
  return normalizeBreaks(breaks).some((b) => s < toMinutes(b.end) && e > toMinutes(b.start));
};

/**
 * Describe how a row should render for the given ordered list of row start times.
 * Returns `{ isBreak, isFirstRow, span, label, range }`. For a continuous break only the
 * first covered row has `isFirstRow = true` and `span` = number of rows it covers; the
 * remaining covered rows have `isFirstRow = false` and should be skipped by the renderer.
 */
export const describeRow = (time, rowTimes, breaks) => {
  const range = findBreakAt(time, breaks);
  if (!range) return { isBreak: false, isFirstRow: false, span: 1, label: '', range: null };
  const covered = rowTimes.filter((t) => isTimeInBreak(t, [range]));
  return {
    isBreak: true,
    isFirstRow: covered[0] === time,
    span: Math.max(1, covered.length),
    label: range.label || '',
    range,
  };
};

/** Hourly start times (HH:MM) covered by a range. */
export const expandBreakToHours = (range) => {
  const out = [];
  for (let m = toMinutes(range.start); m < toMinutes(range.end); m += 60) out.push(fromMinutes(m));
  return out;
};

/** Add `[start, end)` to the breaks, merging with neighbours. */
export const addBreak = (breaks, start, end, label = '') =>
  normalizeBreaks([...normalizeBreaks(breaks), { start, end, label }]);

/** Remove the hour starting at `time` from whichever break covers it (splitting if needed). */
export const removeHourFromBreaks = (breaks, time) => {
  const t = toMinutes(time);
  const out = [];
  for (const b of normalizeBreaks(breaks)) {
    const s = toMinutes(b.start);
    const e = toMinutes(b.end);
    if (t >= e || t + 60 <= s) {
      out.push(b);
      continue;
    }
    if (s < t) out.push({ start: b.start, end: fromMinutes(t), label: b.label });
    if (e > t + 60) out.push({ start: fromMinutes(t + 60), end: b.end, label: b.label });
  }
  return out;
};

/** Format 'HH:MM' as e.g. '1:00 PM'. */
export const formatClock = (time) => {
  if (!time) return '';
  const [h, m] = time.split(':');
  const hour = parseInt(h, 10);
  return `${hour % 12 || 12}:${m} ${hour >= 12 && hour < 24 ? 'PM' : 'AM'}`;
};

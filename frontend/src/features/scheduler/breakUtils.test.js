// Run with: node --test src/features/scheduler/breakUtils.test.js
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  normalizeBreaks, isTimeInBreak, describeRow, slotOverlapsBreak,
  addBreak, removeHourFromBreaks, expandBreakToHours,
} from './breakUtils.js';

const rows = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'];

test('legacy string becomes a one-hour range', () => {
  assert.deepEqual(normalizeBreaks(['13:00']), [{ start: '13:00', end: '14:00', label: '' }]);
});

test('overlapping and touching ranges merge; discrete ones stay separate', () => {
  const out = normalizeBreaks([
    { start: '12:00', end: '14:00' },
    { start: '13:00', end: '15:00', label: 'Lunch' },
    { start: '10:00', end: '11:00' },
    { start: '16:00', end: '17:00' },
  ]);
  assert.equal(out.length, 3);
  assert.deepEqual(out.map((b) => [b.start, b.end]), [['10:00', '11:00'], ['12:00', '15:00'], ['16:00', '17:00']]);
  assert.equal(out[1].label, 'Lunch');
});

test('invalid entries are ignored', () => {
  assert.deepEqual(normalizeBreaks(['abc', { start: '15:00', end: '14:00' }, null, undefined]), []);
  assert.deepEqual(normalizeBreaks(undefined), []);
});

test('13:00 can be unselected (no gap heuristic)', () => {
  const withBreak = normalizeBreaks(['13:00']);
  assert.equal(isTimeInBreak('13:00', withBreak), true);
  const after = removeHourFromBreaks(withBreak, '13:00');
  assert.equal(isTimeInBreak('13:00', after), false);
  assert.deepEqual(after, []);
});

test('break end is exclusive', () => {
  const b = [{ start: '12:00', end: '15:00' }];
  assert.equal(isTimeInBreak('12:00', b), true);
  assert.equal(isTimeInBreak('14:00', b), true);
  assert.equal(isTimeInBreak('15:00', b), false);
});

test('continuous 12-15 break renders once with span 3', () => {
  const b = [{ start: '12:00', end: '15:00' }];
  const first = describeRow('12:00', rows, b);
  const mid = describeRow('13:00', rows, b);
  assert.deepEqual([first.isBreak, first.isFirstRow, first.span], [true, true, 3]);
  assert.deepEqual([mid.isBreak, mid.isFirstRow], [true, false]);
  assert.equal(describeRow('15:00', rows, b).isBreak, false);
});

test('discrete breaks (10am and 3pm) give two banners with classes between', () => {
  const b = normalizeBreaks(['10:00', '15:00']);
  assert.equal(describeRow('10:00', rows, b).isFirstRow, true);
  assert.equal(describeRow('15:00', rows, b).isFirstRow, true);
  assert.equal(describeRow('12:00', rows, b).isBreak, false);
});

test('removing the middle hour splits a continuous break', () => {
  const out = removeHourFromBreaks([{ start: '12:00', end: '15:00' }], '13:00');
  assert.deepEqual(out.map((x) => [x.start, x.end]), [['12:00', '13:00'], ['14:00', '15:00']]);
});

test('slotOverlapsBreak filters timeslots inside breaks', () => {
  const b = [{ start: '12:00', end: '15:00' }];
  assert.equal(slotOverlapsBreak('14:00:00', '15:00:00', b), true);
  assert.equal(slotOverlapsBreak('15:00:00', '16:00:00', b), false);
  assert.equal(slotOverlapsBreak('11:00:00', '12:00:00', b), false);
});

test('addBreak merges and expandBreakToHours lists hours', () => {
  const out = addBreak([{ start: '10:00', end: '11:00' }], '11:00', '13:00');
  assert.deepEqual(out.map((x) => [x.start, x.end]), [['10:00', '13:00']]);
  assert.deepEqual(expandBreakToHours(out[0]), ['10:00', '11:00', '12:00']);
});

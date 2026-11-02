#!/usr/bin/env node
// Regression cases for the inline STONK hourly model; no DOM or network required.
// Run: node work/test_stonk_hourly.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const template = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
const start = template.indexOf('function stkHourModel(');
assert.notEqual(start, -1, 'template must define the pure stkHourModel function');
const end = template.indexOf('\nfunction ', start + 1);
assert.notEqual(end, -1, 'stkHourModel must be followed by another function marker');
const context = vm.createContext({});
vm.runInContext(template.slice(start, end), context);
const model = context.stkHourModel;
for (const name of ['stkHourSeries', 'stkHourMoney']) {
  const functionStart = template.indexOf(`function ${name}(`);
  assert.notEqual(functionStart, -1, `template must define ${name}`);
  const functionEnd = template.indexOf('\nfunction ', functionStart + 1);
  assert.notEqual(functionEnd, -1, `${name} must be followed by another function marker`);
  vm.runInContext(template.slice(functionStart, functionEnd), context);
}
const hour = 3600;
const now = Date.parse('2026-11-01T09:30:23Z') / 1000;
const current = Math.floor(now / hour) * hour;
const latest = current - hour;
const json = value => JSON.parse(JSON.stringify(value));
let passed = 0;
function test(name, check) {
  check();
  passed += 1;
  console.log('PASS', name);
}
function close(actual, expected, message) {
  assert.equal(typeof actual, 'number', message);
  assert(Math.abs(actual - expected) < 1e-9, message || `${actual} should equal ${expected}`);
}
function window12(values) {
  return [values.map((_, i) => current - (12 - i) * hour), values];
}

test('UTC slots exclude the current unfinished hour and all future values', () => {
  const actual = model([latest, current, current + hour], [100, 900000, 900000], 72, now);
  assert.equal(actual.hours.length, 72);
  assert.equal(actual.hours[0], current - 72 * hour);
  assert.equal(actual.hours.at(-1), latest);
  assert.equal(actual.vals.at(-1), 100);
  assert.equal(actual.sum, 100);
  assert.equal(actual.count, 1);
  assert.equal(actual.latest.ts, latest);
});

test('6h, 24h and 72h spans retain the same UTC ending slot', () => {
  for (const span of [6, 24, 72]) {
    const actual = model([latest], [10], span, now);
    assert.equal(actual.hours.length, span);
    assert.equal(actual.vals.length, span);
    assert.equal(actual.hours[0], current - span * hour);
    assert.equal(actual.hours.at(-1), latest);
  }
});

test('selected 6h, 24h and 72h totals each include only their own complete hours', () => {
  const times = Array.from({length: 72}, (_, i) => current - (72 - i) * hour);
  const amounts = Array(48).fill(1).concat(Array(18).fill(10), Array(6).fill(100));
  times.push(current - 73 * hour, current);
  amounts.push(1000000, 1000000);
  for (const [span, sum] of [[6, 600], [24, 780], [72, 828]]) {
    const actual = model(times, amounts, span, now);
    assert.equal(actual.sum, sum, `${span}h total must follow the selected range`);
    assert.equal(actual.count, span, `${span}h count must follow the selected range`);
  }
});

test('selected-range boundaries preserve missing hours and count real zero samples', () => {
  const offsets = [73, 72, 25, 24, 7, 6, 3, 2, 1, 0];
  const times = offsets.map(offset => current - offset * hour);
  const amounts = [999999, 1000, 100, 10, 20, 30, null, 0, 40, 999999];
  for (const [span, sum, count] of [[6, 70, 3], [24, 100, 5], [72, 1200, 7]]) {
    const actual = model(times, amounts, span, now);
    assert.equal(actual.sum, sum, `${span}h sum excludes unsampled and out-of-range hours`);
    assert.equal(actual.count, count, `${span}h count includes the genuine zero only`);
    assert.equal(actual.vals.filter(value => value === null).length, span - count);
    assert.deepEqual(json(actual.vals.slice(-3)), [null, 0, 40]);
  }
  for (const span of [6, 24]) {
    const empty = model([current - 25 * hour], [100], span, now);
    assert.equal(empty.sum, null, `${span}h without observations has no total`);
    assert.equal(empty.count, 0);
  }
});

test('missing, nonnumeric, nonfinite and negative amounts are gaps; zero is valid', () => {
  const input = [undefined, null, NaN, Infinity, -Infinity, -1, '12', false, 0, 12];
  const times = input.map((_, i) => current - (input.length - i) * hour);
  const actual = model(times, input, 24, now);
  assert.deepEqual(json(actual.vals.slice(-10)), [null, null, null, null, null, null, null, null, 0, 12]);
  assert.equal(actual.count, 2);
  assert.equal(actual.sum, 12);
});

test('unordered samples map to exact hourly timestamps without filling a gap', () => {
  const actual = model([latest, latest - 2 * hour, latest - hour + 60], [100, 80, 90], 6, now);
  assert.deepEqual(json(actual.vals.slice(-3)), [80, null, 100]);
  assert.equal(actual.latest.value, 100);
  assert.equal(actual.latest.change, null);
});

test('latest hourly change uses the adjacent hour, never an older valid sample', () => {
  const actual = model([latest - 2 * hour, latest - hour, latest], [50, 100, 125], 6, now);
  assert.equal(actual.latest.ts, latest);
  assert.equal(actual.latest.value, 125);
  assert.equal(actual.latest.previous, 100);
  close(actual.latest.change, 0.25);
  const gap = model([latest - 2 * hour, latest], [50, 125], 6, now);
  assert.equal(gap.latest.change, null);
});

test('latest values are found across 72h even when the selected span has no samples', () => {
  const actual = model([current - 10 * hour, current - 11 * hour], [120, 100], 6, now);
  assert.equal(actual.count, 0);
  assert.equal(actual.sum, null);
  assert.equal(actual.latest.ts, current - 10 * hour);
  assert.equal(actual.latest.value, 120);
  close(actual.latest.change, 0.2);
});

test('zero income remains visible and a zero prior hour does not yield infinity', () => {
  const zero = model([latest - hour, latest], [100, 0], 6, now);
  assert.equal(zero.latest.value, 0);
  assert.equal(zero.latest.change, -1);
  const priorZero = model([latest - hour, latest], [0, 100], 6, now);
  assert.equal(priorZero.latest.previous, 0);
  assert.equal(priorZero.latest.change, null);
  const allZero = model([latest], [0], 6, now);
  assert.equal(allZero.count, 1);
  assert.equal(allZero.sum, 0);
});

test('six-hour change requires two complete windows and a positive prior sum', () => {
  const values = Array(6).fill(100).concat(Array(6).fill(200));
  const [times] = window12(values);
  const complete = model(times, values, 24, now);
  assert.deepEqual(json(complete.recent), {sum: 1200, count: 6});
  assert.deepEqual(json(complete.prior), {sum: 600, count: 6});
  close(complete.change6, 1);
  for (const index of [1, 10]) {
    const missing = values.slice(); missing[index] = null;
    assert.equal(model(times, missing, 24, now).change6, null);
  }
  const noPriorIncome = Array(6).fill(0).concat(Array(6).fill(200));
  assert.equal(model(times, noPriorIncome, 24, now).change6, null);
  const none = model([], [], 24, now);
  assert.equal(none.sum, null);
  assert.equal(none.recent.sum, null);
  assert.equal(none.prior.sum, null);
  assert.equal(none.change6, null);
});

test('UTC midnight ends at the preceding day, with no stale or future-day leakage', () => {
  const midnight = Date.parse('2026-11-02T00:00:00Z') / 1000;
  const actual = model([midnight - hour, midnight, midnight - 73 * hour], [25, 1000, 1000], 24, midnight);
  assert.equal(actual.hours.at(-1), midnight - hour);
  assert.equal(actual.latest.ts, midnight - hour);
  assert.equal(actual.sum, 25);
});

test('2026-11-01 observed snapshot: hourly rebound +127.5%, six-hour trend -67.0%', () => {
  // Captured from hourly.stonk.rev in the 2026-11-01 09:30:23 UTC snapshot.
  // The final 09:00 slot is unfinished and must not displace a completed hour.
  const values = [1368.13, 1284.05, 1540.65, 838.94, 6949.92, 2143.62,
    1024.28, 723.75, 664.6, 794.17, 443.74, 1009.71, null];
  const times = values.map((_, i) => current - (12 - i) * hour);
  const actual = model(times, values, 24, now);
  assert.equal(actual.latest.ts, Date.parse('2026-11-01T08:00:00Z') / 1000);
  close(actual.latest.value, 1009.71);
  close(actual.latest.previous, 443.74);
  assert.equal((actual.latest.change * 100).toFixed(1), '127.5');
  close(actual.recent.sum, 4660.25);
  close(actual.prior.sum, 14125.31);
  assert.equal(actual.recent.count, 6);
  assert.equal(actual.prior.count, 6);
  assert.equal((actual.change6 * 100).toFixed(1), '-67.0');
});

test('original series and formatter use selected totals and correct units for all three metrics', () => {
  const times = Array.from({length: 72}, (_, i) => current - (72 - i) * hour);
  const base = Array(48).fill(1).concat(Array(18).fill(10), Array(6).fill(100));
  context.stkBundle = () => ({});
  context.hourlyBundle = () => ({hours: times, generated: now, stonk: {
    rev: base, burn: base.map(value => value * 100), vol: base.map(value => value * 10),
  }});
  context.Date = {now: () => now * 1000};
  for (const [tab, multiplier, formatted, zero] of [
    ['rev', 1, '$1,200', '$0'],
    ['burn', 100, '1,200 STONK', '0 STONK'],
    ['vol', 10, '$1,200', '$0'],
  ]) {
    context.STK_HTAB = tab;
    for (const [span, total] of [[6, 600], [24, 780], [72, 828]]) {
      context.STK_HRANGE = span;
      const actual = context.stkHourSeries();
      assert.equal(actual.sum, total * multiplier, `${tab} ${span}h must use selected samples`);
      assert.equal(actual.count, span);
      assert.equal(actual.generated, now);
    }
    assert.equal(context.stkHourMoney(1200), formatted);
    assert.equal(context.stkHourMoney(0), zero);
    assert.equal(context.stkHourMoney(null), '—');
  }
});

console.log(`STONK hourly model: ${passed} regression groups passed.`);

#!/usr/bin/env node
// Exercise the real inline display helpers in several non-Beijing host zones.
// Run: node work/test_beijing_time.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {spawnSync} = require('node:child_process');

if (!process.argv.includes('--tz-worker')) {
  for (const TZ of ['UTC', 'America/Los_Angeles', 'Asia/Tokyo']) {
    const result = spawnSync(process.execPath, [__filename, '--tz-worker'], {
      env: {...process.env, TZ}, encoding: 'utf8', timeout: 10000,
    });
    assert.equal(result.status, 0, `${TZ}: ${result.error || ''}\n${result.stdout}\n${result.stderr}`);
    console.log(`PASS Beijing display helpers with host TZ=${TZ}`);
  }
  console.log('Beijing time: 3 host-timezone suites passed.');
  process.exit(0);
}

const template = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
const context = vm.createContext({LANG: 'zh'});
for (const name of ['bjISO', 'bjZone', 'bjStamp', 'bjHour', 'bjDay', 'bjDayEnd', 'bjClock', 'stkDailyDates']) {
  const start = template.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `template must define the real ${name} display helper`);
  const end = template.indexOf('\nfunction ', start + 1);
  assert.notEqual(end, -1, `${name} must be followed by another function marker`);
  vm.runInContext(template.slice(start, end), context);
}
let passed = 0;
function test(name, check) {
  check();
  passed += 1;
  console.log('PASS', name);
}
function parts(value) {
  return context.bjISO(value).split(/[- :]/).map(Number);
}

test('Date, milliseconds and offset-qualified ISO inputs describe the same instant', () => {
  const iso = '2026-12-31T16:05:06Z';
  const inRealmDate = vm.runInContext(`new Date('${iso}')`, context);
  const expected = [2027, 1, 1, 0, 5, 6];
  for (const value of [iso, Date.parse(iso), inRealmDate, '2027-01-01T00:05:06+08:00']) {
    assert.deepEqual(parts(value), expected);
  }
  assert.equal(context.bjISO(0), '1970-01-01 08:00:00');
});

test('Beijing midnight and New Year occur eight hours before UTC midnight', () => {
  assert.deepEqual(parts('2026-12-31T15:59:59Z'), [2026, 12, 31, 23, 59, 59]);
  assert.deepEqual(parts('2026-12-31T16:00:00Z'), [2027, 1, 1, 0, 0, 0]);
  assert.deepEqual(parts('2026-11-01T16:00:00Z'), [2026, 11, 2, 0, 0, 0]);
});

test('display stamps keep year, optional seconds and an explicit Beijing label', () => {
  assert.equal(context.bjZone(), '北京时间');
  assert.equal(context.bjISO('2026-12-31T16:05:06Z'), '2027-01-01 00:05:06');
  const stamp = context.bjStamp('2026-12-31T16:05:06Z');
  assert.match(stamp, /^2027-01-01 00:05\s+北京时间$/);
  assert.match(context.bjStamp('2026-12-31T16:05:06Z', true), /^2027-01-01 00:05:06\s+北京时间$/);
  context.LANG = 'en';
  assert.equal(context.bjZone(), 'Beijing');
  assert.match(context.bjStamp('2026-12-31T16:05:06Z'), /^2027-01-01 00:05\s+Beijing$/);
  context.LANG = 'zh';
});

test('hour labels accept epoch seconds and preserve midnight without a 24:00 label', () => {
  const seconds = Date.parse('2026-12-31T16:05:00Z') / 1000;
  assert.match(context.bjHour(seconds), /^1\/1 00:05\s+北京时间$/);
  assert.equal(context.bjHour(seconds, false), '1/1 00:05');
});

test('clock-only labels use Beijing time with optional seconds and either language', () => {
  const instant = '2026-12-31T16:05:06Z';
  assert.equal(context.bjClock(instant), '00:05:06 北京时间');
  assert.equal(context.bjClock(instant, false), '00:05 北京时间');
  context.LANG = 'en';
  assert.equal(context.bjClock(instant), '00:05:06 Beijing');
  assert.equal(context.bjClock(instant, false), '00:05 Beijing');
  context.LANG = 'zh';
});

test('US and European daylight-saving transitions never change the Beijing UTC+8 offset', () => {
  for (const [iso, expected] of [
    ['2026-03-08T09:59:00Z', [2026, 3, 8, 17, 59, 0]],
    ['2026-03-08T10:00:00Z', [2026, 3, 8, 18, 0, 0]],
    ['2026-11-01T08:59:00Z', [2026, 11, 1, 16, 59, 0]],
    ['2026-11-01T09:00:00Z', [2026, 11, 1, 17, 0, 0]],
    ['2026-03-29T00:59:00Z', [2026, 3, 29, 8, 59, 0]],
    ['2026-03-29T01:00:00Z', [2026, 3, 29, 9, 0, 0]],
  ]) {
    assert.deepEqual(parts(iso), expected, iso);
  }
});

test('official UTC daily buckets remain Beijing 08:00-to-08:00 windows', () => {
  for (const [date, next] of [
    ['2026-10-31', '2026-11-01'],
    ['2026-12-31', '2027-01-01'],
    ['2028-02-29', '2028-03-01'],
  ]) {
    assert.equal(context.bjDay(date), `${date.slice(5)} 08:00–${next.slice(5)} 08:00 北京时间`);
    assert.equal(context.bjDay(date, true), `${date} 08:00–${next} 08:00 北京时间`);
    assert.equal(context.bjDayEnd(date), `${next} 08:00 北京时间`);
  }
  context.LANG = 'en';
  assert.equal(context.bjDay('2026-12-31'), '12-31 08:00–01-01 08:00 Beijing');
  assert.equal(context.bjDayEnd('2026-12-31'), '2027-01-01 08:00 Beijing');
  context.LANG = 'zh';
});

test('invalid instants remain unavailable instead of fabricating a displayed time', () => {
  const invalidDate = vm.runInContext('new Date(NaN)', context);
  for (const value of ['not-a-date', '', NaN, undefined, null, invalidDate]) {
    assert.equal(context.bjISO(value), '');
    assert.equal(context.bjStamp(value), '—');
    assert.equal(context.bjStamp(value, true), '—');
    assert.equal(context.bjClock(value), '—');
    assert.equal(context.bjClock(value, false), '—');
  }
  for (const value of [null, undefined, '', NaN, Infinity, 'not-a-date']) {
    assert.equal(context.bjHour(value), '—');
  }
});

test('invalid daily buckets never roll over into another date or default to 1970', () => {
  for (const value of [null, undefined, '', 0, 'not-a-date', '2026-02-30',
    '2026-13-01', '2026-00-01', '2026-1-01', '2026-01-32', '2026-10-31T00:00:00Z']) {
    assert.equal(context.bjDay(value), '—', String(value));
    assert.equal(context.bjDay(value, true), '—', String(value));
    assert.equal(context.bjDayEnd(value), '—', String(value));
  }
});

test('legacy MM-DD flywheel snapshots recover exact years from the revenue history', () => {
  const result = context.stkDailyDates({dates: ['09-21', '09-22', '09-23'], rev90: {
    dates: ['2026-09-20', '2026-09-23', '2026-09-21', '2026-09-22'],
  }});
  assert.deepEqual(Array.from(result), ['2026-09-21', '2026-09-22', '2026-09-23']);
  assert.equal(context.bjDay(result[0]), '09-21 08:00–09-22 08:00 北京时间');
});

test('legacy flywheel dates retain their historical years across New Year', () => {
  const result = context.stkDailyDates({dates: ['12-31', '01-01', '01-02'], rev90: {
    dates: ['2024-12-31', '2025-01-01', '2025-01-02'],
  }});
  assert.deepEqual(Array.from(result), ['2024-12-31', '2025-01-01', '2025-01-02']);
  assert.equal(context.bjDay(result[0], true), '2024-12-31 08:00–2025-01-01 08:00 北京时间');
});

test('explicit ISO display dates take precedence over the legacy history lookup', () => {
  const result = context.stkDailyDates({dates: ['12-31', '01-01'],
    datesISO: ['2028-12-31', '2029-01-01'], rev90: {dates: ['2024-12-31', '2025-01-01']}});
  assert.deepEqual(Array.from(result), ['2028-12-31', '2029-01-01']);
  const complete = context.stkDailyDates({dates: ['2024-12-31', '2025-01-01']});
  assert.deepEqual(Array.from(complete), ['2024-12-31', '2025-01-01']);
});

test('missing or ambiguous legacy years stay empty instead of guessing the current year', () => {
  assert.deepEqual(Array.from(context.stkDailyDates({})), []);
  assert.deepEqual(Array.from(context.stkDailyDates({dates: ['12-31', '01-01']})), ['', '']);
  const ambiguous = context.stkDailyDates({dates: ['10-31', '11-01', '11-02'], rev90: {
    dates: ['2025-10-31', '2026-10-31', '2026-11-01'],
  }});
  assert.deepEqual(Array.from(ambiguous), ['', '2026-11-01', '']);
  const mismatched = context.stkDailyDates({dates: ['12-31', '01-01'],
    datesISO: ['2030-01-01', '2029-12-31'], rev90: {dates: ['2024-12-31']}});
  assert.deepEqual(Array.from(mismatched), ['2024-12-31', '']);
  assert.equal(context.bjDay(ambiguous[0]), '—');
});

console.log(`Beijing time: ${passed} groups passed with host TZ=${process.env.TZ}.`);

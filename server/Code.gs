/**
 * 재난소통 영웅 랭킹 서버 (Google Apps Script)
 * Copyright (c) 2026 KOREA CONTENTS LAB. All rights reserved.
 *
 * 설치: 랭킹 관리 구글 시트 → 확장 프로그램 → Apps Script → 이 코드를 붙여넣고 저장
 *       → 배포 → 새 배포 → 유형: 웹 앱 → 실행: 나 / 액세스: 모든 사용자 → 배포
 *       → 나온 웹 앱 URL(…/exec)을 게임 설정에 넣습니다.
 *
 * 게임이 보내는 요청 (모두 GET)
 *   ?action=verify&code=KCL-XXXX-XXXX&nick=이름
 *   ?action=submit&code=…&nick=…&costume=lime&stage=fire&power=9&goods=4&npc=…&run=고유ID
 *   ?action=rank&code=…            (code 없이도 상위 랭킹 조회 가능)
 * 응답에는 인증번호가 절대 포함되지 않습니다.
 */
const STAGES = ['flood', 'fire', 'quake', 'blast', 'heat', 'collapse', 'virus'];
const STAGE_KO = { flood: '침수', fire: '화재', quake: '지진', blast: '폭발', heat: '폭염', collapse: '건물붕괴', virus: '감염병확산' };
const COSTUME_KO = { lime: '민방위 대원', fire: '소방관', police: '경찰관', gov: '공무원', blue: '일반인' };
const PASS = 8;          // 관문 통과 기준 파워
const STAGE_MULT = 10;   // 관문 점수 = 관문별 최고 파워 합 × 10
const GOOD_PTS = 5;      // 적정 답변 1개당 참여 점수
const TOP = 50;          // 게임에 보여줄 상위 인원

const SHEETS = {
  codes: { name: '인증번호', head: ['인증번호', '발급 대상(메모)', '상태', '발급일', '최초 사용일', '닉네임'] },
  rank: { name: '랭킹', head: ['인증번호', '닉네임', '복장', '침수', '화재', '지진', '폭발', '폭염', '건물붕괴', '감염병확산', '통과 관문 수', '적정 답변 누적', '훈련 횟수', '관문 점수', '총점', '최근 훈련'] },
  log: { name: '훈련기록', head: ['시각', '인증번호', '닉네임', '재난', '대상', '최종 파워', '통과', '적정 답변', '훈련 ID'] }
};

/* ---------- 웹 앱 진입점 ---------- */
function doGet(e) {
  const p = (e && e.parameter) || {};
  let out;
  try {
    if (p.action === 'verify') out = verify_(p);
    else if (p.action === 'submit') out = submit_(p);
    else if (p.action === 'rank') out = rank_(p.code);
    else out = { ok: true, service: '재난소통 영웅 랭킹', holder: 'KOREA CONTENTS LAB' };
  } catch (err) {
    out = { ok: false, error: 'server', message: String((err && err.message) || err) };
  }
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(ContentService.MimeType.JSON);
}

/* ---------- 공통 ---------- */
function sheet_(key) {
  const def = SHEETS[key], ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(def.name);
  if (!sh) { sh = ss.insertSheet(def.name); sh.appendRow(def.head); sh.setFrozenRows(1); }
  return sh;
}
const norm_ = c => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const cleanNick_ = s => String(s || '').replace(/[<>&"'\u0000-\u001f]/g, '').trim().slice(0, 12) || '익명';
const today_ = () => Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');

function findCode_(code) {
  const n = norm_(code);
  if (n.length < 8) return null;
  const v = sheet_('codes').getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (norm_(v[i][0]) === n) return { row: i + 1, code: String(v[i][0]).trim(), status: String(v[i][2] || '').trim(), firstUse: v[i][4] };
  }
  return null;
}

/* ---------- 인증번호 확인 ---------- */
function verify_(p) {
  const c = findCode_(p.code);
  if (!c) return { ok: false, error: 'invalid' };
  if (c.status === '중지') return { ok: false, error: 'stopped' };
  const sh = sheet_('codes');
  if (!c.firstUse) sh.getRange(c.row, 5).setValue(new Date());
  if (p.nick) sh.getRange(c.row, 6).setValue(cleanNick_(p.nick));
  return Object.assign({ ok: true }, myInfo_(rankList_(), c.code));
}

/* ---------- 훈련 결과 제출 ---------- */
function submit_(p) {
  const c = findCode_(p.code);
  if (!c) return { ok: false, error: 'invalid' };
  if (c.status === '중지') return { ok: false, error: 'stopped' };
  const stage = String(p.stage || '');
  if (STAGES.indexOf(stage) < 0) return { ok: false, error: 'bad_stage' };
  const power = Math.max(0, Math.min(10, parseInt(p.power, 10) || 0));
  const goods = Math.max(0, Math.min(5, parseInt(p.goods, 10) || 0));
  const run = String(p.run || '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 40);
  const nick = cleanNick_(p.nick);
  const costume = COSTUME_KO[p.costume] || '';

  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const before = rankList_();
    const prev = myInfo_(before, c.code);
    const cache = CacheService.getScriptCache();
    if (run && cache.get('run_' + run)) return Object.assign({ ok: true, duplicate: true, prevRank: prev.rank, gained: 0 }, prev);

    const sh = sheet_('rank');
    const v = sh.getDataRange().getValues();
    let rowIdx = -1;
    for (let i = 1; i < v.length; i++) if (norm_(v[i][0]) === norm_(c.code)) { rowIdx = i; break; }
    const row = rowIdx > 0 ? v[rowIdx].slice(0, 16) : [c.code, '', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''];
    while (row.length < 16) row.push('');

    const col = 3 + STAGES.indexOf(stage);
    if (power >= PASS) row[col] = Math.max(Number(row[col]) || 0, power);
    let sum = 0, passed = 0;
    for (let k = 3; k <= 9; k++) { const s = Number(row[k]) || 0; row[k] = s; sum += s; if (s > 0) passed++; }
    row[1] = nick; row[2] = costume || row[2];
    row[10] = passed;
    row[11] = (Number(row[11]) || 0) + goods;
    row[12] = (Number(row[12]) || 0) + 1;
    row[13] = sum * STAGE_MULT;
    row[14] = row[13] + row[11] * GOOD_PTS;
    row[15] = new Date();

    if (rowIdx > 0) sh.getRange(rowIdx + 1, 1, 1, 16).setValues([row]);
    else sh.appendRow(row);

    sheet_('log').appendRow([new Date(), c.code, nick, STAGE_KO[stage], String(p.npc || '').slice(0, 20), power, power >= PASS ? '통과' : '재훈련', goods, run]);
    if (run) cache.put('run_' + run, '1', 21600);
    SpreadsheetApp.flush();

    const now = myInfo_(rankList_(), c.code);
    return Object.assign({ ok: true, prevRank: prev.rank, gained: now.total - (prev.total || 0) }, now);
  } finally {
    lock.releaseLock();
  }
}

/* ---------- 랭킹 조회 ---------- */
function rank_(code) {
  const list = rankList_();
  const out = { ok: true, count: list.length, updated: new Date().toISOString(), top: list.slice(0, TOP).map(r => ({ rank: r.rank, nick: r.nick, costume: r.costume, passed: r.passed, goods: r.goods, total: r.total, me: !!code && norm_(r.code) === norm_(code) })) };
  if (code) {
    const c = findCode_(code);
    if (!c) out.meError = 'invalid';
    else if (c.status === '중지') out.meError = 'stopped';
    else out.me = myInfo_(list, c.code);
  }
  return out;
}

function rankList_() {
  const v = sheet_('rank').getDataRange().getValues();
  const list = [];
  for (let i = 1; i < v.length; i++) {
    if (!v[i][0]) continue;
    list.push({ code: String(v[i][0]), nick: String(v[i][1] || '익명'), costume: String(v[i][2] || ''), passed: Number(v[i][10]) || 0, goods: Number(v[i][11]) || 0, stageScore: Number(v[i][13]) || 0, total: Number(v[i][14]) || 0, runs: Number(v[i][12]) || 0 });
  }
  list.sort((a, b) => b.total - a.total || b.stageScore - a.stageScore || a.runs - b.runs);
  list.forEach((r, i) => { r.rank = i > 0 && r.total === list[i - 1].total ? list[i - 1].rank : i + 1; });
  return list;
}

function myInfo_(list, code) {
  const n = norm_(code);
  const i = list.findIndex(r => norm_(r.code) === n);
  if (i < 0) return { rank: null, count: list.length, total: 0, passed: 0, goods: 0, gapUp: null };
  const me = list[i];
  let gapUp = null;
  for (let j = i - 1; j >= 0; j--) if (list[j].total > me.total) { gapUp = list[j].total - me.total; break; }
  return { rank: me.rank, count: list.length, total: me.total, passed: me.passed, goods: me.goods, gapUp: gapUp };
}

/* ---------- 시트 메뉴 (운영자용) ---------- */
function onOpen() {
  SpreadsheetApp.getUi().createMenu('랭킹 관리')
    .addItem('인증번호 10개 발급', 'issue10')
    .addItem('인증번호 50개 발급', 'issue50')
    .addSeparator()
    .addItem('랭킹 초기화(새 시즌)', 'resetRanking')
    .addToUi();
}
function issue10() { issue_(10); }
function issue50() { issue_(50); }
function issue_(n) {
  const A = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  const sh = sheet_('codes');
  const have = new Set(sh.getDataRange().getValues().map(r => norm_(r[0])));
  const part = () => Array.from({ length: 4 }, () => A[Math.floor(Math.random() * A.length)]).join('');
  const rows = [];
  while (rows.length < n) {
    const code = 'KCL-' + part() + '-' + part();
    if (have.has(norm_(code))) continue;
    have.add(norm_(code));
    rows.push([code, '', '사용가능', today_(), '', '']);
  }
  sh.getRange(sh.getLastRow() + 1, 1, rows.length, 6).setValues(rows);
  SpreadsheetApp.getActiveSpreadsheet().toast(n + '개의 인증번호를 아래에 추가했습니다.', '랭킹 관리');
}
function resetRanking() {
  const ui = SpreadsheetApp.getUi();
  const ok = ui.alert('랭킹 초기화', '랭킹 탭의 모든 점수를 지웁니다. 인증번호와 훈련기록은 남습니다. 계속할까요?', ui.ButtonSet.YES_NO);
  if (ok !== ui.Button.YES) return;
  const sh = sheet_('rank');
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, sh.getLastColumn()).clearContent();
  SpreadsheetApp.getActiveSpreadsheet().toast('랭킹을 초기화했습니다. 새 시즌을 시작합니다.', '랭킹 관리');
}

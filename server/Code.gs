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
 *   ?action=apply&name=…&org=…&email=…&agree=1   (인증번호 신청 → 자동 발급 또는 승인 대기)
 *   ?action=config                  (신청 받기 여부·발급 방식 조회)
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
  codes: { name: '인증번호', head: ['인증번호', '발급 대상(메모)', '상태', '발급일', '최초 사용일', '닉네임', '학교'] },
  schools: { name: '학교목록', head: ['학교명', '약칭(주소)', '담당 교사', '계약 기간', '상태', '발급 수', '드라이브 폴더', '학교 전용 주소', '등록일'] },
  rank: { name: '랭킹', head: ['인증번호', '닉네임', '복장', '침수', '화재', '지진', '폭발', '폭염', '건물붕괴', '감염병확산', '통과 관문 수', '적정 답변 누적', '훈련 횟수', '관문 점수', '총점', '최근 훈련', '성별'] },
  log: { name: '훈련기록', head: ['시각', '인증번호', '닉네임', '재난', '대상', '최종 파워', '통과', '적정 답변', '훈련 ID'] },
  req: { name: '인증신청', head: ['신청 시각', '이름', '소속', '이메일', '상태', '인증번호', '처리 시각', '메모'] },
  conf: { name: '설정', head: ['항목', '값', '설명'] }
};
const CONF_DEFAULT = [
  ['발급 방식', '자동', '자동: 신청 즉시 번호 발급 · 승인: 운영자가 [랭킹 관리] 메뉴로 승인해야 발급'],
  ['신청 받기', '켜기', '끄기로 바꾸면 게임에서 새 신청을 받지 않습니다'],
  ['하루 자동 발급 한도', 200, '하루 자동 발급 수가 이 값을 넘으면 그날 신청은 승인 대기로 넘어갑니다'],
  ['이메일 발송', '켜기', '발급된 번호를 신청자 이메일로 보냅니다'],
  ['보내는 사람 이름', 'KOREA CONTENTS LAB', '안내 메일의 보낸 사람 이름']
];
const GAME_URL = 'https://ktvwin-pixel.github.io/disaster-game/';

/* ---------- 웹 앱 진입점 ---------- */
function doGet(e) {
  const p = (e && e.parameter) || {};
  let out;
  try {
    if (p.action === 'verify') out = verify_(p);
    else if (p.action === 'submit') out = submit_(p);
    else if (p.action === 'rank') out = rank_(p.code, p.school);
    else if (p.action === 'apply') out = apply_(p);
    else if (p.action === 'school') { const sc = schoolByKey_(p.s); out = sc ? { ok: true, name: sc.name, key: sc.key } : { ok: false, error: 'no_school' }; }
    else if (p.action === 'config') out = { ok: true, open: conf_('신청 받기') !== '끄기', mode: conf_('발급 방식') === '승인' ? 'approve' : 'auto' };
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
  if (!sh) {
    sh = ss.insertSheet(def.name); sh.appendRow(def.head); sh.setFrozenRows(1);
    if (key === 'conf') sh.getRange(2, 1, CONF_DEFAULT.length, 3).setValues(CONF_DEFAULT);
  }
  return sh;
}
function conf_(name) {
  const v = sheet_('conf').getDataRange().getValues();
  for (let i = 1; i < v.length; i++) if (String(v[i][0]).trim() === name) return String(v[i][1]).trim();
  const d = CONF_DEFAULT.find(r => r[0] === name);
  return d ? String(d[1]) : '';
}
const norm_ = c => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const cleanNick_ = s => String(s || '').replace(/[<>&"'\u0000-\u001f]/g, '').trim().slice(0, 12) || '익명';
const today_ = () => Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');

function findCode_(code) {
  const n = norm_(code);
  if (n.length < 8) return null;
  const v = sheet_('codes').getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (norm_(v[i][0]) === n) return { row: i + 1, code: String(v[i][0]).trim(), status: String(v[i][2] || '').trim(), firstUse: v[i][4], school: String(v[i][6] || '').trim() };
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
  return Object.assign({ ok: true, profile: profile_(c.code), school: c.school || '' }, myInfo_(rankList_(), c.code));
}

/* 인증번호로 이어하기: 저장된 별칭·복장·성별·관문별 최고 점수를 돌려줍니다 (인증번호 자체는 돌려주지 않음) */
function profile_(code) {
  const v = sheet_('rank').getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (norm_(v[i][0]) !== norm_(code)) continue;
    const r = v[i], stages = {};
    STAGES.forEach((k, j) => { stages[k] = Number(r[3 + j]) || 0; });
    const ck = Object.keys(COSTUME_KO).find(k => COSTUME_KO[k] === r[2]) || ({ '소방대원': 'fire', '경찰공무원': 'police' })[r[2]] || '';
    return { nick: String(r[1] || ''), costume: ck, g: String(r[16] || ''), stages: stages, goods: Number(r[11]) || 0, runs: Number(r[12]) || 0 };
  }
  return null;
}

/* ---------- 훈련 결과 제출 ---------- */
function submit_(p) {
  const c = findCode_(p.code);
  if (!c) return { ok: false, error: 'invalid' };
  if (c.status === '중지') return { ok: false, error: 'stopped' };
  const stage = String(p.stage || '');
  if (STAGES.indexOf(stage) < 0) return { ok: false, error: 'bad_stage' };
  const power = Math.max(0, Math.min(10, parseInt(p.power, 10) || 0));
  const goods = Math.max(0, Math.min(8, parseInt(p.goods, 10) || 0));
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
    const row = rowIdx > 0 ? v[rowIdx].slice(0, 17) : [c.code, '', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', ''];
    while (row.length < 17) row.push('');

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
    if (p.g === 'm' || p.g === 'f') row[16] = p.g;

    if (rowIdx > 0) sh.getRange(rowIdx + 1, 1, 1, 17).setValues([row]);
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
const topOf_ = (list, code) => list.slice(0, TOP).map(r => ({ rank: r.rank, nick: r.nick, costume: r.costume, passed: r.passed, goods: r.goods, total: r.total, me: !!code && norm_(r.code) === norm_(code) }));
function rank_(code, schoolKey) {
  const list = rankList_();
  const out = { ok: true, count: list.length, updated: new Date().toISOString(), top: topOf_(list, code) };
  let schoolName = '';
  if (code) {
    const c = findCode_(code);
    if (!c) out.meError = 'invalid';
    else if (c.status === '중지') out.meError = 'stopped';
    else { out.me = myInfo_(list, c.code); schoolName = c.school; }
  }
  if (schoolKey) { const sc = schoolByKey_(schoolKey); if (sc) schoolName = sc.name; else out.schoolError = 'invalid'; }
  if (schoolName) { const sc2 = schoolByName_(schoolName); if (sc2) out.schoolKey = sc2.key; }
  if (schoolName) out.school = schoolRank_(schoolName, code);
  return out;
}
/* 학교별 랭킹: 그 학교 인증번호로 훈련한 사람만 모아 순위를 다시 매김 */
function schoolRank_(name, code) {
  const codes = sheet_('codes').getDataRange().getValues().slice(1).filter(r => String(r[6] || '').trim() === name);
  const set = new Set(codes.map(r => norm_(r[0])));
  const list = rankList_().filter(r => set.has(norm_(r.code)));
  list.forEach((r, i) => { r.rank = i > 0 && r.total === list[i - 1].total ? list[i - 1].rank : i + 1; });
  const sum = (k) => list.reduce((a, r) => a + r[k], 0);
  const out = { name: name, count: list.length, issued: codes.length, started: codes.filter(r => r[4]).length,
    avgPassed: list.length ? Math.round(sum('passed') / list.length * 10) / 10 : 0, goods: sum('goods'), top: topOf_(list, code) };
  if (code && set.has(norm_(code))) out.me = myInfo_(list, code);
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

/* ---------- 인증번호 신청 ---------- */
const EMAIL_RE = /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/;
const clean_ = (s, n) => String(s || '').replace(/[<>&"'\u0000-\u001f]/g, '').trim().slice(0, n);

function newCodes_(n) {
  const A = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  const have = new Set(sheet_('codes').getDataRange().getValues().map(r => norm_(r[0])));
  const part = () => Array.from({ length: 4 }, () => A[Math.floor(Math.random() * A.length)]).join('');
  const out = [];
  while (out.length < n) {
    const code = 'KCL-' + part() + '-' + part();
    if (have.has(norm_(code))) continue;
    have.add(norm_(code)); out.push(code);
  }
  return out;
}
function issueTo_(memo, school) {
  const code = newCodes_(1)[0];
  const sh = sheet_('codes');
  if (school) ensureHeads_();
  sh.getRange(sh.getLastRow() + 1, 1, 1, school ? 7 : 6).setValues([[code, memo, '사용가능', today_(), '', ''].concat(school ? [school] : [])]);
  return code;
}
function mail_(to, name, code) {
  if (conf_('이메일 발송') === '끄기') return '메일 발송 꺼짐';
  try {
    const sender = conf_('보내는 사람 이름') || 'KOREA CONTENTS LAB';
    MailApp.sendEmail({
      to: to, name: sender,
      subject: '[재난소통 영웅] 랭킹 인증번호 안내',
      htmlBody: '<div style="font-family:sans-serif;line-height:1.7">' + clean_(name, 20) + '님, 재난소통 영웅 랭킹 인증번호를 보내 드립니다.<br><br>' +
        '<div style="font-size:22px;font-weight:bold;letter-spacing:2px;padding:10px 14px;background:#fff4d6;display:inline-block">' + code + '</div><br><br>' +
        '게임 → <b>랭킹 보기</b> → 인증번호 입력란에 위 번호를 넣고 <b>등록</b>을 누르세요.<br>' +
        '게임 주소: <a href="' + GAME_URL + '">' + GAME_URL + '</a><br><br>' +
        '<span style="color:#888;font-size:12px">이 번호는 1인 1개입니다. 다른 사람과 함께 쓰지 마세요.<br>© 2026 ' + sender + '</span></div>'
    });
    return '메일 발송';
  } catch (e) {
    return '메일 발송 실패: ' + String(e && e.message || e).slice(0, 60);
  }
}
function apply_(p) {
  if (conf_('신청 받기') === '끄기') return { ok: false, error: 'closed' };
  const name = clean_(p.name, 20), org = clean_(p.org, 30), email = clean_(p.email, 80).toLowerCase();
  if (!name) return { ok: false, error: 'need_name' };
  if (!EMAIL_RE.test(email)) return { ok: false, error: 'bad_email' };
  if (String(p.agree) !== '1') return { ok: false, error: 'need_agree' };
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const sh = sheet_('req');
    const v = sh.getDataRange().getValues();
    for (let i = v.length - 1; i >= 1; i--) {
      if (String(v[i][3]).toLowerCase() !== email) continue;
      const st = String(v[i][4]);
      if (st === '발급' && v[i][5]) {
        const note = mail_(email, name, String(v[i][5]));
        sh.getRange(i + 1, 8).setValue('재발송 요청 ' + Utilities.formatDate(new Date(), 'Asia/Seoul', 'MM-dd HH:mm') + ' · ' + note);
        return { ok: true, status: 'already', mailed: note === '메일 발송' };
      }
      if (st === '대기') return { ok: true, status: 'pending', again: true };
      if (st === '거절') return { ok: false, error: 'rejected' };
    }
    const now = new Date();
    let auto = conf_('발급 방식') !== '승인';
    if (auto) {
      const cap = parseInt(conf_('하루 자동 발급 한도'), 10) || 200;
      const t = today_();
      const issuedToday = v.slice(1).filter(r => r[4] === '발급' && r[6] && Utilities.formatDate(new Date(r[6]), 'Asia/Seoul', 'yyyy-MM-dd') === t).length;
      if (issuedToday >= cap) auto = false;
    }
    if (!auto) {
      sh.appendRow([now, name, org, email, '대기', '', '', '']);
      return { ok: true, status: 'pending' };
    }
    const sch = p.s ? schoolByKey_(p.s) : null;
    const code = issueTo_(name + (org ? ' / ' + org : '') + ' / ' + email, sch ? sch.name : '');
    const note = mail_(email, name, code);
    sh.appendRow([now, name, org, email, '발급', code, now, '자동 발급 · ' + note]);
    return { ok: true, status: 'issued', code: code, mailed: note === '메일 발송' };
  } finally {
    lock.releaseLock();
  }
}

/* ---------- 운영자: 승인 대기 신청 처리 ---------- */
function approveSelected() { approve_(true); }
function approveAll() { approve_(false); }
function approve_(onlySelected) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = sheet_('req');
  let rows = [];
  if (onlySelected) {
    if (ss.getActiveSheet().getName() !== SHEETS.req.name) { ss.toast('[인증신청] 탭에서 승인할 줄을 선택한 뒤 다시 누르세요.', '랭킹 관리'); return; }
    const r = ss.getActiveRange();
    for (let i = r.getRow(); i < r.getRow() + r.getNumRows(); i++) if (i > 1) rows.push(i);
  } else {
    const v = sh.getDataRange().getValues();
    for (let i = 1; i < v.length; i++) if (v[i][4] === '대기') rows.push(i + 1);
  }
  let n = 0;
  rows.forEach(row => {
    const r = sh.getRange(row, 1, 1, 8).getValues()[0];
    if (r[4] !== '대기') return;
    const code = issueTo_(r[1] + (r[2] ? ' / ' + r[2] : '') + ' / ' + r[3]);
    const note = mail_(r[3], r[1], code);
    sh.getRange(row, 5, 1, 4).setValues([['발급', code, new Date(), '운영자 승인 · ' + note]]);
    n++;
  });
  ss.toast(n + '건을 승인하고 인증번호를 발급했습니다.', '랭킹 관리');
}

/* ---------- 시트 메뉴 (운영자용) ---------- */
function onOpen() {
  SpreadsheetApp.getUi().createMenu('랭킹 관리')
    .addItem('선택한 신청 승인·발송', 'approveSelected')
    .addItem('대기 중인 신청 모두 승인·발송', 'approveAll')
    .addSeparator()
    .addItem('인증번호 10개 발급', 'issue10')
    .addItem('인증번호 50개 발급', 'issue50')
    .addSeparator()
    .addItem('랭킹 초기화(새 시즌)', 'resetRanking')
    .addToUi();
  SpreadsheetApp.getUi().createMenu('학교 관리')
    .addItem('① 계약 학교 등록 (드라이브 폴더 만들기)', 'menuRegisterSchool')
    .addItem('② 학교별 인증번호 발급 (명단·카드 만들기)', 'menuIssueSchool')
    .addItem('③ 학교 현황 보고서 만들기', 'menuReportSchool')
    .addSeparator()
    .addItem('학교 전용 주소 보기', 'menuSchoolLink')
    .addItem('샘플 학교 만들기 (연습용)', 'sampleSchool')
    .addToUi();
}
function issue10() { issue_(10); }
function issue50() { issue_(50); }
function issue_(n) {
  const sh = sheet_('codes');
  const rows = newCodes_(n).map(code => [code, '', '사용가능', today_(), '', '']);
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


/* =====================================================================
   학교 관리 · © 2026 KOREA CONTENTS LAB
   단계: ① 계약 학교 등록 → ② 학교별 인증번호 발급 → ③ 학교 현황 보고서
   구글 드라이브: 재난소통 영웅 학교 관리 / 학교명 / 01_계약서 · 02_인증번호 명단 · 03_랭킹·참여 현황 · 04_교육자료
   ===================================================================== */
const ROOT_NAME = '재난소통 영웅 학교 관리';
const COMMON_NAME = '00_공통 자료';
const SUB = ['01_계약서', '02_인증번호 명단', '03_랭킹·참여 현황', '04_교육자료'];
const stamp_ = () => Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');
const cleanSchool_ = s => String(s || '').replace(/[<>&"'\\/\u0000-\u001f]/g, '').trim().slice(0, 40);

function ensureHeads_() {
  const sh = sheet_('codes');
  if (sh.getMaxColumns() < 7) sh.insertColumnsAfter(sh.getMaxColumns(), 7 - sh.getMaxColumns());
  if (!sh.getRange(1, 7).getValue()) sh.getRange(1, 7).setValue('학교');
  sheet_('schools');
}
function folderIn_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
function root_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('ROOT_ID');
  if (id) { try { const f = DriveApp.getFolderById(id); if (!f.isTrashed()) return f; } catch (e) {} }
  const f = folderIn_(DriveApp.getRootFolder(), ROOT_NAME);
  props.setProperty('ROOT_ID', f.getId());
  folderIn_(f, COMMON_NAME);
  return f;
}
function schools_() {
  const v = sheet_('schools').getDataRange().getValues();
  const out = [];
  for (let i = 1; i < v.length; i++) if (v[i][0]) out.push({ row: i + 1, name: String(v[i][0]).trim(), key: String(v[i][1]).trim(), teacher: v[i][2], period: v[i][3], status: v[i][4], issued: Number(v[i][5]) || 0, folder: String(v[i][6] || '') });
  return out;
}
const schoolByName_ = n => schools_().find(s => s.name === cleanSchool_(n));
const cleanKey_ = k => String(k || '').toLowerCase().replace(/[^a-z0-9-]/g, '').replace(/^-+|-+$/g, '').slice(0, 30);
const schoolByKey_ = k => schools_().find(s => s.key && s.key === cleanKey_(k));
const schoolLink_ = key => GAME_URL + '?s=' + key;
const folderName_ = sc => sc.name + ' (' + sc.key + ')';
function schoolFolder_(sc) {
  const f = folderIn_(root_(), folderName_(sc));
  SUB.forEach(n => folderIn_(f, n));
  return f;
}

/* ① 계약 학교 등록: 학교목록에 한 줄 + 드라이브 폴더 + 공통 자료 복사 */
function registerSchool_(name, key, teacher, period) {
  ensureHeads_();
  name = cleanSchool_(name); key = cleanKey_(key);
  if (!name) throw new Error('학교 이름을 입력하세요.');
  let sc = schoolByName_(name);
  if (!sc) {
    if (!key || key.length < 2) throw new Error('약칭은 영문 소문자·숫자·하이픈 2자 이상으로 정해 주세요. 예: dj-hanbit');
    const dup = schoolByKey_(key);
    if (dup) throw new Error('이미 쓰는 약칭입니다: ' + key + ' (' + dup.name + ')');
    sheet_('schools').appendRow([name, key, clean_(teacher, 30), clean_(period, 40), '계약', 0, '', schoolLink_(key), stamp_()]);
    sc = schoolByName_(name);
  }
  const folder = schoolFolder_(sc);
  sheet_('schools').getRange(sc.row, 7).setValue(folder.getUrl());
  // 공통 자료(계약서 양식 · 교육안 PPT 등)를 학교 폴더로 복사 — 이미 있으면 건너뜀
  const common = folderIn_(root_(), COMMON_NAME).getFiles();
  while (common.hasNext()) {
    const file = common.next(), nm = file.getName();
    const to = /계약/.test(nm) ? folderIn_(folder, SUB[0]) : folderIn_(folder, SUB[3]);
    const copyName = /계약/.test(nm) ? name + '_' + nm.replace(/^재난소통_영웅_/, '') : nm;
    if (!to.getFilesByName(copyName).hasNext()) file.makeCopy(copyName, to);
  }
  return { school: sc, folder: folder };
}

/* ② 학교별 인증번호 발급: 번호 생성 + 명단 시트(인쇄용) + 카드 문서(오려 쓰기) */
function issueSchool_(name, n) {
  ensureHeads_();
  const sc = schoolByName_(name);
  if (!sc) throw new Error('먼저 ① 계약 학교 등록을 해 주세요: ' + name);
  n = Math.max(1, Math.min(2000, parseInt(n, 10) || 0));
  const lock = LockService.getScriptLock(); lock.waitLock(30000);
  let codes;
  try {
    codes = newCodes_(n);
    const sh = sheet_('codes');
    const rows = codes.map(code => [code, sc.name + ' 일괄 발급', '사용가능', today_(), '', '', sc.name]);
    sh.getRange(sh.getLastRow() + 1, 1, rows.length, 7).setValues(rows);
    sheet_('schools').getRange(sc.row, 6).setValue(sc.issued + n);
  } finally { lock.releaseLock(); }
  const dir = folderIn_(schoolFolder_(sc), SUB[1]);
  const title = sc.name + '_인증번호_' + n + '개_' + stamp_();
  // 명단 시트
  const ss = SpreadsheetApp.create(title + '_명단');
  const t = ss.getSheets()[0]; t.setName('명단');
  t.getRange(1, 1, 1, 5).merge().setValue(sc.name + ' · 재난소통 영웅 인증번호 명단 (' + stamp_() + ')').setFontSize(14).setFontWeight('bold');
  t.getRange(2, 1, 1, 5).merge().setValue('우리 학교 게임 주소: ' + schoolLink_(sc.key) + '  ·  학생 이름은 인쇄한 종이에만 적으세요.').setFontColor('#5b6478');
  const body = [['번호', '인증번호', '학년·반', '이름 (종이에 기록)', '나눠 준 날']].concat(codes.map((c, i) => [i + 1, c, '', '', '']));
  t.getRange(4, 1, body.length, 5).setValues(body).setVerticalAlignment('middle').setHorizontalAlignment('center').setBorder(true, true, true, true, true, true, '#a9b2c3', SpreadsheetApp.BorderStyle.SOLID);
  t.getRange(4, 1, 1, 5).setFontWeight('bold').setBackground('#e8ecf3');
  t.getRange(5, 2, codes.length, 1).setFontFamily('Roboto Mono').setFontWeight('bold').setFontSize(12);
  t.setColumnWidths(1, 1, 50); t.setColumnWidth(2, 170); t.setColumnWidth(3, 90); t.setColumnWidth(4, 160); t.setColumnWidth(5, 100);
  t.setRowHeights(5, codes.length, 26); t.setFrozenRows(4);
  DriveApp.getFileById(ss.getId()).moveTo(dir);
  // 카드 문서 (한 장에 2칸씩, 오려서 학생에게)
  const doc = DocumentApp.create(title + '_카드');
  const b = doc.getBody(); b.setMarginTop(36).setMarginBottom(36).setMarginLeft(40).setMarginRight(40);
  b.appendParagraph(sc.name + ' · 재난소통 영웅 인증번호 카드  (점선대로 오려 나눠 주세요)').setFontSize(10).setForegroundColor('#5b6478');
  const cell = c => sc.name + '\n' + c + '\n' + schoolLink_(sc.key) + '\n번호를 넣으면 기록이 이어져요. 잃어버리지 마세요.';
  const rows2 = [];
  for (let i = 0; i < codes.length; i += 2) rows2.push([cell(codes[i]), codes[i + 1] ? cell(codes[i + 1]) : '']);
  const tb = b.appendTable(rows2);
  tb.setBorderColor('#9aa3b5');
  const st = {}; st[DocumentApp.Attribute.FONT_SIZE] = 9; st[DocumentApp.Attribute.FONT_FAMILY] = 'Malgun Gothic'; tb.setAttributes(st);
  for (let r = 0; r < tb.getNumRows(); r++) for (let k = 0; k < tb.getRow(r).getNumCells(); k++) {
    const ce = tb.getCell(r, k); const tx = ce.editAsText(); const s0 = tx.getText();
    ce.setPaddingTop(8).setPaddingBottom(8).setPaddingLeft(10);
    const a = s0.indexOf('\n') + 1, z = s0.indexOf('\n', a);
    if (a > 0 && z > a) tx.setFontSize(a, z - 1, 15).setBold(a, z - 1, true).setFontFamily(a, z - 1, 'Roboto Mono');
  }
  doc.saveAndClose();
  DriveApp.getFileById(doc.getId()).moveTo(dir);
  return { n: n, list: ss.getUrl(), cards: doc.getUrl(), folder: dir.getUrl() };
}

/* ③ 학교 현황 보고서: 03 폴더에 날짜별 시트 */
function reportSchool_(name) {
  const sc = schoolByName_(name);
  if (!sc) throw new Error('등록되지 않은 학교입니다: ' + name);
  const r = schoolRank_(sc.name, '');
  const all = rankList_();
  const set = new Set(sheet_('codes').getDataRange().getValues().slice(1).filter(x => String(x[6] || '').trim() === sc.name).map(x => norm_(x[0])));
  const list = all.filter(x => set.has(norm_(x.code)));
  list.forEach((x, i) => { x.rank = i > 0 && x.total === list[i - 1].total ? list[i - 1].rank : i + 1; });
  const ss = SpreadsheetApp.create(sc.name + '_랭킹·참여 현황_' + stamp_());
  const t = ss.getSheets()[0]; t.setName('현황');
  t.getRange(1, 1).setValue(sc.name + ' · 재난소통 영웅 참여 현황 (' + stamp_() + ')').setFontSize(14).setFontWeight('bold');
  const sum = [['발급한 인증번호', r.issued], ['사용을 시작한 번호', r.started], ['랭킹에 오른 학생', r.count], ['평균 통과 관문 (7개 중)', r.avgPassed], ['적정 답변 합계', r.goods], ['학교 전용 주소', schoolLink_(sc.key)], ['드라이브 폴더', folderName_(sc)]];
  t.getRange(3, 1, sum.length, 2).setValues(sum).setBorder(true, true, true, true, true, true, '#a9b2c3', SpreadsheetApp.BorderStyle.SOLID);
  t.getRange(3, 1, sum.length, 1).setFontWeight('bold').setBackground('#e8ecf3');
  const head = [['순위', '별칭', '복장', '통과 관문', '적정 답변', '총점', '훈련 횟수']];
  const body = list.map(x => [x.rank, x.nick, x.costume, x.passed, x.goods, x.total, x.runs]);
  const y = 4 + sum.length;
  t.getRange(y, 1, 1, 7).setValues(head).setFontWeight('bold').setBackground('#e8ecf3');
  if (body.length) t.getRange(y + 1, 1, body.length, 7).setValues(body);
  t.getRange(y, 1, body.length + 1, 7).setBorder(true, true, true, true, true, true, '#a9b2c3', SpreadsheetApp.BorderStyle.SOLID).setHorizontalAlignment('center');
  t.setColumnWidth(1, 170); t.setColumnWidth(2, 140);
  DriveApp.getFileById(ss.getId()).moveTo(folderIn_(schoolFolder_(sc), SUB[2]));
  return { url: ss.getUrl(), count: r.count };
}

/* ---------- 메뉴 (운영자 화면) ---------- */
function ask_(title, msg) {
  const ui = SpreadsheetApp.getUi();
  const r = ui.prompt(title, msg, ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return null;
  return r.getResponseText().trim();
}
const schoolList_ = () => schools_().map(s => '· ' + s.name + ' [' + s.key + '] 발급 ' + s.issued + '개').join('\n') || '(아직 등록된 학교가 없습니다)';
function menuRegisterSchool() {
  const ui = SpreadsheetApp.getUi();
  const name = ask_('① 계약 학교 등록', '학교 이름을 입력하세요. 예: 대전한빛초등학교'); if (!name) return;
  const key = ask_('① 계약 학교 등록', '학교 약칭을 영문으로 정하세요. 학교 전용 게임 주소와 드라이브 폴더 이름에 함께 쓰입니다.\n영문 소문자 · 숫자 · 하이픈(-). 예: dj-hanbit'); if (!key) return;
  const teacher = ask_('① 계약 학교 등록', '담당 교사 (선택, 비워도 됩니다). 예: 김안전 교사'); if (teacher === null) return;
  const period = ask_('① 계약 학교 등록', '계약 기간 (선택). 예: 2027.3.1 ~ 2028.2.29'); if (period === null) return;
  try {
    const r = registerSchool_(name, key, teacher, period);
    ui.alert('등록 완료', '드라이브 폴더: ' + folderName_(r.school) + '\n' + r.folder.getUrl() + '\n\n학교 전용 게임 주소\n' + schoolLink_(r.school.key) + '\n\n다음 단계: ② 학교별 인증번호 발급', ui.ButtonSet.OK);
  } catch (e) { ui.alert('등록하지 못했습니다', String(e.message || e), ui.ButtonSet.OK); }
}
function menuIssueSchool() {
  const ui = SpreadsheetApp.getUi();
  const name = ask_('② 학교별 인증번호 발급', '학교 이름을 입력하세요.\n\n등록된 학교\n' + schoolList_()); if (!name) return;
  const n = ask_('② 학교별 인증번호 발급', '만들 개수를 입력하세요 (1~2000). 예: 1100'); if (!n) return;
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast('인증번호와 명단을 만드는 중입니다. 1,000개 기준 1~2분 걸립니다.', '학교 관리', 30);
    const r = issueSchool_(name, n);
    ui.alert('발급 완료', r.n + '개를 만들었습니다.\n\n인쇄용 명단\n' + r.list + '\n\n오려 쓰는 카드\n' + r.cards + '\n\n폴더\n' + r.folder, ui.ButtonSet.OK);
  } catch (e) { ui.alert('발급하지 못했습니다', String(e.message || e), ui.ButtonSet.OK); }
}
function menuReportSchool() {
  const ui = SpreadsheetApp.getUi();
  const name = ask_('③ 학교 현황 보고서', '학교 이름을 입력하세요.\n\n등록된 학교\n' + schoolList_()); if (!name) return;
  try { const r = reportSchool_(name); ui.alert('보고서 완료', '랭킹에 오른 학생 ' + r.count + '명\n\n' + r.url, ui.ButtonSet.OK); }
  catch (e) { ui.alert('보고서를 만들지 못했습니다', String(e.message || e), ui.ButtonSet.OK); }
}
function menuSchoolLink() {
  const ui = SpreadsheetApp.getUi();
  const name = ask_('학교 전용 주소', '학교 이름을 입력하세요.\n\n등록된 학교\n' + schoolList_()); if (!name) return;
  const sc = schoolByName_(name);
  ui.alert(sc ? sc.name : '찾지 못함', sc ? '이 주소를 학교에 보내 주세요. 접속하면 학교 이름과 학교 랭킹이 먼저 보입니다.\n\n' + schoolLink_(sc.key) + '\n\n드라이브 폴더: ' + folderName_(sc) : '등록되지 않은 학교입니다.', ui.ButtonSet.OK);
}
/* 연습용: 샘플초등학교 등록 + 인증번호 6개 + 현황 보고서 (편집기에서 실행해 권한 승인에도 씀) */
function sampleSchool() {
  const r = registerSchool_('샘플초등학교', 'sample', '연습용', '연습용');
  const s = schoolByName_('샘플초등학교');
  const i = s.issued ? null : issueSchool_('샘플초등학교', 6);
  const rep = reportSchool_('샘플초등학교');
  Logger.log(JSON.stringify({ folder: r.folder.getUrl(), link: schoolLink_(r.school.key), issue: i, report: rep.url }));
  return { folder: r.folder.getUrl(), link: schoolLink_(r.school.key), issue: i, report: rep.url };
}

/* 처음 한 번: 공통 자료(협업 계약서 · 교육안 PPT)를 '00_공통 자료'에 저장하고 샘플 학교를 만듭니다.
   편집기에서 이 함수를 실행하면 드라이브 · 문서 권한 승인 창이 뜹니다. */
function setupSchoolDrive() {
  const SRC = 'https://raw.githubusercontent.com/ktvwin-pixel/disaster-game/f7d96190c87c51f40711684e4bac40cec85d5911/';
  const files = [['a2.docx', '재난소통_영웅_협업_계약서.docx', MimeType.MICROSOFT_WORD], ['a1.pptx', '재난소통_영웅_교육안.pptx', MimeType.MICROSOFT_POWERPOINT]];
  const common = folderIn_(root_(), COMMON_NAME);
  const done = [];
  files.forEach(([src, name, mime]) => {
    if (common.getFilesByName(name).hasNext()) { done.push(name + ' (이미 있음)'); return; }
    const res = UrlFetchApp.fetch(SRC + src, { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) { done.push(name + ' 실패 ' + res.getResponseCode()); return; }
    common.createFile(res.getBlob().setName(name).setContentType(mime));
    done.push(name);
  });
  ensureHeads_();
  const sample = sampleSchool();
  Logger.log(JSON.stringify({ common: done, sample: sample }));
  return { common: done, sample: sample };
}

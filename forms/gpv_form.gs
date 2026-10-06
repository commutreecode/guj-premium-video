/**
 * Guj Premium Video — intake Google Form v2 + Sheet + profile.json builder (Google Apps Script)
 *
 * v2 changes: birth YEAR only · couple-photo option (grandparents, parents) · siblings branch by
 * relation (ભાઈ-ભાભી / બહેન-બનેવી / ભાઈ / બહેન get their own fields) · own Income / Property section.
 * Use a NEW Apps Script project for v2. Keep the v1 project (forms/gpv_form_v1.gs) for old responses.
 *
 * SETUP (once)
 *   1. script.google.com -> New project -> paste this file -> Save.
 *   2. Run createGujPremiumForm (authorise Forms, Sheets, Drive, triggers).
 *      The log prints the form edit / share / Sheet links and the upload questions to add.
 *   3. Apps Script cannot create "File upload" questions: add the ones in UPLOADS by hand, with EXACTLY
 *      those titles, at the end of the section named. (Run listUploadQuestions to print them again.)
 *
 * EVERY SUBMISSION (automatic)
 *   Drive "Guj Premium Video - Profiles/<id>_<first name>/" gets profile.json + photos/ (renamed),
 *   and the Sheet gets JSON + Folder columns. After editing a row: rebuildSelectedRow / rebuildAllRows.
 */

const FORM_TITLE = 'કોમ્યુટ્રી CT પ્રિમિયમ મેમ્બર - વિડિયો બાયોડેટા (Guj Premium Video)';
const DRIVE_ROOT = 'Guj Premium Video - Profiles';

// ---------------------------------------------------------------- section titles
const SEC = {
  dd: 'દાદા-દાદી',
  nn: 'નાના-નાની',
  par: 'માતા-પિતા',
  s1: 'ભાઈ/બહેન 1',
  s1bb: 'ભાઈ/બહેન 1 - બહેન-બનેવી વિગત',
  s1bh: 'ભાઈ/બહેન 1 - ભાઈ-ભાભી વિગત',
  s1b: 'ભાઈ/બહેન 1 - ભાઈ વિગત',
  s1s: 'ભાઈ/બહેન 1 - બહેન વિગત',
  s1ph: 'ભાઈ/બહેન 1 - ફોટો',
  s2bb: 'ભાઈ/બહેન 2 - બહેન-બનેવી વિગત',
  s2bh: 'ભાઈ/બહેન 2 - ભાઈ-ભાભી વિગત',
  s2b: 'ભાઈ/બહેન 2 - ભાઈ વિગત',
  s2s: 'ભાઈ/બહેન 2 - બહેન વિગત',
  s2ph: 'ભાઈ/બહેન 2 - ફોટો',
  edu: 'અભ્યાસ',
  work: 'વ્યવસાય',
  prop: 'Income / Property',
};

// ---------------------------------------------------------------- question titles (must stay identical)
const Q = {
  gender: 'ઉમેદવાર (Candidate)',
  name: 'ઉમેદવારનું પૂરું નામ - ગુજરાતીમાં (Full name)',
  first_name: 'પહેલું નામ - ગુજરાતીમાં (First name)',
  native_village: 'ગામ (Native village)',
  city: 'હાલ (Current city / area)',
  birth_year: 'જન્મ વર્ષ (Birth year)',
  marital: 'વૈવાહિક સ્થિતિ (Marital status)',
  height_ft: 'ઊંચાઈ - ફૂટ (Height, feet)',
  height_in: 'ઊંચાઈ - ઇંચ (Height, inches)',
  sect: 'સમાજ / ફિરકો (e.g. દેરાવાસી જૈન)',
  hobbies: 'શોખ - English, comma separated (Hobbies)',
  profile_url: 'CommuTree profile link',
  privacy: 'ઉમેદવારના ફોટા વિડિયોમાં (Candidate photos in video)',

  dd_name: 'દાદા-દાદી - નામ (e.g. દાદીનું નામ + દાદાનું નામ + અટક)',
  dd_village: 'દાદા-દાદી - ગામ',
  nn_name: 'નાના-નાની - નામ (e.g. નાનીનું નામ + નાનાનું નામ + અટક)',
  nn_village: 'નાના-નાની - ગામ',

  par_name: 'માતા-પિતા - નામ (માતાનું પૂરું નામ, e.g. દિવ્યા નિલેશ ખિમજી મારૂ)',
  par_village: 'માતા-પિતા - ગામ',
  par_city: 'માતા-પિતા - હાલ',
  mother_name: 'માતાનું ટૂંકું નામ (e.g. દિવ્યાબેન)',
  mother_occ: 'માતાનો વ્યવસાય - one line per row (e.g. HouseWife)',
  father_name: 'પિતાનું ટૂંકું નામ (e.g. નિલેશભાઈ)',
  father_occ: 'પિતાનો વ્યવસાય - one line per row (e.g. Business: / Company, City / (Description))',

  edu1_degree: 'અભ્યાસ 1 - Degree (e.g. B.Com)',
  edu1_inst: 'અભ્યાસ 1 - College / University',
  edu2_degree: 'અભ્યાસ 2 - Degree (optional)',
  edu2_inst: 'અભ્યાસ 2 - College / University (optional)',

  work_style: 'વ્યવસાય - કાર્ડ પ્રકાર (Job card type)',
  work_label: 'વ્યવસાય - પ્રકાર (e.g. Family Business, Job, Self-employed)',
  work_company: 'કંપની / બિઝનેસ નામ, શહેર (e.g. Maru nx, Dombivali)',
  work_desc: 'બિઝનેસ / કામ વિશે (e.g. Retailer of Steel & Home Appliances)',
  work_bullets: 'વ્યવસાય - points, one per line (for "List of points")',

  income: 'Income (optional, e.g. 20-50 Lakhs p.a.)',
  property: 'Property - one per line (e.g. Residence 3BHK at Mulund)',
};

// Sibling questions: n = 1 or 2. Each relation has its own section and fields.
const SQ = n => ({
  type: `ભાઈ/બહેન ${n} - સંબંધ (Sibling ${n})`,
  bb_sis: `ભાઈ/બહેન ${n} - બહેનનું નામ (first name, e.g. કિંજલ)`,
  bb_bil: `ભાઈ/બહેન ${n} - બનેવીનું પૂરું નામ (e.g. દિવ્ય ભાવેશ રાંભિયા)`,
  bb_place: `ભાઈ/બહેન ${n} - બહેન-બનેવી હાલ (place)`,
  bb_sis_work: `ભાઈ/બહેન ${n} - બહેનનો વ્યવસાય / અભ્યાસ`,
  bb_bil_work: `ભાઈ/બહેન ${n} - બનેવીનો વ્યવસાય`,
  bh_bro: `ભાઈ/બહેન ${n} - ભાઈનું પૂરું નામ (e.g. હાર્દિક મનોજ મારૂ)`,
  bh_sil: `ભાઈ/બહેન ${n} - ભાભીનું નામ (first name)`,
  bh_place: `ભાઈ/બહેન ${n} - ભાઈ-ભાભી હાલ (place)`,
  bh_bro_work: `ભાઈ/બહેન ${n} - ભાઈનો વ્યવસાય`,
  bh_sil_work: `ભાઈ/બહેન ${n} - ભાભીનો વ્યવસાય / અભ્યાસ`,
  b_name: `ભાઈ/બહેન ${n} - ભાઈનું પૂરું નામ (unmarried)`,
  b_place: `ભાઈ/બહેન ${n} - ભાઈ હાલ (place)`,
  b_work: `ભાઈ/બહેન ${n} - ભાઈનો અભ્યાસ / વ્યવસાય (e.g. STUDENT)`,
  s_name: `ભાઈ/બહેન ${n} - બહેનનું પૂરું નામ (unmarried)`,
  s_place: `ભાઈ/બહેન ${n} - બહેન હાલ (place)`,
  s_work: `ભાઈ/બહેન ${n} - બહેનનો અભ્યાસ / વ્યવસાય`,
});

const SIB_TYPES = {      // choice text -> [relation in JSON, field group]
  'બહેન - બનેવી': ['bahen-banevi', 'bb'],
  'ભાઈ - ભાભી': ['bhai-bhabhi', 'bh'],
  'મોટા ભાઈ - ભાભી': ['mota-bhai-bhabhi', 'bh'],
  'ભાઈ (અપરિણીત)': ['bhai', 'b'],
  'બહેન (અપરિણીત)': ['bahen', 's'],
};
const SIB_NONE = 'કોઈ નહીં / વધુ નથી (None)';

const CHOICES = {
  gender: { 'છોકરો (Boy)': 'boy', 'છોકરી (Girl)': 'girl' },
  marital: { 'Single': 'Single', 'Divorced': 'Divorced', 'Widow': 'Widow', 'Widower': 'Widower' },
  privacy: { 'Show clearly': 'clear', 'Blur': 'blur', 'Hide (no candidate photos)': 'hide' },
  work_style: { 'Business (logo + name + description)': 'business', 'List of points': 'bullets' },
};

// ---------------------------------------------------------------- upload questions (add by hand)
// role -> [title, max files (Forms allows 1/5/10), section, required]
const UPLOADS = {
  hero:      ['ફોટો: ઉમેદવાર - મુખ્ય ફોટો (Main photo)', 1, 'first section (ઉમેદવાર)', true],
  gallery:   ['ફોટા: ઉમેદવાર - ગેલેરી, 6 to 10 photos (Gallery)', 10, 'first section (ઉમેદવાર)'],
  dadi:      ['ફોટો: દાદી', 1, SEC.dd],
  dada:      ['ફોટો: દાદા', 1, SEC.dd],
  dd_couple: ['ફોટો: દાદા-દાદી સાથે (couple photo, optional)', 1, SEC.dd],
  nani:      ['ફોટો: નાની', 1, SEC.nn],
  nana:      ['ફોટો: નાના', 1, SEC.nn],
  nn_couple: ['ફોટો: નાના-નાની સાથે (couple photo, optional)', 1, SEC.nn],
  mata:      ['ફોટો: માતા', 1, SEC.par],
  pita:      ['ફોટો: પિતા', 1, SEC.par],
  par_couple:['ફોટો: માતા-પિતા સાથે (couple photo, optional)', 1, SEC.par],
  s1:        ['ફોટો: ભાઈ/બહેન 1 (1 couple photo or 2 separate)', 5, SEC.s1ph + ' - at the TOP, above "ભાઈ/બહેન 2 - સંબંધ"'],
  s2:        ['ફોટો: ભાઈ/બહેન 2 (1 couple photo or 2 separate)', 5, SEC.s2ph],
  edu:       ['ફોટો: અભ્યાસ કાર્ડ માટે (optional)', 1, SEC.edu],
  work:      ['ફોટો: વ્યવસાય કાર્ડ માટે (optional)', 1, SEC.work],
  logo:      ['લોગો: કંપની / બિઝનેસ (PNG, optional)', 1, SEC.work],
};

const COUPLE_HELP = 'ફોટા: અલગ અલગ (2 ફોટા) અથવા એક સાથેનો couple ફોટો — બંનેમાંથી એક. ' +
                    'Couple ફોટો આડો (landscape) હોય તો વિડિયોમાં પહોળી ફ્રેમ આવશે.';

// ================================================================ create form
function createGujPremiumForm() {
  const f = FormApp.create(FORM_TITLE);
  f.setDescription(
    'CommuTree CT Premium Member વિડિયો બાયોડેટા માટે વિગત ભરો.\n' +
    '• નામ ગુજરાતીમાં લખો.\n' +
    '• ફોટા ઓરિજિનલ મોકલો (WhatsApp forward નહીં), ફોટા પર કોઈ લખાણ ન હોવું જોઈએ.\n' +
    '• જે વિગત ન હોય તે ખાલી રાખો — તે કાર્ડ વિડિયોમાં નહીં આવે.');

  const text = (t, req) => f.addTextItem().setTitle(t).setRequired(!!req);
  const para = (t, req) => f.addParagraphTextItem().setTitle(t).setRequired(!!req);
  const mc = (t, ch, req) => f.addMultipleChoiceItem().setTitle(t)
      .setChoiceValues(Object.keys(CHOICES[ch])).setRequired(!!req);
  const list = (t, vals, req) => f.addListItem().setTitle(t).setChoiceValues(vals).setRequired(!!req);
  const page = (t, help) => f.addPageBreakItem().setTitle(t).setHelpText(help || '');

  // 1. candidate (first section)
  mc(Q.gender, 'gender', true);
  text(Q.name, true);
  text(Q.first_name, true);
  text(Q.native_village, true);
  text(Q.city, true);
  const years = [];
  for (let y = new Date().getFullYear() - 18; y >= 1965; y--) years.push(String(y));
  list(Q.birth_year, years, true);
  mc(Q.marital, 'marital', true);
  list(Q.height_ft, ['4', '5', '6', '7'], true);
  list(Q.height_in, ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'], true);
  text(Q.sect, true);
  text(Q.hobbies);
  text(Q.profile_url);
  mc(Q.privacy, 'privacy', true);

  // 2-4. family
  page(SEC.dd, COUPLE_HELP);
  text(Q.dd_name); text(Q.dd_village);
  page(SEC.nn, COUPLE_HELP);
  text(Q.nn_name); text(Q.nn_village);
  page(SEC.par, COUPLE_HELP);
  text(Q.par_name); text(Q.par_village); text(Q.par_city);
  text(Q.mother_name); para(Q.mother_occ);
  text(Q.father_name); para(Q.father_occ);

  // 5. siblings with branching
  page(SEC.s1, 'સંબંધ પસંદ કરો — પછી તે મુજબની વિગત પૂછાશે.');
  const s1q = f.addMultipleChoiceItem().setTitle(SQ(1).type).setRequired(true);
  const p1 = sibPages_(f, 1, page, text);         // {bb, bh, b, s, ph} page breaks
  const s2q = f.addMultipleChoiceItem().setTitle(SQ(2).type).setRequired(true);  // sits in s1 photo section
  const p2 = sibPages_(f, 2, page, text);

  // 6-8. education, work, income/property
  const pEdu = page(SEC.edu);
  text(Q.edu1_degree); text(Q.edu1_inst); text(Q.edu2_degree); text(Q.edu2_inst);
  page(SEC.work);
  mc(Q.work_style, 'work_style');
  text(Q.work_label); text(Q.work_company); text(Q.work_desc); para(Q.work_bullets);
  page(SEC.prop, 'Income / Property card માટે. ન હોય તો ખાલી રાખો.');
  text(Q.income); para(Q.property);

  // branching choices (set after all pages exist)
  const choices = (q, p) => Object.keys(SIB_TYPES).map(k => q.createChoice(k, p[SIB_TYPES[k][1]]))
      .concat([q.createChoice(SIB_NONE, pEdu)]);
  s1q.setChoices(choices(s1q, p1));
  s2q.setChoices(choices(s2q, p2));
  // after each relation section, jump to that sibling's photo section
  [p1, p2].forEach(p => { p.bh.setGoToPage(p.ph); p.b.setGoToPage(p.ph); p.s.setGoToPage(p.ph); });
  // (bb -> next page is bh: its break jumps to ph; s -> ph is next linearly)
  // after sibling-2 photos the form continues linearly to Education.

  const ss = SpreadsheetApp.create(FORM_TITLE + ' v2 (Responses)');
  f.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());
  ScriptApp.newTrigger('onGpvSubmit').forSpreadsheet(ss).onFormSubmit().create();

  Logger.log('Form (edit):   ' + f.getEditUrl());
  Logger.log('Form (share):  ' + f.getPublishedUrl());
  Logger.log('Sheet:         ' + ss.getUrl());
  listUploadQuestions();
}

/** Creates the 4 relation sections + photo section for sibling n. Returns their page breaks.
 *  PageBreakItem.setGoToPage(x) on a break = where to go after finishing the section BEFORE it. */
function sibPages_(f, n, page, text) {
  const q = SQ(n);
  const t = k => (n === 1 ? SEC['s1' + k] : SEC['s2' + k]);
  const bb = page(t('bb'));
  text(q.bb_sis); text(q.bb_bil); text(q.bb_place); text(q.bb_sis_work); text(q.bb_bil_work);
  const bh = page(t('bh'));            // its goTo -> photos  (= exit of the bb section)
  text(q.bh_bro); text(q.bh_sil); text(q.bh_place); text(q.bh_bro_work); text(q.bh_sil_work);
  const b = page(t('b'));              // exit of bh section
  text(q.b_name); text(q.b_place); text(q.b_work);
  const s = page(t('s'));              // exit of b section
  text(q.s_name); text(q.s_place); text(q.s_work);
  const ph = page(t('ph'), 'ફોટો: 1 couple ફોટો અથવા 2 અલગ ફોટા.');   // s section flows here linearly
  return { bb: bb, bh: bh, b: b, s: s, ph: ph };
}

function listUploadQuestions() {
  Logger.log('Add these "File upload" questions (exact titles, at the END of the section named):');
  Object.keys(UPLOADS).forEach(k => {
    const [t, n, s, req] = UPLOADS[k];
    Logger.log(`  [${s}]  ${t}   (max files: ${n}${req ? ', required' : ''})`);
  });
}

// ================================================================ submission -> JSON
function onGpvSubmit(e) { buildRow_(e.range.getSheet(), e.range.getRow()); }

function rebuildSelectedRow() {
  const sh = sheet_();
  const r = SpreadsheetApp.getActiveRange() ? SpreadsheetApp.getActiveRange().getRow() : sh.getLastRow();
  if (r < 2) throw new Error('Select a cell in a response row first.');
  buildRow_(sh, r);
}

function rebuildAllRows() {
  const sh = sheet_();
  for (let r = 2; r <= sh.getLastRow(); r++) buildRow_(sh, r);
}

function sheet_() {
  const id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  const ss = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
  return ss.getSheets().find(s => s.getFormUrl()) || ss.getSheets()[0];
}

function buildRow_(sh, row) {
  const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(String);
  const vals = sh.getRange(row, 1, 1, headers.length).getValues()[0];
  const by = {};
  headers.forEach((h, i) => by[h.trim()] = vals[i]);
  const raw = t => String(by[t] == null ? '' : by[t]).trim();
  const get = k => raw(Q[k]);
  const linesOf = s => s.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  const lines = k => linesOf(get(k));
  const pick = (k, ch) => CHOICES[ch][get(k)] || '';
  const firstWord = s => s.split(/\s+/)[0] || '';

  const first = get('first_name') || firstWord(get('name'));
  const m = get('profile_url').match(/ProfileID=(\d+)/i);
  const id = m ? m[1] : 'gpv-' + row;

  const root = folder_(DriveApp.getRootFolder(), DRIVE_ROOT);
  const pf = folder_(root, id + '_' + first);
  const dir = folder_(pf, 'photos');
  const up = (role, nameFn, max) => {
    const ids = raw(UPLOADS[role][0]).split(',').map(s => (s.match(/[-\w]{25,}/) || [])[0])
        .filter(Boolean).slice(0, max || 10);
    return ids.map((fid, i) => copy_(fid, dir, nameFn ? nameFn(i) : (ids.length > 1 ? `${role}_${i + 1}` : role)));
  };

  const p = { version: 2, id: id, theme: pick('gender', 'gender') || 'boy', lang: 'gu',
              privacy: pick('privacy', 'privacy') || 'clear',
              name: get('name'), first_name: first,
              native_village: get('native_village'), city: get('city') };
  const yr = Number((get('birth_year').match(/(19|20)\d\d/) || [''])[0]);
  if (yr) p.birth_year = yr;
  p.marital_status = pick('marital', 'marital') || get('marital');
  if (get('height_ft')) p.height = `${get('height_ft')}'${get('height_in') || 0}"`;
  if (get('sect')) p.sect = get('sect');

  p.photos = {};
  const hero = up('hero'), gallery = up('gallery', i => 'g' + (i + 1));
  if (hero.length) p.photos.hero = hero[0];
  if (gallery.length) p.photos.gallery = gallery;

  // couple photo wins over separate photos (renderer picks the frame from its orientation)
  const famPhotos = (couple, a, b) => {
    const c = up(couple);
    return c.length ? c.slice(0, 1) : up(a).concat(up(b));
  };
  const pair = (nameK, villK, couple, a, b) => {
    if (!get(nameK)) return null;
    const o = { display_name: get(nameK) };
    if (get(villK)) o.village = get(villK);
    const ph = famPhotos(couple, a, b);
    if (ph.length) o.photos = ph;
    return o;
  };
  const dd = pair('dd_name', 'dd_village', 'dd_couple', 'dadi', 'dada'); if (dd) p.dada_dadi = dd;
  const nn = pair('nn_name', 'nn_village', 'nn_couple', 'nani', 'nana'); if (nn) p.nana_nani = nn;

  const mata = up('mata'), pita = up('pita'), parC = up('par_couple');
  if (get('par_name')) {
    p.parents = { display_name: get('par_name') };
    if (get('par_village')) p.parents.village = get('par_village');
    if (get('par_city')) p.parents.city = get('par_city');
    if (p.sect) p.parents.sect = p.sect;
    const ph = parC.length ? parC.slice(0, 1) : mata.concat(pita);
    if (ph.length) p.parents.photos = ph;
  }
  if (get('mother_name') || lines('mother_occ').length) {
    p.mother = { name: get('mother_name'), occupation: lines('mother_occ') };
    if (mata.length) p.mother.photo = mata[0];
  }
  if (get('father_name') || lines('father_occ').length) {
    p.father = { name: get('father_name'), occupation: lines('father_occ') };
    if (pita.length) p.father.photo = pita[0];
  }

  // siblings
  p.siblings = [];
  [1, 2].forEach(n => {
    const q = SQ(n), t = raw(q.type);
    if (!SIB_TYPES[t]) return;
    const [relation, g] = SIB_TYPES[t];
    const r = k => raw(q[k]);
    let s;
    if (g === 'bb' && (r('bb_sis') || r('bb_bil'))) {
      s = { relation, display_name: [r('bb_sis'), r('bb_bil')].filter(Boolean).join(' '), place: r('bb_place'),
            details: [[r('bb_sis'), r('bb_sis_work')], [firstWord(r('bb_bil')), r('bb_bil_work')]] };
    } else if (g === 'bh' && (r('bh_bro') || r('bh_sil'))) {
      s = { relation, display_name: [r('bh_sil'), r('bh_bro')].filter(Boolean).join(' '), place: r('bh_place'),
            details: [[firstWord(r('bh_bro')), r('bh_bro_work')], [r('bh_sil'), r('bh_sil_work')]] };
    } else if (g === 'b' && r('b_name')) {
      s = { relation, display_name: r('b_name'), place: r('b_place'), details: [['', r('b_work')]] };
    } else if (g === 's' && r('s_name')) {
      s = { relation, display_name: r('s_name'), place: r('s_place'), details: [['', r('s_work')]] };
    }
    if (!s) return;
    s.details = s.details.filter(d => d[1]).map(d => ({ who: d[0], text: d[1] }));
    if (!s.place) delete s.place;
    const ph = up('s' + n, null, 2);   // card shows max 2 photos
    if (ph.length) s.photos = ph;
    p.siblings.push(s);
  });
  if (!p.siblings.length) delete p.siblings;

  // education
  const edu = [], eduPh = up('edu');
  [['edu1_degree', 'edu1_inst'], ['edu2_degree', 'edu2_inst']].forEach(([dg, ins], i) => {
    if (!get(dg)) return;
    const o = { degree: get(dg) };
    if (get(ins)) o.institute = get(ins);
    if (i === 0 && eduPh.length) o.photo = eduPh[0];
    edu.push(o);
  });
  if (edu.length) p.education = edu;

  // work
  const style = pick('work_style', 'work_style') || (get('work_company') ? 'business' : 'bullets');
  const workPh = up('work'), logo = up('logo');
  if (style === 'business' && (get('work_company') || get('work_desc'))) {
    p.work = { style: 'business' };
    if (get('work_label')) p.work.label = get('work_label');
    if (logo.length) p.work.logo = logo[0];
    if (get('work_company')) p.work.company = get('work_company');
    if (get('work_desc')) p.work.desc = get('work_desc');
    if (workPh.length) p.work.photo = workPh[0];
  } else if (lines('work_bullets').length) {
    p.work = { style: 'bullets', bullets: lines('work_bullets') };
    if (get('work_label')) p.work.label = get('work_label');
    if (workPh.length) p.work.photo = workPh[0];
  }

  // income / property
  const prop = [];
  if (get('income')) prop.push('Income: ' + get('income'));
  lines('property').forEach(l => prop.push(l));
  if (prop.length) p.property = prop;

  const hob = get('hobbies').split(/[,\n]/).map(s => s.trim()).filter(Boolean);
  if (hob.length) p.hobbies = hob;
  if (get('profile_url')) p.profile_url = get('profile_url');

  const json = JSON.stringify(p, null, 2);
  writeFile_(pf, 'profile.json', json);
  setCol_(sh, row, 'JSON', json);
  setCol_(sh, row, 'Folder', pf.getUrl());
}

// ---------------------------------------------------------------- helpers
function folder_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function copy_(fileId, dir, base) {
  const src = DriveApp.getFileById(fileId);
  const ext = (src.getName().match(/\.(jpe?g|png|webp|heic)$/i) || ['', 'jpg'])[1].toLowerCase();
  const name = base + '.' + ext;
  const old = dir.getFilesByName(name);
  while (old.hasNext()) old.next().setTrashed(true);
  src.makeCopy(name, dir);
  return 'photos/' + name;
}

function writeFile_(dir, name, content) {
  const old = dir.getFilesByName(name);
  while (old.hasNext()) old.next().setTrashed(true);
  dir.createFile(name, content, MimeType.PLAIN_TEXT);
}

function setCol_(sh, row, title, value) {
  const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(String);
  let c = headers.indexOf(title) + 1;
  if (!c) { c = sh.getLastColumn() + 1; sh.getRange(1, c).setValue(title); }
  sh.getRange(row, c).setValue(value);
}

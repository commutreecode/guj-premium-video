/**
 * Guj Premium Video — Google Form + Sheet + profile.json builder (Google Apps Script)
 *
 * SETUP (once)
 *   1. script.google.com -> New project -> paste this file -> Save.
 *   2. Run createGujPremiumForm  (authorise Forms, Sheets, Drive).
 *      The log prints the form edit link, the public link and the Sheet link.
 *   3. Apps Script cannot create "File upload" questions. Open the form editor and add the
 *      upload questions listed in UPLOADS below, with EXACTLY those titles, in the sections named.
 *      (Run listUploadQuestions to print the list again.)
 *
 * EVERY SUBMISSION (automatic)
 *   - A Drive folder  "Guj Premium Video - Profiles/<id>_<first name>/"  is created with
 *     profile.json + photos/ (uploads copied and renamed: hero.jpg, dada.jpg, g1.jpg ...).
 *   - The Sheet gets two columns: JSON (the profile JSON) and Folder (link to that folder).
 *   - To render: download the folder (zip) from Drive and give it to the renderer:
 *       profiles/<name>/profile.json + profiles/<name>/photos/...
 *
 * AFTER EDITING A ROW IN THE SHEET
 *   - Select a cell in that row and run rebuildSelectedRow (or rebuildAllRows).
 */

const FORM_TITLE = 'કોમ્યુટ્રી CT પ્રિમિયમ મેમ્બર - વિડિયો બાયોડેટા (Guj Premium Video)';
const DRIVE_ROOT = 'Guj Premium Video - Profiles';

// ---------------------------------------------------------------- question titles
// Keys are used by the JSON builder; titles must stay identical in the form.
const Q = {
  gender: 'ઉમેદવાર (Candidate)',
  name: 'ઉમેદવારનું પૂરું નામ - ગુજરાતીમાં (Full name)',
  first_name: 'પહેલું નામ - ગુજરાતીમાં (First name)',
  native_village: 'ગામ (Native village)',
  city: 'હાલ (Current city / area)',
  dob: 'જન્મ તારીખ (Date of birth)',
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

  s1_rel: 'ભાઈ/બહેન 1 - સંબંધ (Sibling 1 relation)',
  s1_name: 'ભાઈ/બહેન 1 - નામ (as on card)',
  s1_place: 'ભાઈ/બહેન 1 - હાલ (place)',
  s1_details: 'ભાઈ/બહેન 1 - વિગત, one line per person (e.g. કિંજલ: Teacher)',
  s2_rel: 'ભાઈ/બહેન 2 - સંબંધ (Sibling 2 relation)',
  s2_name: 'ભાઈ/બહેન 2 - નામ (as on card)',
  s2_place: 'ભાઈ/બહેન 2 - હાલ (place)',
  s2_details: 'ભાઈ/બહેન 2 - વિગત, one line per person',

  edu1_degree: 'અભ્યાસ 1 - Degree (e.g. B.Com)',
  edu1_inst: 'અભ્યાસ 1 - College / University',
  edu2_degree: 'અભ્યાસ 2 - Degree (optional)',
  edu2_inst: 'અભ્યાસ 2 - College / University (optional)',

  work_style: 'વ્યવસાય - કાર્ડ પ્રકાર (Job card type)',
  work_label: 'વ્યવસાય - પ્રકાર (e.g. Family Business, Job, Self-employed)',
  work_company: 'કંપની / બિઝનેસ નામ, શહેર (e.g. Maru nx, Dombivali)',
  work_desc: 'બિઝનેસ / કામ વિશે (e.g. Retailer of Steel & Home Appliances)',
  work_bullets: 'વ્યવસાય - points, one per line (for "List of points")',

  property: 'Income / Property - one per line (e.g. Residence 3BHK at Mulund)',
};

const CHOICES = {
  gender: { 'છોકરો (Boy)': 'boy', 'છોકરી (Girl)': 'girl' },
  marital: { 'Single': 'Single', 'Divorced': 'Divorced', 'Widow': 'Widow', 'Widower': 'Widower' },
  privacy: { 'Show clearly': 'clear', 'Blur': 'blur', 'Hide (no candidate photos)': 'hide' },
  rel: {
    'બહેન - બનેવી (Sister & brother-in-law)': 'bahen-banevi',
    'ભાઈ - ભાભી (Brother & sister-in-law)': 'bhai-bhabhi',
    'મોટા ભાઈ - ભાભી (Elder brother & sister-in-law)': 'mota-bhai-bhabhi',
    'ભાઈ (Brother)': 'bhai',
    'બહેન (Sister)': 'bahen',
  },
  work_style: { 'Business (logo + name + description)': 'business', 'List of points': 'bullets' },
};

// ---------------------------------------------------------------- upload questions (add manually)
// role -> [title, max files, section]
const UPLOADS = {
  hero:    ['ફોટો: ઉમેદવાર - મુખ્ય ફોટો (Main photo)', 1, 'ઉમેદવાર'],
  gallery: ['ફોટા: ઉમેદવાર - ગેલેરી, 6 to 10 photos (Gallery)', 10, 'ઉમેદવાર'],
  dadi:    ['ફોટો: દાદી', 1, 'દાદા-દાદી / નાના-નાની'],
  dada:    ['ફોટો: દાદા', 1, 'દાદા-દાદી / નાના-નાની'],
  nani:    ['ફોટો: નાની', 1, 'દાદા-દાદી / નાના-નાની'],
  nana:    ['ફોટો: નાના', 1, 'દાદા-દાદી / નાના-નાની'],
  mata:    ['ફોટો: માતા', 1, 'માતા-પિતા'],
  pita:    ['ફોટો: પિતા', 1, 'માતા-પિતા'],
  s1:      ['ફોટો: ભાઈ/બહેન 1 (1 joint photo or 2 photos)', 2, 'ભાઈ/બહેન'],
  s2:      ['ફોટો: ભાઈ/બહેન 2 (1 joint photo or 2 photos)', 2, 'ભાઈ/બહેન'],
  edu:     ['ફોટો: અભ્યાસ કાર્ડ માટે (optional)', 1, 'અભ્યાસ / વ્યવસાય'],
  work:    ['ફોટો: વ્યવસાય કાર્ડ માટે (optional)', 1, 'અભ્યાસ / વ્યવસાય'],
  logo:    ['લોગો: કંપની / બિઝનેસ (PNG, optional)', 1, 'અભ્યાસ / વ્યવસાય'],
};

// ================================================================ create form
function createGujPremiumForm() {
  const f = FormApp.create(FORM_TITLE);
  f.setDescription(
    'CommuTree CT Premium Member વિડિયો બાયોડેટા માટે વિગત ભરો.\n' +
    '• નામ ગુજરાતીમાં લખો.\n' +
    '• ફોટા ઓરિજિનલ મોકલો (WhatsApp forward નહીં), ફોટા પર કોઈ લખાણ ન હોવું જોઈએ.\n' +
    '• જે વિગત ન હોય તે ખાલી રાખો — તે કાર્ડ વિડિયોમાં નહીં આવે.');

  const text = (k, req) => f.addTextItem().setTitle(Q[k]).setRequired(!!req);
  const para = (k, req) => f.addParagraphTextItem().setTitle(Q[k]).setRequired(!!req);
  const mc = (k, ch, req) => f.addMultipleChoiceItem().setTitle(Q[k])
      .setChoiceValues(Object.keys(CHOICES[ch])).setRequired(!!req);
  const list = (k, vals, req) => f.addListItem().setTitle(Q[k]).setChoiceValues(vals).setRequired(!!req);
  const section = (t, d) => f.addPageBreakItem().setTitle(t).setHelpText(d || '');

  // Section 1: candidate
  mc('gender', 'gender', true);
  text('name', true);
  text('first_name', true);
  text('native_village', true);
  text('city', true);
  f.addDateItem().setTitle(Q.dob).setRequired(true);
  mc('marital', 'marital', true);
  list('height_ft', ['4', '5', '6', '7'], true);
  list('height_in', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'], true);
  text('sect', true);
  text('hobbies');
  text('profile_url');
  mc('privacy', 'privacy', true);

  section('દાદા-દાદી / નાના-નાની', 'ફોટા અલગ અલગ (દાદી, દાદા) અથવા એક સાથે - બંને ચાલશે.');
  text('dd_name'); text('dd_village');
  text('nn_name'); text('nn_village');

  section('માતા-પિતા');
  text('par_name'); text('par_village'); text('par_city');
  text('mother_name'); para('mother_occ');
  text('father_name'); para('father_occ');

  section('ભાઈ/બહેન', 'Sibling ન હોય તો ખાલી રાખો.');
  mc('s1_rel', 'rel'); text('s1_name'); text('s1_place'); para('s1_details');
  mc('s2_rel', 'rel'); text('s2_name'); text('s2_place'); para('s2_details');

  section('અભ્યાસ / વ્યવસાય');
  text('edu1_degree'); text('edu1_inst'); text('edu2_degree'); text('edu2_inst');
  mc('work_style', 'work_style');
  text('work_label'); text('work_company'); text('work_desc'); para('work_bullets');
  para('property');

  const ss = SpreadsheetApp.create(FORM_TITLE + ' (Responses)');
  f.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());
  ScriptApp.newTrigger('onGpvSubmit').forSpreadsheet(ss).onFormSubmit().create();

  Logger.log('Form (edit):   ' + f.getEditUrl());
  Logger.log('Form (share):  ' + f.getPublishedUrl());
  Logger.log('Sheet:         ' + ss.getUrl());
  listUploadQuestions();
}

function listUploadQuestions() {
  Logger.log('Add these "File upload" questions in the form editor (exact titles):');
  Object.keys(UPLOADS).forEach(k => {
    const [t, n, s] = UPLOADS[k];
    Logger.log(`  [${s}]  ${t}   (max files: ${n}${k === 'hero' ? ', required' : ''})`);
  });
}

// ================================================================ submission -> JSON
function onGpvSubmit(e) {
  const sh = e.range.getSheet();
  buildRow_(sh, e.range.getRow());
}

function rebuildSelectedRow() {
  const sh = sheet_();
  const row = SpreadsheetApp.getActiveRange() ? SpreadsheetApp.getActiveRange().getRow() : sh.getLastRow();
  if (row < 2) throw new Error('Select a cell in a response row first.');
  buildRow_(sh, row);
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
  const byTitle = {};
  headers.forEach((h, i) => byTitle[h.trim()] = vals[i]);
  const get = k => String(byTitle[Q[k]] == null ? '' : byTitle[Q[k]]).trim();
  const lines = k => get(k).split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  const pick = (k, ch) => CHOICES[ch][get(k)] || '';

  const first = get('first_name') || get('name').split(/\s+/)[0];
  const m = get('profile_url').match(/ProfileID=(\d+)/i);
  const id = m ? m[1] : 'gpv-' + row;

  // folder for this profile
  const root = folder_(DriveApp.getRootFolder(), DRIVE_ROOT);
  const pf = folder_(root, id + '_' + first);
  const photosDir = folder_(pf, 'photos');
  const up = (role, idx) => {
    const t = UPLOADS[role][0];
    const ids = String(byTitle[t] || '').split(',').map(s => (s.match(/[-\w]{25,}/) || [])[0]).filter(Boolean);
    return ids.map((fid, i) => copy_(fid, photosDir, idx ? idx(i) : (ids.length > 1 ? role + '_' + (i + 1) : role)));
  };

  const p = { version: 1, id: id, theme: pick('gender', 'gender') || 'boy', lang: 'gu',
              privacy: pick('privacy', 'privacy') || 'clear',
              name: get('name'), first_name: first,
              native_village: get('native_village'), city: get('city') };
  const dob = byTitle[Q.dob];
  if (dob instanceof Date) { p.dob = Utilities.formatDate(dob, 'Asia/Kolkata', 'yyyy-MM-dd'); p.birth_year = dob.getFullYear(); }
  else if (get('dob')) { p.dob = get('dob'); p.birth_year = Number((get('dob').match(/(19|20)\d\d/) || [''])[0]) || undefined; }
  p.marital_status = pick('marital', 'marital') || get('marital');
  if (get('height_ft')) p.height = `${get('height_ft')}'${get('height_in') || 0}"`;
  if (get('sect')) p.sect = get('sect');

  const hero = up('hero');
  const gallery = up('gallery', i => 'g' + (i + 1));
  p.photos = {};
  if (hero.length) p.photos.hero = hero[0];
  if (gallery.length) p.photos.gallery = gallery;

  const pair = (nameK, villK, a, b) => {
    if (!get(nameK)) return null;
    const ph = up(a).concat(up(b));
    const o = { display_name: get(nameK) };
    if (get(villK)) o.village = get(villK);
    if (ph.length) o.photos = ph;
    return o;
  };
  const dd = pair('dd_name', 'dd_village', 'dadi', 'dada'); if (dd) p.dada_dadi = dd;
  const nn = pair('nn_name', 'nn_village', 'nani', 'nana'); if (nn) p.nana_nani = nn;

  const mata = up('mata'), pita = up('pita');
  if (get('par_name')) {
    p.parents = { display_name: get('par_name') };
    if (get('par_village')) p.parents.village = get('par_village');
    if (get('par_city')) p.parents.city = get('par_city');
    if (p.sect) p.parents.sect = p.sect;
    const ph = mata.concat(pita); if (ph.length) p.parents.photos = ph;
  }
  if (get('mother_name') || lines('mother_occ').length) {
    p.mother = { name: get('mother_name'), occupation: lines('mother_occ') };
    if (mata.length) p.mother.photo = mata[0];
  }
  if (get('father_name') || lines('father_occ').length) {
    p.father = { name: get('father_name'), occupation: lines('father_occ') };
    if (pita.length) p.father.photo = pita[0];
  }

  p.siblings = [];
  [['s1_rel', 's1_name', 's1_place', 's1_details', 's1'], ['s2_rel', 's2_name', 's2_place', 's2_details', 's2']]
    .forEach(([r, n, pl, d, role]) => {
      if (!get(n)) return;
      const s = { relation: pick(r, 'rel') || 'bhai', display_name: get(n) };
      if (get(pl)) s.place = get(pl);
      const ph = up(role); if (ph.length) s.photos = ph;
      s.details = lines(d).map(l => {
        const i = l.search(/[:：]/);
        return i > 0 ? { who: l.slice(0, i).trim(), text: l.slice(i + 1).trim() } : { who: '', text: l };
      });
      p.siblings.push(s);
    });
  if (!p.siblings.length) delete p.siblings;

  const edu = [];
  const eduPh = up('edu');
  [['edu1_degree', 'edu1_inst'], ['edu2_degree', 'edu2_inst']].forEach(([dg, ins], i) => {
    if (!get(dg)) return;
    const o = { degree: get(dg) };
    if (get(ins)) o.institute = get(ins);
    if (i === 0 && eduPh.length) o.photo = eduPh[0];
    edu.push(o);
  });
  if (edu.length) p.education = edu;

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
  if (lines('property').length) p.property = lines('property');
  const hob = get('hobbies').split(/[,\n]/).map(s => s.trim()).filter(Boolean);
  if (hob.length) p.hobbies = hob;
  if (get('profile_url')) p.profile_url = get('profile_url');

  const json = JSON.stringify(p, null, 2);
  writeFile_(pf, 'profile.json', json);
  setCol_(sh, headers, row, 'JSON', json);
  setCol_(sh, sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(String), row, 'Folder', pf.getUrl());
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

function setCol_(sh, headers, row, title, value) {
  let c = headers.indexOf(title) + 1;
  if (!c) { c = sh.getLastColumn() + 1; sh.getRange(1, c).setValue(title); }
  sh.getRange(row, c).setValue(value);
}

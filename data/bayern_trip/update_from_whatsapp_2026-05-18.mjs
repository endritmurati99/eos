import fs from 'node:fs';

const token = fs.readFileSync('/data/.openclaw/secrets/notion.token', 'utf8').trim();
const version = '2022-06-28';

const ids = {
  pages: {
    comms: '363986920e81815ea740e04ab5be5f35'
  },
  databases: {
    participants: '363986920e8181f898f1de296c3720e2',
    dates: '363986920e81811aa545e500b199bdd0',
    tasks: '363986920e81817482c6eaed18539cd9',
    logistics: '363986920e8181c29af0d8e22b57d34a'
  }
};

async function notion(path, { method = 'GET', body } = {}) {
  const res = await fetch(`https://api.notion.com/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      'Notion-Version': version,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) throw new Error(`${method} ${path} failed: ${res.status} ${data.code || ''} ${data.message || text}`);
  return data;
}

const rt = (content) => [{ type: 'text', text: { content: String(content ?? '').slice(0, 1900) } }];
const titleProp = (s) => ({ title: rt(s) });
const richProp = (s) => ({ rich_text: s ? rt(s) : [] });
const selectProp = (s) => ({ select: s ? { name: s } : null });
const dateProp = (s) => ({ date: s ? { start: s } : null });
const numProp = (n) => ({ number: n === null || n === undefined ? null : n });

const h2 = (content) => ({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(content) } });
const h3 = (content) => ({ object: 'block', type: 'heading_3', heading_3: { rich_text: rt(content) } });
const bul = (content) => ({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(content) } });
const callout = (emoji, content, color = 'gray_background') => ({ object: 'block', type: 'callout', callout: { icon: { type: 'emoji', emoji }, rich_text: rt(content), color } });

function plainTitle(page, prop) {
  return page.properties?.[prop]?.title?.map(t => t.plain_text).join('')?.trim() || '';
}

async function queryAll(db) {
  const results = [];
  let start_cursor;
  do {
    const body = { page_size: 100 };
    if (start_cursor) body.start_cursor = start_cursor;
    const res = await notion(`/databases/${db}/query`, { method: 'POST', body });
    results.push(...res.results);
    start_cursor = res.has_more ? res.next_cursor : null;
  } while (start_cursor);
  return results;
}

async function upsertByTitle(db, titleName, title, properties) {
  const rows = await queryAll(db);
  const existing = rows.find(p => plainTitle(p, titleName).toLowerCase() === title.toLowerCase());
  if (existing) {
    await notion(`/pages/${existing.id}`, { method: 'PATCH', body: { properties } });
    return { action: 'updated', id: existing.id, title };
  }
  const created = await notion('/pages', { method: 'POST', body: { parent: { database_id: db }, properties: { [titleName]: titleProp(title), ...properties } } });
  return { action: 'created', id: created.id, title };
}

const participants = [
  ['Endrit', 'Orga', '2026-05-17T14:11:00+02:00', '', 'Organisator; JA im Poll sichtbar.'],
  ['Mariam', 'Zugesagt', '2026-05-18T17:09:00+02:00', 'Juni schlecht; braucht exaktes Datum; 10.07 okay.', 'JA im Poll; schrieb: kommt aufs Datum an, Juni schlecht, 10.07 okay.'],
  ['Bachar', 'Zugesagt', '2026-05-18T16:01:00+02:00', '', 'JA im Poll sichtbar.'],
  ['Houda Fh', 'Zugesagt', '2026-05-18T15:59:00+02:00', '26.06 nicht; Juli okay.', 'JA im Poll; schrieb: 26.06 geht nicht, Juli okay.'],
  ['Burak Uni', 'Zugesagt', '2026-05-18T15:37:00+02:00', '', 'JA im Poll sichtbar.'],
  ['~JAMIL69', 'Zugesagt', '2026-05-17T16:20:00+02:00', '', 'JA im Poll sichtbar; angezeigte Nummer: +49 176 84238541.'],
  ['Mikail Caj', 'Zugesagt', '2026-05-17T14:59:00+02:00', '', 'JA im Poll sichtbar.'],
  ['Armin', 'Zugesagt', '2026-05-17T14:49:00+02:00', '', 'JA im Poll sichtbar.'],
  ['Björn Ironside', 'Zugesagt', '2026-05-17T14:26:00+02:00', '27. problematisch/nicht möglich laut vorherigem Stand.', 'JA im Poll sichtbar; fragte nach Optionen/Versorgung; bat alle zu voten, damit Endrit Termine anfragen kann.'],
  ['Nourhan✨', 'Zugesagt', '2026-05-17T14:20:00+02:00', '', 'JA im Poll sichtbar.'],
  ['Aya', 'Bedingt', null, '10.07 okay.', 'Schrieb: 10.07 für mich ok. In diesen 3 Screenshots nicht in der sichtbaren JA-Poll-Liste.'],
  ['Abdul Uni', 'Offen', null, 'Nähe Klausurenphase kritisch.', 'Schrieb: Das ist nah an der Klausurenphase.']
];

const changed = { participants: [], dates: [], tasks: [], logistics: [], comms: false };

for (const [name, status, date, unavailable, note] of participants) {
  changed.participants.push(await upsertByTitle(ids.databases.participants, 'Name', name, {
    Status: selectProp(status),
    'Zugesagt am': dateProp(date),
    'Nicht verfügbar': richProp(unavailable),
    'Auto?': selectProp('Unklar'),
    Notiz: richProp(note)
  }));
}

const dateRows = [
  ['26.06 / Juni-Termin', 'Problematisch', 'Houda kann am 26.06 nicht; Mariam sagt Juni ist schlecht.', 'Juni wirkt aktuell schwächer. Nur weiterverfolgen, wenn Gruppe es trotzdem trägt.', null],
  ['10.07', 'Möglich', 'Aya okay; Mariam okay; Houda sagt Juli ist okay.', 'Aktuell stärkster klar genannter Termin aus den neuen Screenshots.', null],
  ['Juli allgemein', 'Möglich', 'Houda: Juli okay; Mariam: Juni schlecht.', 'Juli priorisieren, genaue Wochenenden separat bestätigen.', null]
];
for (const [termin, status, conflicts, notes, yes] of dateRows) {
  changed.dates.push(await upsertByTitle(ids.databases.dates, 'Termin', termin, {
    Status: selectProp(status),
    Konflikte: richProp(conflicts),
    'Ja-Stimmen': numProp(yes)
  }));
}

const tasks = [
  ['JA-Liste aus Poll aktualisieren', 'Teilnehmer', 'Erledigt', 'Endrit/EOS', '10 sichtbare JA-Stimmen aus Poll eingetragen.'],
  ['Termin 10.07 gegen Gruppe prüfen', 'Kommunikation', 'Jetzt', 'Endrit', '10.07 ist für Aya und Mariam okay; Houda sagt Juli okay. Rest der Gruppe auf konkretes Datum abfragen.'],
  ['Versorgung/Optionen aus PDF klären', 'Logistik', 'Als Nächstes', 'Endrit', 'Björn fragte nach Optionen und Versorgung; diese Punkte in der nächsten Gruppeninfo sauber beantworten.'],
  ['Via Claudia / Claudia-Anfrage vorbereiten', 'Kommunikation', 'Als Nächstes', 'Endrit', 'Nächster Schritt laut Endrit: langsam anschreiben/anfragen, sobald Datum und Teilnehmerstand ausreichend klar sind.'],
  ['Autos/Fahrer und Sitzplätze abfragen', 'Transport', 'Als Nächstes', 'Gruppe', 'Nach dem Datum separat klären; entscheidend für Camping- und Budgetplanung.']
];
for (const [aufgabe, bereich, status, owner, note] of tasks) {
  changed.tasks.push(await upsertByTitle(ids.databases.tasks, 'Aufgabe', aufgabe, {
    Bereich: selectProp(bereich),
    Status: selectProp(status),
    Owner: richProp(owner),
    Notiz: richProp(note)
  }));
}

const logistics = [
  ['Versorgung / Essen klären', 'Equipment', 'Offen', 'Gruppe', 'Björn fragte, welche Optionen/Versorgung geplant sind; im PDF offenbar nicht klar genug.'],
  ['Datum 10.07 als Favorit prüfen', 'Camping', 'In Klärung', 'Endrit', 'Aktuell mehrere positive Signale für 10.07/Juli. Camping erst nach finalem Datum und Teilnehmerzahl anfragen.']
];
for (const [punkt, typ, status, owner, details] of logistics) {
  changed.logistics.push(await upsertByTitle(ids.databases.logistics, 'Punkt', punkt, {
    Typ: selectProp(typ),
    Status: selectProp(status),
    Owner: richProp(owner),
    Details: richProp(details)
  }));
}

await notion(`/blocks/${ids.pages.comms}/children`, {
  method: 'PATCH',
  body: { children: [
    h2('Update aus WhatsApp-Screenshots — 18.05.2026'),
    callout('✅', 'Poll: 10 sichtbare Stimmen bei „JA, ICH BIN FEST DABEI“.', 'green_background'),
    h3('Sichtbare JA-Stimmen'),
    bul('Endrit Murati — gestern 14:11'),
    bul('Mariam — heute 17:09; Juni schlecht, 10.07 okay, will genaues Datum wissen'),
    bul('Bachar — heute 16:01'),
    bul('Houda Fh — heute 15:59; 26.06 nicht, Juli okay'),
    bul('Burak Uni — heute 15:37'),
    bul('~JAMIL69 / +49 176 84238541 — gestern 16:20'),
    bul('Mikail Caj — gestern 14:59'),
    bul('Armin — gestern 14:49'),
    bul('Björn Ironside — gestern 14:26; fragte nach Optionen/Versorgung und pushte Abstimmung'),
    bul('Nourhan✨ — gestern 14:20'),
    h3('Weitere Rückmeldungen'),
    bul('Aya: 10.07 für mich ok.'),
    bul('Abdul Uni: Nähe zur Klausurenphase kritisch.'),
    h3('Operative Notiz'),
    bul('Juli/10.07 wirkt aktuell besser als 26.06/Juni.'),
    bul('Nächster sinnvoller Schritt: konkretes Datum bestätigen lassen und danach Anfrage an Via Claudia/Claudia vorbereiten.'),
    bul('Björn-Frage beantworten: Optionen/Versorgung klarer erklären.')
  ] }
});
changed.comms = true;

console.log(JSON.stringify({ ok: true, changed }, null, 2));

import fs from 'node:fs';

const token = fs.readFileSync('/data/.openclaw/secrets/notion.token', 'utf8').trim();
const version = '2022-06-28';

const ids = {
  main: '363986920e81805f8bdfd6c7c6708370',
  pages: {
    participants: '363986920e81814e9d3dc34d2ffb6b1d',
    planning: '363986920e8181a1b312ed4950c5eea2',
    logistics: '363986920e81814ba0cbc5e0dac2bd49',
    comms: '363986920e81815ea740e04ab5be5f35'
  },
  dbs: {
    participants: '363986920e8181f898f1de296c3720e2',
    dates: '363986920e81811aa545e500b199bdd0',
    tasks: '363986920e81817482c6eaed18539cd9',
    logistics: '363986920e8181c29af0d8e22b57d34a',
    budget: '363986920e8181caabe3d2c208b48e7e'
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

const rt = (content, href = null, annotations = {}) => [{ type: 'text', text: { content: String(content ?? '').slice(0, 1900), link: href ? { url: href } : null }, annotations }];
const h1 = s => ({ object: 'block', type: 'heading_1', heading_1: { rich_text: rt(s) } });
const h2 = s => ({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(s) } });
const h3 = s => ({ object: 'block', type: 'heading_3', heading_3: { rich_text: rt(s) } });
const p = s => ({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(s) } });
const bul = s => ({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(s) } });
const todo = (s, checked = false) => ({ object: 'block', type: 'to_do', to_do: { rich_text: rt(s), checked } });
const callout = (emoji, s, color = 'gray_background') => ({ object: 'block', type: 'callout', callout: { icon: { type: 'emoji', emoji }, rich_text: rt(s), color } });
const divider = () => ({ object: 'block', type: 'divider', divider: {} });
const linkToPage = page_id => ({ object: 'block', type: 'link_to_page', link_to_page: { type: 'page_id', page_id } });
const titleProp = s => ({ title: rt(s) });
const richProp = s => ({ rich_text: s ? rt(s) : [] });
const selectProp = s => ({ select: s ? { name: s } : null });
const numProp = n => ({ number: n === null || n === undefined ? null : n });
const dateProp = s => ({ date: s ? { start: s } : null });
const euroProp = n => ({ number: n === null || n === undefined ? null : n });

function textOf(block) {
  const value = block[block.type];
  const arr = Array.isArray(value?.rich_text) ? value.rich_text : [];
  return arr.map(t => t.plain_text).join('');
}

async function children(id) {
  const out = [];
  let cur;
  do {
    const qs = new URLSearchParams({ page_size: '100' });
    if (cur) qs.set('start_cursor', cur);
    const res = await notion(`/blocks/${id}/children?${qs.toString()}`);
    out.push(...res.results);
    cur = res.has_more ? res.next_cursor : null;
  } while (cur);
  return out;
}

async function archiveBlocks(blocks, predicate = () => true) {
  let archived = 0;
  for (const b of blocks) {
    if (!predicate(b)) continue;
    if (b.type === 'child_page' || b.type === 'child_database') continue;
    await notion(`/blocks/${b.id}`, { method: 'PATCH', body: { archived: true } });
    archived++;
  }
  return archived;
}

async function append(id, blocks) {
  for (let i = 0; i < blocks.length; i += 80) {
    await notion(`/blocks/${id}/children`, { method: 'PATCH', body: { children: blocks.slice(i, i + 80) } });
  }
}

async function queryAll(db) {
  const out = [];
  let cur;
  do {
    const body = { page_size: 100 };
    if (cur) body.start_cursor = cur;
    const res = await notion(`/databases/${db}/query`, { method: 'POST', body });
    out.push(...res.results);
    cur = res.has_more ? res.next_cursor : null;
  } while (cur);
  return out;
}

function plainTitle(page, prop) {
  return page.properties?.[prop]?.title?.map(t => t.plain_text).join('').trim() || '';
}

async function upsert(db, titleName, title, properties) {
  const rows = await queryAll(db);
  const existing = rows.find(p => plainTitle(p, titleName).toLowerCase() === title.toLowerCase());
  if (existing) {
    await notion(`/pages/${existing.id}`, { method: 'PATCH', body: { archived: false, properties } });
    return { action: 'updated', title, id: existing.id };
  }
  const created = await notion('/pages', { method: 'POST', body: { parent: { database_id: db }, properties: { [titleName]: titleProp(title), ...properties } } });
  return { action: 'created', title, id: created.id };
}

// Clean visible clutter. Keep child pages/databases only; remove old update logs, duplicated notes, and “archived blocks” notices.
const archived = { main: 0, comms: 0, participants: 0, planning: 0, logistics: 0 };
archived.main = await archiveBlocks(await children(ids.main));
archived.comms = await archiveBlocks(await children(ids.pages.comms));
archived.participants = await archiveBlocks(await children(ids.pages.participants));
archived.planning = await archiveBlocks(await children(ids.pages.planning));
archived.logistics = await archiveBlocks(await children(ids.pages.logistics));

await append(ids.main, [
  h1('Bayern Trip'),
  callout('🟡', 'Aktueller Status: Abstimmung ist durch. Anfrage an Via Claudia wurde gesendet. Wir warten jetzt auf die Antwort / Angebote für beide Juli-Termine.', 'yellow_background'),
  h2('Fester Stand'),
  bul('Teilnehmerplanung: 12 Personen'),
  bul('Anreise: aus Dortmund, voraussichtlich 3 Autos'),
  bul('Übernachtung: Zelte, einfache Lösung reicht — kein Komfort/Plus nötig, Standard/Zeltwiese bevorzugt'),
  bul('Termine angefragt: 03.07.–05.07.2026 und 10.07.–12.07.2026'),
  bul('Campingplatz: Via Claudia Camping, Lechbruck am See'),
  h2('Nächster Schritt'),
  todo('Antwort von Via Claudia abwarten', false),
  todo('Angebote vergleichen und Termin auswählen', false),
  todo('Danach Gruppe informieren und finale Zusagen/Autos/Zelte bestätigen', false),
  divider(),
  h2('Arbeitsbereiche'),
  linkToPage(ids.pages.participants),
  linkToPage(ids.pages.planning),
  linkToPage(ids.pages.logistics),
  linkToPage(ids.pages.comms)
]);

await append(ids.pages.comms, [
  callout('💬', 'Nur aktueller Kommunikationsstand — alte Update-Logs sind archiviert.', 'gray_background'),
  h2('Aktueller Status'),
  bul('Alle haben abgestimmt / der Planungsstand ist jetzt auf 12 Personen gesetzt.'),
  bul('Mail an Via Claudia Camping wurde am 19.05.2026 gesendet.'),
  bul('Wir warten auf Rückmeldung zu beiden Terminen und wählen danach den passenden Termin aus.'),
  h2('Angefragte Termine'),
  bul('03.07.2026 bis 05.07.2026 — Freitag Anreise, Sonntag Abreise'),
  bul('10.07.2026 bis 12.07.2026 — Freitag Anreise, Sonntag Abreise'),
  h2('Anfrage-Inhalt kurz'),
  bul('12 Personen, voraussichtlich 3 Autos, mehrere Zelte, Anreise aus Dortmund.'),
  bul('Gesucht: einfachste/günstigste sinnvolle Lösung, weil der Platz hauptsächlich zum Übernachten und für Sanitäranlagen genutzt wird.'),
  bul('Gefragt wurde nach Standardstellplätzen vs. Zeltwiese, Personen/Zelte pro Stellplatz, Autos pro Stellplatz, Zusatz-PKW, nebeneinander liegenden Plätzen und Gruppenregeln.'),
  h2('Sobald Antwort kommt'),
  todo('Angebot in Camping/Logistik eintragen', false),
  todo('Kosten pro Person berechnen', false),
  todo('Terminentscheidung vorbereiten', false)
]);

await append(ids.pages.participants, [
  callout('👥', 'Aktueller Arbeitsstand: 12 Personen eingeplant. Details/Fahrer/Zelte werden nach dem Camping-Angebot final bestätigt.', 'green_background')
]);

await append(ids.pages.planning, [
  callout('📋', 'Planungsstand: Abstimmung erledigt → Campinganfrage läuft → Termin nach Angebot auswählen.', 'blue_background')
]);

await append(ids.pages.logistics, [
  callout('⛺', 'Logistikstand: Via Claudia angefragt für 12 Personen, 3 Autos, 2 Nächte, einfache Stellplatz-/Zeltlösung.', 'brown_background')
]);

const changed = { dates: [], tasks: [], logistics: [], budget: [] };
for (const row of [
  ['03.07.–05.07.2026', 'Angefragt', 'Freitag bis Sonntag; 12 Personen, 3 Autos, mehrere Zelte; einfache Standard-/Zeltlösung bevorzugt.', 12],
  ['10.07.–12.07.2026', 'Angefragt', 'Freitag bis Sonntag; 12 Personen, 3 Autos, mehrere Zelte; einfache Standard-/Zeltlösung bevorzugt.', 12]
]) {
  changed.dates.push(await upsert(ids.dbs.dates, 'Termin', row[0], {
    Status: selectProp(row[1]),
    Konflikte: richProp(row[2]),
    'Ja-Stimmen': numProp(row[3])
  }));
}

for (const row of [
  ['Via Claudia Anfrage gesendet', 'Camping', 'Erledigt', 'EOS/Endrit', 'Gesendet am 19.05.2026 an anfrage@via-claudia-camping.de; Message-ID 19e3fdb20a4b1d59.'],
  ['Antwort von Via Claudia abwarten', 'Camping', 'Jetzt', 'Endrit/EOS', 'Warten auf Angebote/Einschätzung für 03.–05.07. und 10.–12.07. für 12 Personen, 3 Autos, mehrere Zelte.'],
  ['Termin nach Angebot auswählen', 'Kommunikation', 'Wartet', 'Endrit', 'Wenn beide Termine möglich sind, wählt Endrit den passenden Termin und gibt Via Claudia Bescheid.'],
  ['Finale Autos/Fahrer/Zelte bestätigen', 'Transport', 'Wartet', 'Gruppe', 'Nach Camping-Rückmeldung konkrete Fahrer, Sitzplätze, Zelte und Zusatz-PKW klären.']
]) {
  changed.tasks.push(await upsert(ids.dbs.tasks, 'Aufgabe', row[0], {
    Bereich: selectProp(row[1]),
    Status: selectProp(row[2]),
    Owner: richProp(row[3]),
    Notiz: richProp(row[4])
  }));
}

for (const row of [
  ['Via Claudia Anfrage — aktueller Status', 'Camping', 'In Klärung', 'Endrit/EOS', 'Anfrage gesendet: 12 Personen, 3 Autos, 2 Nächte, mehrere Zelte, Anreise aus Dortmund. Angefragt: 03.–05.07. und 10.–12.07.2026. Ziel: einfache/günstige Lösung, Standard/Zeltwiese, kein Komfort/Plus.'],
  ['Autos / Parken', 'Auto', 'In Klärung', 'Gruppe', 'Voraussichtlich 3 Autos. Angefragt: wie viele Autos pro Stellplatz, Zusatz-PKW/Separatparkplatz, Kosten und ob Autos ggf. auf weiteren Stellplätzen stehen können.'],
  ['Zelte / Stellplätze', 'Zelt', 'In Klärung', 'Gruppe', 'Mehrere Zelte. Angefragt: wie viele Personen/Zelte pro Standardstellplatz, ob mehrere Stellplätze nebeneinander möglich sind, und ob Zeltwiese sinnvoll/günstig ist.']
]) {
  changed.logistics.push(await upsert(ids.dbs.logistics, 'Punkt', row[0], {
    Typ: selectProp(row[1]),
    Status: selectProp(row[2]),
    Owner: richProp(row[3]),
    Details: richProp(row[4])
  }));
}

for (const row of [
  ['Camping Via Claudia', 'Camping', null, 'Angefragt'],
  ['Sprit/Parken', 'Transport', null, 'Schätzung'],
  ['Essen', 'Essen', null, 'Schätzung'],
  ['Reserve', 'Reserve', 20, 'Schätzung']
]) {
  changed.budget.push(await upsert(ids.dbs.budget, 'Posten', row[0], {
    Kategorie: selectProp(row[1]),
    'Schätzung p.P.': euroProp(row[2]),
    Status: selectProp(row[3])
  }));
}

console.log(JSON.stringify({ ok: true, archived, changed }, null, 2));

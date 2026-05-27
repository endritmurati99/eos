import fs from 'node:fs';

const token = fs.readFileSync('/data/.openclaw/secrets/notion.token', 'utf8').trim();
const parentPageId = process.env.NOTION_PARENT_PAGE_ID || '363986920e81805f8bdfd6c7c6708370';
const version = '2022-06-28';

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
  if (!res.ok) {
    throw new Error(`${method} ${path} failed: ${res.status} ${data.code || ''} ${data.message || text}`);
  }
  return data;
}

const rt = (content) => [{ type: 'text', text: { content } }];
const p = (content) => ({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(content) } });
const h1 = (content) => ({ object: 'block', type: 'heading_1', heading_1: { rich_text: rt(content) } });
const h2 = (content) => ({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(content) } });
const bul = (content) => ({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(content) } });
const todo = (content) => ({ object: 'block', type: 'to_do', to_do: { rich_text: rt(content), checked: false } });
const divider = () => ({ object: 'block', type: 'divider', divider: {} });

async function append(blocks) {
  for (let i = 0; i < blocks.length; i += 90) {
    await notion(`/blocks/${parentPageId}/children`, { method: 'PATCH', body: { children: blocks.slice(i, i + 90) } });
  }
}

async function createDatabase(title, properties) {
  return notion('/databases', {
    method: 'POST',
    body: {
      parent: { type: 'page_id', page_id: parentPageId },
      title: rt(title),
      properties
    }
  });
}

async function createPageInDb(database_id, properties) {
  return notion('/pages', { method: 'POST', body: { parent: { database_id }, properties } });
}

function titleProp(name) { return { title: rt(name) }; }
function richProp(text) { return { rich_text: text ? rt(text) : [] }; }
function selectProp(name) { return name ? { select: { name } } : { select: null }; }
function numberProp(n) { return n === undefined || n === null ? { number: null } : { number: n }; }
function checkboxProp(v) { return { checkbox: !!v }; }

console.log('Updating main page...');
await append([
  h1('Bayern Trip — Planungszentrale'),
  p('Phase: verbindliche Teilnehmerzahl und Terminverfügbarkeit klären. Ohne genaue Teilnehmerzahl kann der Campingplatz nicht sinnvoll angefragt oder gebucht werden.'),
  h2('Aktueller WhatsApp-Text'),
  p('Hey Leute, ich brauche jetzt bitte verbindlich die genaue Teilnehmeranzahl für den Bayern-Trip, damit ich den Campingplatz anfragen/buchen kann. Stimmt bitte im Poll ab, ob ihr grundsätzlich dabei seid. Falls ihr an bestimmten Terminen nicht könnt, schreibt das bitte kurz in die Gruppe, weil ich das im Poll nicht sauber abfragen kann. Wichtig: Es geht erstmal darum, wer wirklich dabei sein will — ohne genaue Anzahl kann ich nichts buchen. Bitte bis übermorgen 20:00 Uhr abstimmen.'),
  h2('Bekannte Infos aus den Screenshots'),
  bul('WhatsApp-Gruppe: Bayern_Trip'),
  bul('Gruppe laut Screenshot: ca. 13 Mitglieder'),
  bul('Deadline: übermorgen 20:00 Uhr'),
  bul('Björn Ironside kann am 27. nicht wegen ADAC-Kurventraining; sonst dabei.'),
  bul('Azika wäre dabei, falls der Termin 10.07.–12.07. wird.'),
  h2('Nächste Schritte'),
  todo('Poll bis Deadline beobachten'),
  todo('Verbindliche Ja-Liste erstellen'),
  todo('Termin mit den wenigsten Konflikten auswählen'),
  todo('Campingplätze shortlist erstellen und 2 Nächte prüfen'),
  todo('Autos/Fahrer und Sitzplätze klären'),
  todo('Budgetrahmen bestätigen und ggf. Anzahlung einsammeln'),
  divider(),
  p('Die folgenden Datenbanken wurden automatisch angelegt und vorbefüllt.')
]);

console.log('Creating databases...');
const participants = await createDatabase('Teilnehmer / RSVP', {
  Name: { title: {} },
  Status: { select: { options: [
    { name: 'Organizer', color: 'blue' }, { name: 'Yes', color: 'green' }, { name: 'No', color: 'red' },
    { name: 'Maybe', color: 'yellow' }, { name: 'Conditional', color: 'orange' }, { name: 'Unknown', color: 'gray' }
  ] } },
  'Kann mit?': { select: { options: [ { name: 'Ja', color: 'green' }, { name: 'Nein', color: 'red' }, { name: 'Vielleicht', color: 'yellow' }, { name: 'Unbekannt', color: 'gray' } ] } },
  'Nicht verfügbar': { rich_text: {} },
  'Auto/Fahrer': { select: { options: [ { name: 'Fahrer', color: 'blue' }, { name: 'Mitfahrer', color: 'green' }, { name: 'Kein Auto', color: 'red' }, { name: 'Unbekannt', color: 'gray' } ] } },
  'Camping verbindlich': { checkbox: {} },
  'Anzahlung bezahlt': { checkbox: {} },
  Notizen: { rich_text: {} }
});

const dates = await createDatabase('Terminoptionen / Konflikte', {
  Termin: { title: {} },
  Status: { select: { options: [ { name: 'Favorit', color: 'green' }, { name: 'Möglich', color: 'blue' }, { name: 'Problematisch', color: 'orange' }, { name: 'Ausgeschlossen', color: 'red' } ] } },
  'Ja-Stimmen': { number: { format: 'number' } },
  Konflikte: { rich_text: {} },
  Notizen: { rich_text: {} }
});

const camping = await createDatabase('Camping / Unterkunft', {
  Campingplatz: { title: {} },
  Ort: { rich_text: {} },
  Link: { url: {} },
  Status: { select: { options: [ { name: 'Shortlist', color: 'blue' }, { name: 'Angefragt', color: 'yellow' }, { name: 'Verfügbar', color: 'green' }, { name: 'Voll', color: 'red' }, { name: 'Zu teuer', color: 'orange' } ] } },
  'Min. Nächte': { rich_text: {} },
  Kapazität: { rich_text: {} },
  'Preis p.P.': { number: { format: 'euro' } },
  Notizen: { rich_text: {} }
});

const cars = await createDatabase('Autos / Fahrer', {
  Auto: { title: {} },
  Fahrer: { rich_text: {} },
  'Sitzplätze frei': { number: { format: 'number' } },
  Abfahrtsort: { rich_text: {} },
  Mitfahrer: { rich_text: {} },
  Notizen: { rich_text: {} }
});

const tasks = await createDatabase('Aufgaben', {
  Aufgabe: { title: {} },
  Status: { select: { options: [ { name: 'Offen', color: 'gray' }, { name: 'In Arbeit', color: 'yellow' }, { name: 'Blockiert', color: 'red' }, { name: 'Erledigt', color: 'green' } ] } },
  Owner: { rich_text: {} },
  Priorität: { select: { options: [ { name: 'Hoch', color: 'red' }, { name: 'Mittel', color: 'yellow' }, { name: 'Niedrig', color: 'gray' } ] } },
  Notizen: { rich_text: {} }
});

const packing = await createDatabase('Packliste / Gruppenequipment', {
  Item: { title: {} },
  Kategorie: { select: { options: [ { name: 'Schlafen', color: 'blue' }, { name: 'Kochen', color: 'orange' }, { name: 'Kleidung', color: 'green' }, { name: 'Dokumente', color: 'purple' }, { name: 'Gruppe', color: 'yellow' }, { name: 'Auto', color: 'gray' } ] } },
  'Wer bringt es?': { rich_text: {} },
  Pflicht: { checkbox: {} },
  Status: { select: { options: [ { name: 'Offen', color: 'gray' }, { name: 'Organisiert', color: 'yellow' }, { name: 'Eingepackt', color: 'green' } ] } }
});

const budget = await createDatabase('Budget', {
  Posten: { title: {} },
  Kategorie: { select: { options: [ { name: 'Camping', color: 'green' }, { name: 'Transport', color: 'blue' }, { name: 'Essen', color: 'orange' }, { name: 'Aktivität', color: 'purple' }, { name: 'Reserve', color: 'gray' } ] } },
  'Schätzung p.P.': { number: { format: 'euro' } },
  Status: { select: { options: [ { name: 'Schätzung', color: 'gray' }, { name: 'Bestätigt', color: 'green' }, { name: 'Offen', color: 'yellow' } ] } },
  Notizen: { rich_text: {} }
});

console.log('Filling rows...');
const people = [
  ['Endrit / Du', 'Organizer', 'Ja', '', 'Unbekannt', true, false, 'Organisator; Poll und Camping-Anfrage'],
  ['Abdul Uni', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Armin', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Aya', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Bachar', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Björn Ironside', 'Conditional', 'Ja', '27.', 'Unbekannt', false, false, 'Kann am 27. nicht wegen ADAC-Kurventraining; sonst dabei'],
  ['Burak Uni', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Houda Fh', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Mariam', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Mikail Caj', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Nourhan✨', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['~JAMIL69', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['+49 1575 2446826', 'Unknown', 'Unbekannt', '', 'Unbekannt', false, false, 'sichtbar in Gruppe'],
  ['Azika', 'Conditional', 'Ja', 'nur bestätigt für 10.07.–12.07.', 'Unbekannt', false, false, 'Falls Termin 10.07.–12.07., wäre Azika auch dabei']
];
for (const [name, status, can, unavailable, car, commit, paid, notes] of people) {
  await createPageInDb(participants.id, {
    Name: titleProp(name), Status: selectProp(status), 'Kann mit?': selectProp(can), 'Nicht verfügbar': richProp(unavailable),
    'Auto/Fahrer': selectProp(car), 'Camping verbindlich': checkboxProp(commit), 'Anzahlung bezahlt': checkboxProp(paid), Notizen: richProp(notes)
  });
}

for (const row of [
  ['10.07.–12.07.', 'Möglich', 0, '', 'Azika wäre bei diesem Termin dabei.'],
  ['27. / Wochenende mit 27.', 'Problematisch', 0, 'Björn kann am 27. nicht.', 'Nur wählen, wenn Björns Ausfall okay ist.'],
  ['Weiterer Termin aus Poll', 'Möglich', 0, '', 'Nach Poll ergänzen.']
]) {
  await createPageInDb(dates.id, { Termin: titleProp(row[0]), Status: selectProp(row[1]), 'Ja-Stimmen': numberProp(row[2]), Konflikte: richProp(row[3]), Notizen: richProp(row[4]) });
}

for (const row of [
  ['Campingplatz 1', 'Füssen / Schwangau / Allgäu', null, 'Shortlist', '2 Nächte prüfen', '6–10 Personen', null, 'Offizieller Campingplatz, kein Wildcamping.'],
  ['Campingplatz 2', 'Füssen / Schwangau / Allgäu', null, 'Shortlist', '2 Nächte prüfen', '6–10 Personen', null, 'Anfrage erst nach Teilnehmerzahl/Termin.'],
  ['Campingplatz 3', 'Füssen / Schwangau / Allgäu', null, 'Shortlist', '2 Nächte prüfen', '6–10 Personen', null, 'High-season Mindestnächte beachten.']
]) {
  await createPageInDb(camping.id, { Campingplatz: titleProp(row[0]), Ort: richProp(row[1]), Link: { url: row[2] }, Status: selectProp(row[3]), 'Min. Nächte': richProp(row[4]), Kapazität: richProp(row[5]), 'Preis p.P.': numberProp(row[6]), Notizen: richProp(row[7]) });
}

for (const row of [
  ['Auto 1', '', null, 'Dortmund', '', 'Fahrer noch klären'],
  ['Auto 2', '', null, 'Dortmund', '', 'Fahrer noch klären'],
  ['Auto 3', '', null, 'Dortmund', '', 'Optional bei 8–10 Personen']
]) {
  await createPageInDb(cars.id, { Auto: titleProp(row[0]), Fahrer: richProp(row[1]), 'Sitzplätze frei': numberProp(row[2]), Abfahrtsort: richProp(row[3]), Mitfahrer: richProp(row[4]), Notizen: richProp(row[5]) });
}

for (const row of [
  ['Poll bis Deadline beobachten', 'Offen', 'Endrit', 'Hoch', 'Bis übermorgen 20:00 Uhr'],
  ['Verbindliche Ja-Liste erstellen', 'Offen', 'Endrit', 'Hoch', 'Nur mit Ja-Stimmen weiterplanen'],
  ['Termin festlegen', 'Offen', 'Endrit', 'Hoch', 'Konflikte aus WhatsApp berücksichtigen'],
  ['Campingplätze shortlist erstellen', 'Offen', 'Endrit', 'Hoch', '2 Nächte in High Season prüfen'],
  ['Autos/Fahrer klären', 'Offen', 'Gruppe', 'Mittel', '2–3 private Autos aus Dortmund'],
  ['Budget bestätigen', 'Offen', 'Endrit', 'Mittel', 'Realistisch 160–180 € p.P. kommunizieren']
]) {
  await createPageInDb(tasks.id, { Aufgabe: titleProp(row[0]), Status: selectProp(row[1]), Owner: richProp(row[2]), Priorität: selectProp(row[3]), Notizen: richProp(row[4]) });
}

for (const row of [
  ['Zelt(e)', 'Schlafen', '', true, 'Offen'],
  ['Schlafsack', 'Schlafen', 'jede Person selbst', true, 'Offen'],
  ['Isomatte', 'Schlafen', 'jede Person selbst', true, 'Offen'],
  ['Campingkocher', 'Kochen', '', false, 'Offen'],
  ['Müllbeutel', 'Gruppe', '', true, 'Offen'],
  ['Powerbank', 'Gruppe', '', false, 'Offen'],
  ['Führerschein/Fahrzeugpapiere', 'Auto', 'Fahrer', true, 'Offen']
]) {
  await createPageInDb(packing.id, { Item: titleProp(row[0]), Kategorie: selectProp(row[1]), 'Wer bringt es?': richProp(row[2]), Pflicht: checkboxProp(row[3]), Status: selectProp(row[4]) });
}

for (const row of [
  ['Camping', 'Camping', 60, 'Schätzung', 'abhängig von Platz und Mindestnächten'],
  ['Sprit / Auto', 'Transport', 45, 'Schätzung', '2–3 Autos aus Dortmund'],
  ['Essen', 'Essen', 40, 'Schätzung', 'Gruppeneinkauf + Snacks'],
  ['Aktivitäten / Parken', 'Aktivität', 25, 'Schätzung', 'Neuschwanstein/Allgäu-Kontext'],
  ['Reserve', 'Reserve', 20, 'Schätzung', 'Puffer'],
]) {
  await createPageInDb(budget.id, { Posten: titleProp(row[0]), Kategorie: selectProp(row[1]), 'Schätzung p.P.': numberProp(row[2]), Status: selectProp(row[3]), Notizen: richProp(row[4]) });
}

console.log(JSON.stringify({
  ok: true,
  parentPageId,
  databases: {
    participants: participants.url,
    dates: dates.url,
    camping: camping.url,
    cars: cars.url,
    tasks: tasks.url,
    packing: packing.url,
    budget: budget.url
  }
}, null, 2));

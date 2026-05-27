import fs from 'node:fs';

const token = fs.readFileSync('/data/.openclaw/secrets/notion.token', 'utf8').trim();
const parentPageId = '363986920e81805f8bdfd6c7c6708370';
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
  if (!res.ok) throw new Error(`${method} ${path} failed: ${res.status} ${data.code || ''} ${data.message || text}`);
  return data;
}

const rt = (content, href = null, annotations = {}) => [{ type: 'text', text: { content, link: href ? { url: href } : null }, annotations }];
const h1 = (content) => ({ object: 'block', type: 'heading_1', heading_1: { rich_text: rt(content) } });
const h2 = (content) => ({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(content) } });
const h3 = (content) => ({ object: 'block', type: 'heading_3', heading_3: { rich_text: rt(content) } });
const p = (content) => ({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(content) } });
const paraLink = (label, url) => ({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(label, url) } });
const bul = (content) => ({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(content) } });
const todo = (content, checked = false) => ({ object: 'block', type: 'to_do', to_do: { rich_text: rt(content), checked } });
const divider = () => ({ object: 'block', type: 'divider', divider: {} });
const callout = (emoji, content, color = 'gray_background') => ({ object: 'block', type: 'callout', callout: { icon: { type: 'emoji', emoji }, rich_text: rt(content), color } });
const quote = (content) => ({ object: 'block', type: 'quote', quote: { rich_text: rt(content) } });
const linkToPage = (page_id) => ({ object: 'block', type: 'link_to_page', link_to_page: { type: 'page_id', page_id } });
const linkToDb = (database_id) => ({ object: 'block', type: 'link_to_page', link_to_page: { type: 'database_id', database_id } });
const bookmark = (url, caption = '') => ({ object: 'block', type: 'bookmark', bookmark: { url, caption: caption ? rt(caption) : [] } });

const titleProp = (s) => ({ title: rt(s) });
const richProp = (s) => ({ rich_text: s ? rt(s) : [] });
const selectProp = (s) => ({ select: s ? { name: s } : null });
const numProp = (n) => ({ number: n === null || n === undefined ? null : n });
const cbProp = (v) => ({ checkbox: !!v });
const dateProp = (start) => ({ date: start ? { start } : null });

async function append(blockId, blocks) {
  for (let i = 0; i < blocks.length; i += 80) {
    await notion(`/blocks/${blockId}/children`, { method: 'PATCH', body: { children: blocks.slice(i, i + 80) } });
  }
}

async function clearChildren(blockId) {
  let cursor;
  let archived = 0;
  do {
    const qs = new URLSearchParams({ page_size: '100' });
    if (cursor) qs.set('start_cursor', cursor);
    const res = await notion(`/blocks/${blockId}/children?${qs.toString()}`);
    for (const block of res.results) {
      try {
        if (block.type === 'child_page') {
          await notion(`/pages/${block.id}`, { method: 'PATCH', body: { archived: true } });
        } else if (block.type === 'child_database') {
          await notion(`/databases/${block.id}`, { method: 'PATCH', body: { archived: true } });
        } else {
          await notion(`/blocks/${block.id}`, { method: 'PATCH', body: { archived: true } });
        }
        archived++;
      } catch (error) {
        // Keep going: if Notion refuses to archive a specific child type, the rebuild should still create a clean top dashboard.
        console.error('ARCHIVE_SKIP', block.type, block.id, String(error.message).slice(0, 180));
      }
    }
    cursor = res.has_more ? res.next_cursor : null;
  } while (cursor);
  return archived;
}

async function createPage(parentId, title, emoji, children = [], coverUrl = null) {
  const body = {
    parent: { page_id: parentId },
    icon: { type: 'emoji', emoji },
    properties: { title: { title: rt(title) } },
    children
  };
  if (coverUrl) body.cover = { type: 'external', external: { url: coverUrl } };
  return notion('/pages', { method: 'POST', body });
}

async function createDatabase(parentId, title, properties) {
  return notion('/databases', {
    method: 'POST',
    body: { parent: { type: 'page_id', page_id: parentId }, title: rt(title), is_inline: true, properties }
  });
}

async function addRow(database_id, properties) {
  return notion('/pages', { method: 'POST', body: { parent: { database_id }, properties } });
}

function navColumns(pages) {
  return {
    object: 'block',
    type: 'column_list',
    column_list: {
      children: [
        {
          object: 'block', type: 'column', column: { children: [
            callout('🧭', 'Navigation', 'gray_background'),
            linkToPage(pages.participants.id),
            linkToPage(pages.planning.id),
            linkToPage(pages.logistics.id),
            linkToPage(pages.budget.id),
            linkToPage(pages.route.id),
            linkToPage(pages.comms.id),
            divider(),
            callout('📌', 'Regel: erst Zusagen + Termin, dann Camping buchen.', 'blue_background')
          ] }
        },
        {
          object: 'block', type: 'column', column: { children: [
            callout('🏔️', 'AKTUELLE PHASE: PLANUNG — verbindliche Teilnehmerzahl und Termin klären.', 'blue_background'),
            callout('⏰', 'Deadline: übermorgen 20:00 Uhr. Danach nur mit Ja-Stimmen weiterplanen.', 'yellow_background'),
            callout('⚠️', 'Blocker: Autos/Fahrer und Zelte sind noch nicht final.', 'red_background'),
            h2('Heute wichtig'),
            todo('Offene Personen aktiv nachziehen'),
            todo('Absagen/Termin-Konflikte sauber in Teilnehmer eintragen'),
            todo('Fahrer + Zelte separat abfragen')
          ] }
        }
      ]
    }
  };
}

console.log('Clean old dashboard blocks...');
await notion(`/pages/${parentPageId}`, {
  method: 'PATCH',
  body: {
    icon: { type: 'emoji', emoji: '🏔️' },
    cover: { type: 'external', external: { url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1800&q=80' } },
    properties: { title: { title: rt('Bayern Trip') } }
  }
});
const archived = await clearChildren(parentPageId);

console.log('Create clean section pages...');
const planning = await createPage(parentPageId, 'Planung', '📋', [
  callout('📋', 'Terminentscheidung und nächste Schritte. Teilnehmer haben jetzt einen eigenen Reiter.', 'blue_background'),
  h2('Arbeitslogik'),
  bul('Erst Teilnehmer verbindlich klären.'),
  bul('Dann Termin wählen.'),
  bul('Danach Camping, Autos und Budget finalisieren.')
]);
const participantsPage = await createPage(parentPageId, 'Teilnehmer', '👥', [
  callout('👥', 'Zentrale Teilnehmerliste: zugesagt, bedingt, offen. Die Liste steht direkt auf dieser Seite — kein extra Datenbank-Klick nötig.', 'green_background'),
  h2('Aktueller Stand'),
  bul('7 feste Zusagen inkl. Endrit'),
  bul('1 bedingt: Azika bei 10.07.–12.07.'),
  bul('5 offen'),
  callout('📅', 'Poll-Zeiten werden als echtes Datum gespeichert, nicht als Text wie „heute“.', 'blue_background')
]);
const logistics = await createPage(parentPageId, 'Logistik', '⛺', [
  callout('⛺', 'Camping, Autos und Gruppenequipment gehören zusammen. Das ist der operative Engpass.', 'brown_background'),
  h2('Engpässe'),
  todo('Fahrer sicher bestätigen'),
  todo('Zelte/Schlafplätze bestätigen'),
  todo('Campingplatz mit 2 Nächten finden')
]);
const budgetPage = await createPage(parentPageId, 'Budget', '💶', [
  callout('💶', 'Arbeite erstmal mit 160–180 € p.P. als realistische Erwartung, bis Camping und Transport bestätigt sind.', 'yellow_background')
]);
const route = await createPage(parentPageId, 'Route & Ideen', '🧭', [
  callout('🧭', 'Ideenspeicher für Füssen, Allgäu, Neuschwanstein und Via Claudia. Erst planen, dann überladen.', 'purple_background'),
  bookmark('https://www.allgaeu.de/touren/radfernroute-via-claudia-augusta-etappe-rosshaupten-fuessen', 'Via Claudia Augusta: Roßhaupten – Füssen'),
  bookmark('https://www.fuessen.de/kultur/ferienstrassen/', 'Füssen: Ferienstraßen und Lage')
]);
const comms = await createPage(parentPageId, 'WhatsApp & Notizen', '💬', [
  callout('💬', 'Hier kommen Texte, Gruppeninfos und Entscheidungen hin — nicht auf das Dashboard.', 'gray_background'),
  h2('Aktueller Gruppen-Text'),
  h2('Poll-Ergebnis'),
  bul('7 feste Zusagen: Du, ~JAMIL69, Mikail Caj, Aya, Armin, Björn Ironside, Nourhan ✨'),
  bul('Noch offen: Abdul, Bachar, Burak, Houda, Mariam'),
  bul('Bedingt: Azika bei 10.07.–12.07.'),
  h2('Aktueller Gruppen-Text'),
  quote('Hey Leute, ich brauche jetzt bitte verbindlich die genaue Teilnehmeranzahl für den Bayern-Trip, damit ich den Campingplatz anfragen/buchen kann. Stimmt bitte im Poll ab, ob ihr grundsätzlich dabei seid. Falls ihr an bestimmten Terminen nicht könnt, schreibt das bitte kurz in die Gruppe, weil ich das im Poll nicht sauber abfragen kann. Wichtig: Es geht erstmal darum, wer wirklich dabei sein will — ohne genaue Anzahl kann ich nichts buchen. Bitte bis übermorgen 20:00 Uhr abstimmen.'),
  h2('Screenshot-Infos'),
  bul('WhatsApp-Gruppe: Bayern_Trip'),
  bul('ca. 13 Mitglieder sichtbar'),
  bul('Poll JA / fest dabei: Du, ~JAMIL69, Mikail Caj, Aya, Armin, Björn Ironside, Nourhan ✨'),
  bul('Björn: fest dabei, aber kann am 27. nicht.'),
  bul('Azika: dabei, falls 10.07.–12.07.')
]);
const pages = { participants: participantsPage, planning, logistics, budget: budgetPage, route, comms };

console.log('Create clean databases inside section pages...');
const participantsDb = await createDatabase(participantsPage.id, 'Teilnehmerliste', {
  Name: { title: {} },
  Status: { select: { options: [
    { name: 'Zugesagt', color: 'green' }, { name: 'Bedingt', color: 'orange' },
    { name: 'Offen', color: 'gray' }, { name: 'Abgesagt', color: 'red' }, { name: 'Orga', color: 'blue' }
  ] } },
  'Zugesagt am': { date: {} },
  'Nicht verfügbar': { rich_text: {} },
  'Auto?': { select: { options: [ { name: 'Fahrer', color: 'blue' }, { name: 'Mitfahrer', color: 'green' }, { name: 'Unklar', color: 'gray' } ] } },
  'Zelt/Equipment': { rich_text: {} },
  Notiz: { rich_text: {} }
});
const datesDb = await createDatabase(planning.id, 'Termine', {
  Termin: { title: {} }, Status: { select: { options: [ { name: 'Favorit', color: 'green' }, { name: 'Möglich', color: 'blue' }, { name: 'Problematisch', color: 'orange' } ] } },
  Konflikte: { rich_text: {} }, 'Ja-Stimmen': { number: { format: 'number' } }
});
const tasksDb = await createDatabase(planning.id, 'Nächste Schritte', {
  Aufgabe: { title: {} }, Bereich: { select: { options: [ { name: 'Teilnehmer', color: 'blue' }, { name: 'Camping', color: 'brown' }, { name: 'Transport', color: 'green' }, { name: 'Budget', color: 'yellow' }, { name: 'Kommunikation', color: 'gray' } ] } },
  Status: { select: { options: [ { name: 'Jetzt', color: 'red' }, { name: 'Als Nächstes', color: 'yellow' }, { name: 'Wartet', color: 'gray' }, { name: 'Erledigt', color: 'green' } ] } },
  Owner: { rich_text: {} }, Notiz: { rich_text: {} }
});
const logisticsDb = await createDatabase(logistics.id, 'Logistik Board', {
  Punkt: { title: {} }, Typ: { select: { options: [ { name: 'Camping', color: 'brown' }, { name: 'Auto', color: 'blue' }, { name: 'Zelt', color: 'green' }, { name: 'Equipment', color: 'yellow' } ] } },
  Status: { select: { options: [ { name: 'Offen', color: 'gray' }, { name: 'In Klärung', color: 'yellow' }, { name: 'Bestätigt', color: 'green' }, { name: 'Problem', color: 'red' } ] } },
  Owner: { rich_text: {} }, Details: { rich_text: {} }
});
const budgetDb = await createDatabase(budgetPage.id, 'Budget', {
  Posten: { title: {} }, Kategorie: { select: { options: [ { name: 'Camping', color: 'brown' }, { name: 'Transport', color: 'blue' }, { name: 'Essen', color: 'orange' }, { name: 'Aktivität', color: 'purple' }, { name: 'Reserve', color: 'gray' } ] } },
  'Schätzung p.P.': { number: { format: 'euro' } }, Status: { select: { options: [ { name: 'Schätzung', color: 'gray' }, { name: 'Bestätigt', color: 'green' } ] } }
});

console.log('Fill clean databases...');
const people = [
  ['Endrit', 'Orga', '2026-05-17T14:11:00+02:00', '', 'Unklar', 'Poll-Zusage aus Screenshot'],
  ['Abdul Uni', 'Offen', null, '', 'Unklar', ''],
  ['Armin', 'Zugesagt', '2026-05-17T14:49:00+02:00', '', 'Unklar', 'Poll-Zusage aus Screenshot'],
  ['Aya', 'Zugesagt', '2026-05-17T15:32:00+02:00', '', 'Unklar', 'Poll-Zusage aus Screenshot'],
  ['Bachar', 'Offen', null, '', 'Unklar', ''],
  ['Björn Ironside', 'Zugesagt', '2026-05-17T14:26:00+02:00', '27.', 'Unklar', 'Kann am 27. nicht wegen ADAC-Kurventraining'],
  ['Burak Uni', 'Offen', null, '', 'Unklar', ''],
  ['Houda Fh', 'Offen', null, '', 'Unklar', ''],
  ['Mariam', 'Offen', null, '', 'Unklar', ''],
  ['Mikail Caj', 'Zugesagt', '2026-05-17T14:59:00+02:00', '', 'Unklar', 'Poll-Zusage aus Screenshot'],
  ['Nourhan✨', 'Zugesagt', '2026-05-17T14:20:00+02:00', '', 'Unklar', 'Poll-Zusage aus Screenshot'],
  ['~JAMIL69', 'Zugesagt', '2026-05-17T16:20:00+02:00', '', 'Unklar', 'Poll-Zusage aus Screenshot'],
  ['Azika', 'Bedingt', null, 'nur 10.07.–12.07. bekannt', 'Unklar', 'Wäre bei 10.07.–12.07. dabei']
];
for (const [name, status, acceptedAt, unavailable, car, note] of people) await addRow(participantsDb.id, { Name: titleProp(name), Status: selectProp(status), 'Zugesagt am': dateProp(acceptedAt), 'Nicht verfügbar': richProp(unavailable), 'Auto?': selectProp(car), 'Zelt/Equipment': richProp(''), Notiz: richProp(note) });
for (const row of [['10.07.–12.07.', 'Möglich', 'Azika wäre dabei', 0], ['Wochenende mit 27.', 'Problematisch', 'Björn kann nicht', 0], ['Weiterer Poll-Termin', 'Möglich', 'nach Poll ergänzen', 0]]) await addRow(datesDb.id, { Termin: titleProp(row[0]), Status: selectProp(row[1]), Konflikte: richProp(row[2]), 'Ja-Stimmen': numProp(row[3]) });
for (const row of [
  ['Poll-Ergebnis übertragen', 'Teilnehmer', 'Erledigt', 'Endrit', '7 feste Zusagen aus Screenshot übernommen'],
  ['Offene Personen nachziehen', 'Kommunikation', 'Jetzt', 'Endrit', 'Nur echte Zusagen zählen'],
  ['Fahrer-Abfrage posten', 'Transport', 'Als Nächstes', 'Endrit', 'Wer fährt sicher? Wie viele Plätze?'],
  ['Zelt-Abfrage posten', 'Camping', 'Als Nächstes', 'Endrit', 'Wer hat Zelt/Schlafplätze?'],
  ['Campingplätze anfragen', 'Camping', 'Wartet', 'Endrit', 'erst nach Teilnehmerzahl + Termin']
]) await addRow(tasksDb.id, { Aufgabe: titleProp(row[0]), Bereich: selectProp(row[1]), Status: selectProp(row[2]), Owner: richProp(row[3]), Notiz: richProp(row[4]) });
for (const row of [
  ['Campingplatz finden', 'Camping', 'Offen', 'Endrit', 'Füssen/Schwangau/Allgäu, 2 Nächte prüfen'],
  ['Auto 1', 'Auto', 'Offen', '', 'Fahrer + Sitzplätze offen'],
  ['Auto 2', 'Auto', 'Offen', '', 'Fahrer + Sitzplätze offen'],
  ['Zeltplätze', 'Zelt', 'Offen', '', 'Wie viele Zelte/Personen pro Zelt?'],
  ['Erste-Hilfe / Müll / Powerbank', 'Equipment', 'Offen', '', 'Gruppensachen bündeln']
]) await addRow(logisticsDb.id, { Punkt: titleProp(row[0]), Typ: selectProp(row[1]), Status: selectProp(row[2]), Owner: richProp(row[3]), Details: richProp(row[4]) });
for (const row of [['Camping', 'Camping', 60, 'Schätzung'], ['Sprit/Parken', 'Transport', 45, 'Schätzung'], ['Essen', 'Essen', 40, 'Schätzung'], ['Aktivitäten', 'Aktivität', 25, 'Schätzung'], ['Reserve', 'Reserve', 20, 'Schätzung']]) await addRow(budgetDb.id, { Posten: titleProp(row[0]), Kategorie: selectProp(row[1]), 'Schätzung p.P.': numProp(row[2]), Status: selectProp(row[3]) });

console.log('Append clean main dashboard...');
await append(parentPageId, [
  h1('Bayern Trip'),
  p('Cleanes Planungsdashboard für Teilnehmer, Termin, Camping, Autos, Budget und Kommunikation.'),
  navColumns(pages),
  divider(),
  h2('Statuskarten'),
  {
    object: 'block', type: 'column_list', column_list: { children: [
      { object: 'block', type: 'column', column: { children: [callout('📍', 'Phase: Planung', 'blue_background'), p('Noch keine Buchung. Erst Teilnehmer + Termin finalisieren.')] } },
      { object: 'block', type: 'column', column: { children: [callout('👥', 'Teilnehmer: 7 feste Zusagen', 'green_background'), p('7 fest dabei inkl. Endrit; 1 bedingt; 5 noch offen.')] } },
      { object: 'block', type: 'column', column: { children: [callout('⛺', 'Camping: wartet', 'yellow_background'), p('Anfrage erst mit genauer Anzahl und Zelt-/Autolage.')] } }
    ] }
  },
  h2('Arbeitsbereiche'),
  {
    object: 'block', type: 'column_list', column_list: { children: [
      { object: 'block', type: 'column', column: { children: [h3('Teilnehmer & Planung'), linkToPage(participantsPage.id), linkToPage(planning.id)] } },
      { object: 'block', type: 'column', column: { children: [h3('Logistik'), linkToPage(logistics.id)] } },
      { object: 'block', type: 'column', column: { children: [h3('Budget & Ideen'), linkToPage(budgetPage.id), linkToPage(route.id), linkToPage(comms.id)] } }
    ] }
  },
  divider(),
  callout('🧹', `Aufgeräumt: ${archived} alte Blöcke/duplizierte Inhalte wurden archiviert.`, 'gray_background')
]);

const output = {
  ok: true,
  archivedOldBlocks: archived,
  main: 'https://www.notion.so/Bayern-Trip-363986920e81805f8bdfd6c7c6708370',
  pages: { participants: participantsPage.url, planning: planning.url, logistics: logistics.url, budget: budgetPage.url, route: route.url, comms: comms.url },
  databases: { participants: participantsDb.url, dates: datesDb.url, tasks: tasksDb.url, logistics: logisticsDb.url, budget: budgetDb.url }
};
fs.writeFileSync('data/bayern_trip/clean_rebuild_result.json', JSON.stringify(output, null, 2));
console.log(JSON.stringify(output, null, 2));

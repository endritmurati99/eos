import fs from 'node:fs';

const token = fs.readFileSync('/data/.openclaw/secrets/notion.token', 'utf8').trim();
const parentPageId = '363986920e81805f8bdfd6c7c6708370';
const version = '2022-06-28';
const resultText = fs.readFileSync('data/bayern_trip/notion_setup_result.json', 'utf8');
const setup = JSON.parse(resultText.slice(resultText.indexOf('{')));

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

const rt = (content, href) => [{ type: 'text', text: { content, link: href ? { url: href } : null } }];
const h1 = (content) => ({ object: 'block', type: 'heading_1', heading_1: { rich_text: rt(content), color: 'default' } });
const h2 = (content) => ({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(content), color: 'default' } });
const h3 = (content) => ({ object: 'block', type: 'heading_3', heading_3: { rich_text: rt(content), color: 'default' } });
const p = (content) => ({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(content) } });
const bul = (content) => ({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(content) } });
const todo = (content, checked = false) => ({ object: 'block', type: 'to_do', to_do: { rich_text: rt(content), checked } });
const divider = () => ({ object: 'block', type: 'divider', divider: {} });
const callout = (emoji, content, color = 'gray_background') => ({ object: 'block', type: 'callout', callout: { icon: { type: 'emoji', emoji }, rich_text: rt(content), color } });
const bookmark = (url, caption = '') => ({ object: 'block', type: 'bookmark', bookmark: { url, caption: caption ? rt(caption) : [] } });
const linkToPage = (page_id) => ({ object: 'block', type: 'link_to_page', link_to_page: { type: 'page_id', page_id } });
const linkToDb = (database_id) => ({ object: 'block', type: 'link_to_page', link_to_page: { type: 'database_id', database_id } });

function idFromUrl(url) {
  const raw = url.split('/').pop().split('?')[0];
  return raw.replace(/-/g, '');
}
const dbIds = Object.fromEntries(Object.entries(setup.databases).map(([k, v]) => [k, idFromUrl(v)]));

async function append(blockId, blocks) {
  for (let i = 0; i < blocks.length; i += 90) {
    await notion(`/blocks/${blockId}/children`, { method: 'PATCH', body: { children: blocks.slice(i, i + 90) } });
  }
}

async function createPage(title, emoji, children = [], coverUrl = null) {
  const body = {
    parent: { page_id: parentPageId },
    icon: { type: 'emoji', emoji },
    properties: { title: { title: rt(title) } },
    children
  };
  if (coverUrl) body.cover = { type: 'external', external: { url: coverUrl } };
  return notion('/pages', { method: 'POST', body });
}

async function queryDb(database_id, filter) {
  return notion(`/databases/${database_id}/query`, { method: 'POST', body: filter ? { filter } : {} });
}

async function addDbRow(database_id, properties) {
  return notion('/pages', { method: 'POST', body: { parent: { database_id }, properties } });
}
const titleProp = (s) => ({ title: rt(s) });
const richProp = (s) => ({ rich_text: s ? rt(s) : [] });
const selectProp = (s) => ({ select: s ? { name: s } : null });
const numProp = (n) => ({ number: n });
const cbProp = (b) => ({ checkbox: !!b });

console.log('Update parent page cover/icon/title...');
await notion(`/pages/${parentPageId}`, {
  method: 'PATCH',
  body: {
    icon: { type: 'emoji', emoji: '🏔️' },
    cover: { type: 'external', external: { url: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80' } },
    properties: { title: { title: rt('Bayern Trip — Dashboard') } }
  }
});

console.log('Query counts...');
const people = await queryDb(dbIds.participants);
const total = people.results.length;
let yes = 0, conditional = 0, unknown = 0, no = 0;
for (const row of people.results) {
  const s = row.properties.Status?.select?.name;
  if (s === 'Yes' || s === 'Organizer') yes++;
  else if (s === 'Conditional') conditional++;
  else if (s === 'No') no++;
  else unknown++;
}

console.log('Create visual subpages...');
const dashboard = await createPage('🏔️ Dashboard — Überblick', '🏔️', [
  callout('🎯', 'Ziel jetzt: verbindliche Teilnehmerzahl + Termin festlegen, damit Camping realistisch angefragt/gebucht werden kann.', 'blue_background'),
  callout('⏰', 'Deadline für den Poll: übermorgen 20:00 Uhr. Danach nur mit Ja-Stimmen weiterplanen.', 'yellow_background'),
  callout('⚠️', 'Hauptblocker: Keine Buchung ohne genaue Personenanzahl, Autos/Fahrer und Zelt-/Equipment-Lage.', 'red_background'),
  h2('Auf einen Blick'),
  bul(`Sichtbare Personen in der Teilnehmerdatenbank: ${total}`),
  bul(`Aktuell sicher/Organizer: ${yes}`),
  bul(`Bedingt dabei: ${conditional}`),
  bul(`Noch offen/unbekannt: ${unknown}`),
  h2('Nächste 5 Entscheidungen'),
  todo('Wer ist wirklich dabei?'),
  todo('Welches Wochenende gewinnt trotz Konflikten?'),
  todo('Wie viele Autos und Fahrer haben wir?'),
  todo('Wie viele Zelte/Schlafplätze sind sicher?'),
  todo('Welcher Campingplatz akzeptiert 2 Nächte für die Gruppengröße?'),
  h2('Direkt zu den Arbeitsbereichen'),
  p('Die Datenbanken liegen unten als verlinkte Bereiche. Nutze sie als Arbeitslisten, nicht als Deko.'),
  linkToDb(dbIds.participants),
  linkToDb(dbIds.dates),
  linkToDb(dbIds.tasks),
  linkToDb(dbIds.camping),
  linkToDb(dbIds.cars),
  linkToDb(dbIds.packing),
  linkToDb(dbIds.budget)
], 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1800&q=80');

const participantsPage = await createPage('👥 Teilnehmer & Zusagen', '👥', [
  callout('✅', 'Hier wird aus dem WhatsApp-Poll eine verbindliche Liste. Ziel: nur echte Zusagen zählen.', 'green_background'),
  h2('Arbeitsregel'),
  bul('Ja = wird für Camping/Auto/Budget eingeplant.'),
  bul('Conditional = zählt erst, wenn der passende Termin feststeht.'),
  bul('Unknown = aktiv nachfragen oder nach Deadline ignorieren.'),
  h2('Teilnehmerdatenbank'),
  linkToDb(dbIds.participants),
  h2('Bekannte Hinweise'),
  bul('Björn: nicht am 27.; sonst dabei.'),
  bul('Azika: dabei, falls 10.07.–12.07.')
]);

const campingPage = await createPage('⛺ Camping & Buchung', '⛺', [
  callout('🏕️', 'Camping erst seriös anfragen, wenn Teilnehmerzahl + Termin + Autos/Zelte klar sind.', 'brown_background'),
  h2('Buchungscheck'),
  todo('Teilnehmerzahl final'),
  todo('Termin final'),
  todo('Zeltanzahl / Stellplatzbedarf klar'),
  todo('Autos / Parkplätze klar'),
  todo('2-Nächte-Regel im Juli prüfen'),
  h2('Camping-Datenbank'),
  linkToDb(dbIds.camping)
]);

const transportPage = await createPage('🚗 Autos & Transport', '🚗', [
  callout('🚗', 'Für 6–10 Personen wahrscheinlich 2–3 private Autos ab Dortmund. Fahrer sind kritischer als Mitfahrer.', 'blue_background'),
  h2('Was geklärt werden muss'),
  todo('Wer kann sicher fahren?'),
  todo('Wie viele freie Sitzplätze pro Auto?'),
  todo('Wer bringt Zelte/Equipment im Auto unter?'),
  todo('Abfahrt Dortmund: Uhrzeit + Treffpunkt'),
  h2('Auto-Datenbank'),
  linkToDb(dbIds.cars)
]);

const packingPage = await createPage('🎒 Packliste & Gruppenequipment', '🎒', [
  callout('🎒', 'Nicht jeder muss alles mitbringen. Kritisch sind Zelte, Schlafsystem, Kochen, Müll, Strom und Regenzeug.', 'green_background'),
  h2('Priorität A'),
  bul('Zelte / Schlafplätze'),
  bul('Schlafsack + Isomatte'),
  bul('Regenjacke / warme Schichten'),
  bul('Müllbeutel + Erste-Hilfe'),
  h2('Packlisten-Datenbank'),
  linkToDb(dbIds.packing)
]);

const budgetPage = await createPage('💶 Budget & Anzahlung', '💶', [
  callout('💶', 'Realistisch kommunizieren: 160–180 € p.P. als sicherer Rahmen, bis Camping/Transport bestätigt sind.', 'yellow_background'),
  h2('Kostenblöcke'),
  bul('Camping'),
  bul('Sprit / Parken'),
  bul('Essen / Gruppeneinkauf'),
  bul('Aktivitäten / Reserve'),
  h2('Budget-Datenbank'),
  linkToDb(dbIds.budget)
]);

const routePage = await createPage('🧭 Route & Ideen — Allgäu / Via Claudia', '🧭', [
  callout('🏰', 'Füssen/Allgäu passt gut, weil dort Neuschwanstein, Alpenpanorama und die Via Claudia Augusta zusammenkommen.', 'purple_background'),
  h2('Ideen, nicht final'),
  bul('Füssen / Schwangau als Basis'),
  bul('Neuschwanstein / Alpsee als Klassiker'),
  bul('Via Claudia Augusta Etappe Roßhaupten – Füssen als leichte Landschafts-/Aussichtsoption'),
  bul('Kein Partyfokus, eher Camping + Wandern + Aussicht'),
  h2('Recherche-Links'),
  bookmark('https://www.allgaeu.de/touren/radfernroute-via-claudia-augusta-etappe-rosshaupten-fuessen', 'Via Claudia Augusta: Roßhaupten – Füssen / Allgäu'),
  bookmark('https://www.fuessen.de/kultur/ferienstrassen/', 'Füssen: Romantische Straße, Deutsche Alpenstraße, Via Claudia Augusta')
]);

console.log('Append visual hub section to parent...');
await append(parentPageId, [
  divider(),
  h1('🏔️ Visueller Trip-Hub'),
  callout('🏔️', 'Nutze diesen Bereich als Startpunkt. Die Unterseiten sind klarer als eine einzige riesige Tabelle.', 'blue_background'),
  h2('Start hier'),
  linkToPage(dashboard.id),
  h2('Planungsseiten'),
  linkToPage(participantsPage.id),
  linkToPage(campingPage.id),
  linkToPage(transportPage.id),
  linkToPage(packingPage.id),
  linkToPage(budgetPage.id),
  linkToPage(routePage.id),
  h2('Arbeitslogik'),
  bul('Erst Zusagen + Termin.'),
  bul('Dann Campingplatz anfragen.'),
  bul('Parallel Autos/Fahrer und Zelte klären.'),
  bul('Danach Budget finalisieren und ggf. Anzahlung einsammeln.')
]);

console.log('Add extra practical rows...');
const extraTasks = [
  ['Zelt-/Schlafplatz-Abfrage in WhatsApp posten', 'Offen', 'Endrit', 'Hoch', 'Wer hat Zelt? Wie viele Schlafplätze?'],
  ['Fahrer-Abfrage posten', 'Offen', 'Endrit', 'Hoch', 'Wer fährt sicher? Wie viele Plätze frei?'],
  ['Camping-Anfrage-Text vorbereiten', 'Offen', 'Endrit', 'Mittel', 'Sobald Teilnehmerzahl + Termin klar sind'],
  ['Poll nach Deadline auswerten', 'Offen', 'Endrit', 'Hoch', 'Ja/Maybe/Nein sauber übertragen']
];
for (const [aufgabe, status, owner, prio, notes] of extraTasks) {
  await addDbRow(dbIds.tasks, {
    Aufgabe: titleProp(aufgabe), Status: selectProp(status), Owner: richProp(owner), Priorität: selectProp(prio), Notizen: richProp(notes)
  });
}

const extraPacking = [
  ['Zelt 1', 'Schlafen', '', true, 'Offen'],
  ['Zelt 2', 'Schlafen', '', true, 'Offen'],
  ['Erste-Hilfe-Set', 'Gruppe', '', true, 'Offen'],
  ['Regenschutz / Tarp', 'Gruppe', '', false, 'Offen'],
  ['Kühlbox', 'Kochen', '', false, 'Offen']
];
for (const [item, cat, owner, req, status] of extraPacking) {
  await addDbRow(dbIds.packing, {
    Item: titleProp(item), Kategorie: selectProp(cat), 'Wer bringt es?': richProp(owner), Pflicht: cbProp(req), Status: selectProp(status)
  });
}

const output = {
  ok: true,
  parent: 'https://www.notion.so/Bayern-Trip-363986920e81805f8bdfd6c7c6708370',
  pages: {
    dashboard: dashboard.url,
    participants: participantsPage.url,
    camping: campingPage.url,
    transport: transportPage.url,
    packing: packingPage.url,
    budget: budgetPage.url,
    route: routePage.url
  },
  counts: { total, yes, conditional, unknown, no },
  added: { tasks: extraTasks.length, packing: extraPacking.length }
};
fs.writeFileSync('data/bayern_trip/beautify_result.json', JSON.stringify(output, null, 2));
console.log(JSON.stringify(output, null, 2));

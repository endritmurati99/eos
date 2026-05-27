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
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) throw new Error(`${method} ${path} failed: ${res.status} ${data.message || text}`);
  return data;
}

function richText(items = []) {
  return items.map(item => item.plain_text || item.text?.content || '').join('').trim();
}

function propValue(prop) {
  if (!prop) return '';
  switch (prop.type) {
    case 'title':
      return richText(prop.title);
    case 'rich_text':
      return richText(prop.rich_text);
    case 'select':
      return prop.select?.name || '';
    case 'multi_select':
      return prop.multi_select.map(s => s.name).join(', ');
    case 'number':
      return prop.number === null || prop.number === undefined ? '' : String(prop.number);
    case 'checkbox':
      return prop.checkbox ? 'ja' : 'nein';
    case 'date':
      return prop.date?.end ? `${prop.date.start} bis ${prop.date.end}` : prop.date?.start || '';
    case 'url':
      return prop.url || '';
    case 'email':
      return prop.email || '';
    case 'phone_number':
      return prop.phone_number || '';
    case 'status':
      return prop.status?.name || '';
    case 'people':
      return prop.people.map(p => p.name || p.id).join(', ');
    default:
      return '';
  }
}

async function children(blockId) {
  const out = [];
  let cursor;
  do {
    const qs = new URLSearchParams({ page_size: '100' });
    if (cursor) qs.set('start_cursor', cursor);
    const res = await notion(`/blocks/${blockId}/children?${qs.toString()}`);
    out.push(...res.results);
    cursor = res.has_more ? res.next_cursor : null;
  } while (cursor);
  return out;
}

function blockText(block) {
  const value = block[block.type];
  if (!value) return '';
  if (Array.isArray(value.rich_text)) return richText(value.rich_text);
  if (block.type === 'child_page') return value.title || '';
  if (block.type === 'child_database') return value.title || '';
  return '';
}

function blockToMarkdown(block) {
  const text = blockText(block);
  if (!text) return '';
  switch (block.type) {
    case 'heading_1':
      return `# ${text}`;
    case 'heading_2':
      return `## ${text}`;
    case 'heading_3':
      return `### ${text}`;
    case 'bulleted_list_item':
      return `- ${text}`;
    case 'numbered_list_item':
      return `1. ${text}`;
    case 'to_do':
      return `- [${block.to_do.checked ? 'x' : ' '}] ${text}`;
    case 'callout':
      return `> ${text}`;
    case 'child_page':
      return `- Notion-Unterseite: ${text}`;
    case 'child_database':
      return `- Notion-Datenbank: ${text}`;
    default:
      return text;
  }
}

async function pageMarkdown(title, pageId) {
  const blocks = await children(pageId);
  const lines = [`## ${title}`];
  for (const block of blocks) {
    const line = blockToMarkdown(block);
    if (line) lines.push(line);
  }
  return lines.join('\n');
}

async function queryDatabase(dbId) {
  const out = [];
  let cursor;
  do {
    const body = { page_size: 100 };
    if (cursor) body.start_cursor = cursor;
    const res = await notion(`/databases/${dbId}/query`, { method: 'POST', body });
    out.push(...res.results);
    cursor = res.has_more ? res.next_cursor : null;
  } while (cursor);
  return out;
}

function databaseMarkdown(title, rows) {
  const lines = [`## ${title}`];
  if (!rows.length) {
    lines.push('_Keine Einträge gefunden._');
    return lines.join('\n');
  }

  for (const row of rows) {
    const entries = Object.entries(row.properties)
      .map(([name, prop]) => [name, propValue(prop)])
      .filter(([, value]) => value);
    const titleEntry = entries.find(([, value]) => value) || ['Eintrag', row.id];
    lines.push(`### ${titleEntry[1]}`);
    for (const [name, value] of entries) {
      lines.push(`- ${name}: ${value}`);
    }
  }
  return lines.join('\n');
}

async function main() {
  const [mainPage, participantsPage, planningPage, logisticsPage, commsPage] = await Promise.all([
    pageMarkdown('Notion-Hauptseite Bayern Trip', ids.main),
    pageMarkdown('Teilnehmer-Unterseite', ids.pages.participants),
    pageMarkdown('Planung-Unterseite', ids.pages.planning),
    pageMarkdown('Logistik-Unterseite', ids.pages.logistics),
    pageMarkdown('Kommunikation-Unterseite', ids.pages.comms)
  ]);

  const dbRows = {};
  for (const [name, id] of Object.entries(ids.dbs)) {
    dbRows[name] = await queryDatabase(id);
  }

  const secondBrain = fs.readFileSync('data/bayern_trip/second-brain-status.md', 'utf8').trim();
  const viaClaudia = fs.readFileSync('data/bayern_trip/via_claudia_analysis_2026-05-18.md', 'utf8').trim();
  const planning = JSON.parse(fs.readFileSync('data/bayern_trip/planning-data.json', 'utf8'));

  const now = new Date().toISOString();
  const md = [
    '# Bayern Trip / Via Claudia — Gesamtstand',
    '',
    `Erstellt: ${now}`,
    '',
    '> Arbeitsdokument aus Notion, Second Brain, lokalen Planungsdaten und Via-Claudia-Analyse. Keine Buchung wurde ausgelöst.',
    '',
    '## Executive Summary',
    '',
    '- Ziel: Bayern-/Allgäu-Camping- und Wandertrip mit Via Claudia Camping als Hauptoption.',
    '- Aktueller Organizer-Fokus: verbindlichen Gruppenpoll starten, finale Teilnehmerzahl klären und danach Stellplätze endgültig buchen.',
    '- Aktueller Planungsrahmen: ca. 12 Personen, voraussichtlich 3 Autos, mehrere Zelte, Anreise aus Dortmund, Freitag bis Sonntag.',
    '- Gewünschte Buchungslogik: einfache/günstige sinnvolle Lösung; kein Komfort/Plus als Standard, wenn Standardstellplätze oder Zeltlösung reichen.',
    '- Kritischer Punkt: Zeltwiesen sind nicht zuverlässig im Voraus reservierbar; deshalb sind normale reservierbare Stellplätze die sichere Variante.',
    '- Neuer Nutzerstand: Für alle drei Wochenenden ist Buchung möglich und genug Platz vorhanden; finale Buchung soll nach verbindlichem Poll erfolgen.',
    '',
    '## Drei Wochenendoptionen für den Poll',
    '',
    '- 26.06.2026–28.06.2026 — früheres Angebot/Optionsreservierung lag hierzu vor.',
    '- 03.07.2026–05.07.2026 — angefragte Juli-Option.',
    '- 10.07.2026–12.07.2026 — angefragte Juli-Option; aus früheren WhatsApp-Notizen für mehrere Personen gut passend.',
    '',
    'Hinweis: MEMORY.md hatte zuletzt Juni eher ausgeschlossen, außer Endrit ändert das. Durch die neue Aussage „ich habe jetzt die drei Daten“ ist Juni wieder als Poll-Option aufgenommen.',
    '',
    '## Empfohlene nächste Entscheidung',
    '',
    '1. Gruppenpoll mit allen drei Wochenenden starten.',
    '2. Nur verbindliche Zusagen zählen.',
    '3. Nach Poll zusätzlich Autos/Fahrer/Zelte abfragen.',
    '4. Termin mit stärkster verbindlicher Zusage wählen.',
    '5. Via Claudia final bestätigen und nur die nötige Stellplatzanzahl buchen.',
    '',
    '## Poll-Text für Telegram/WhatsApp',
    '',
    '```text',
    'Bayern-Trip / Via Claudia Camping',
    '',
    'Ich kann jetzt bei Via Claudia für alle drei Wochenenden buchen, es gibt aktuell genug Platz. Damit ich endgültig reservieren kann, brauche ich bitte eine verbindliche Rückmeldung.',
    '',
    'Bitte stimmt ab, an welchen Wochenenden ihr wirklich dabei seid. Danach buche ich den Termin mit den meisten festen Zusagen.',
    '',
    'Wichtig: Bitte nur abstimmen, wenn ihr wirklich mitkommen würdet. Ich brauche danach die finale Zahl für Stellplätze, Autos und Zelte.',
    '',
    'Optionen:',
    '1. 26.06.–28.06.2026 — bin dabei',
    '2. 03.07.–05.07.2026 — bin dabei',
    '3. 10.07.–12.07.2026 — bin dabei',
    '4. Ich bin leider raus',
    '',
    'Wer dabei ist, schreibt bitte zusätzlich kurz:',
    '- Auto ja/nein?',
    '- Fahrer ja/nein?',
    '- Zelt ja/nein, wie viele Plätze?',
    '```',
    '',
    '## Organisationslogik',
    '',
    '- Bei 12 Personen und 3 Autos wirkt 1 Stellplatz unrealistisch, selbst wenn die Fläche theoretisch reicht.',
    '- Bester Verhandlungspunkt: möglichst 1–2 normale Stellplätze plus separates Parken für zusätzliches Auto, falls Via Claudia das erlaubt.',
    '- Wenn Via Claudia aus Platzordnung/Personenregel mehr Stellplätze verlangt, sollte final nach tatsächlicher Teilnehmerzahl gebucht werden.',
    '- Wenn weniger als 12 fest zusagen, reduziert sich ggf. Stellplatz-/Personenbedarf.',
    '',
    '## Teilnehmer- und WhatsApp-Kontext aus lokaler Planung',
    '',
    `- WhatsApp-Gruppe: ${planning.screenshot_extraction?.whatsapp_group || 'Bayern_Trip'}`,
    `- Sichtbare Gruppengröße: ${planning.screenshot_extraction?.group_size_visible || 'nicht gesetzt'}`,
    `- Sichtbare frühere Ja-Stimmen: ${planning.screenshot_extraction?.poll_yes_count_visible || 'nicht gesetzt'}`,
    '',
    ...(planning.visible_members || []).map(member => `- ${member.name}: ${member.status}${member.notes ? ` — ${member.notes}` : ''}`),
    '',
    mainPage,
    '',
    participantsPage,
    '',
    planningPage,
    '',
    logisticsPage,
    '',
    commsPage,
    '',
    databaseMarkdown('Notion-Datenbank: Teilnehmer', dbRows.participants),
    '',
    databaseMarkdown('Notion-Datenbank: Termine', dbRows.dates),
    '',
    databaseMarkdown('Notion-Datenbank: Aufgaben', dbRows.tasks),
    '',
    databaseMarkdown('Notion-Datenbank: Logistik', dbRows.logistics),
    '',
    databaseMarkdown('Notion-Datenbank: Budget', dbRows.budget),
    '',
    '---',
    '',
    secondBrain,
    '',
    '---',
    '',
    viaClaudia
  ].join('\n');

  const outPath = 'data/bayern_trip/bayern-trip-via-claudia-gesamtstand.md';
  fs.writeFileSync(outPath, `${md.trim()}\n`);
  console.log(outPath);
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});

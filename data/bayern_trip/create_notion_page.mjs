// Creates a simple Bayern Trip Notion page via Notion API.
// Requirements:
//   export NOTION_TOKEN='secret_...'
//   export NOTION_PARENT_PAGE_ID='...'
//   node data/bayern_trip/create_notion_page.mjs
// Important: Share the parent Notion page with your integration first.

const token = process.env.NOTION_TOKEN;
const parentPageId = process.env.NOTION_PARENT_PAGE_ID;
if (!token || !parentPageId) {
  console.error('Missing NOTION_TOKEN or NOTION_PARENT_PAGE_ID.');
  process.exit(1);
}

async function notion(path, body) {
  const res = await fetch(`https://api.notion.com/v1${path}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Notion-Version': '2022-06-28'
    },
    body: JSON.stringify(body)
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`${res.status} ${text}`);
  return JSON.parse(text);
}

function p(text) {
  return { object:'block', type:'paragraph', paragraph:{ rich_text:[{ type:'text', text:{ content:text.slice(0, 1900) } }] } };
}
function h2(text) {
  return { object:'block', type:'heading_2', heading_2:{ rich_text:[{ type:'text', text:{ content:text } }] } };
}
function todo(text, checked=false) {
  return { object:'block', type:'to_do', to_do:{ rich_text:[{ type:'text', text:{ content:text } }], checked } };
}

const children = [
  h2('Status'),
  p('Phase: Verbindliche Teilnehmerzahl + Terminverfügbarkeit klären. Deadline: übermorgen 20:00 Uhr. Hauptblocker: Ohne genaue Teilnehmerzahl keine Camping-Anfrage/Buchung.'),
  h2('WhatsApp Text'),
  p('Hey Leute, ich brauche jetzt bitte verbindlich die genaue Teilnehmeranzahl für den Bayern-Trip, damit ich den Campingplatz anfragen/buchen kann. Stimmt bitte im Poll ab, ob ihr grundsätzlich dabei seid. Falls ihr an bestimmten Terminen nicht könnt, schreibt das bitte kurz in die Gruppe, weil ich das im Poll nicht sauber abfragen kann. Wichtig: Es geht erstmal darum, wer wirklich dabei sein will — ohne genaue Anzahl kann ich nichts buchen. Bitte bis übermorgen 20:00 Uhr abstimmen.'),
  h2('Bekannte Teilnehmer / Notizen'),
  p('Björn Ironside: kann am 27. nicht wegen ADAC-Kurventraining; sonst dabei. Azika: falls 10.07.–12.07., wäre sie auch dabei. Gruppe laut Screenshots: Bayern_Trip, 13 Mitglieder.'),
  h2('Startaufgaben'),
  todo('Poll bis Deadline beobachten'),
  todo('Verbindliche Ja-Liste erstellen'),
  todo('Termin mit wenigsten Konflikten wählen'),
  todo('Campingplätze shortlist erstellen'),
  todo('Autos/Fahrer klären'),
  todo('Budget bestätigen'),
  h2('Datenbanken, die in Notion angelegt werden sollten'),
  p('Participants / RSVP, Terminoptionen, Camping/Unterkunft, Transport/Autos, Budget, Packliste, Aufgaben, Entscheidungslog. CSV-Import: data/bayern_trip/participants.csv')
];

const page = await notion('/pages', {
  parent: { page_id: parentPageId },
  icon: { emoji: '🏕️' },
  properties: { title: { title: [{ type:'text', text:{ content:'Bayern Trip — Planungszentrale' } }] } },
  children
});
console.log(page.url);

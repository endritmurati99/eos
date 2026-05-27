import fs from 'node:fs';
const token = fs.readFileSync('/data/.openclaw/secrets/notion.token','utf8').trim();
const version='2022-06-28';
const ids={comms:'363986920e81815ea740e04ab5be5f35', tasks:'363986920e81817482c6eaed18539cd9', logistics:'363986920e8181c29af0d8e22b57d34a'};
async function notion(path,{method='GET',body}={}){const res=await fetch(`https://api.notion.com/v1${path}`,{method,headers:{Authorization:`Bearer ${token}`,'Notion-Version':version,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined}); const text=await res.text(); let data; try{data=JSON.parse(text)}catch{data={raw:text}} if(!res.ok)throw new Error(`${method} ${path} failed: ${res.status} ${data.message||text}`); return data;}
const rt=s=>[{type:'text',text:{content:String(s??'').slice(0,1900)}}];
const h2=s=>({object:'block',type:'heading_2',heading_2:{rich_text:rt(s)}});
const h3=s=>({object:'block',type:'heading_3',heading_3:{rich_text:rt(s)}});
const bul=s=>({object:'block',type:'bulleted_list_item',bulleted_list_item:{rich_text:rt(s)}});
const callout=(emoji,s,color='gray_background')=>({object:'block',type:'callout',callout:{icon:{type:'emoji',emoji},rich_text:rt(s),color}});
const code=s=>({object:'block',type:'code',code:{language:'plain text',rich_text:rt(s)}});
const titleProp=s=>({title:rt(s)}), richProp=s=>({rich_text:s?rt(s):[]}), selectProp=s=>({select:s?{name:s}:null});
async function queryAll(db){const out=[];let cur;do{const body={page_size:100}; if(cur)body.start_cursor=cur; const r=await notion(`/databases/${db}/query`,{method:'POST',body}); out.push(...r.results); cur=r.has_more?r.next_cursor:null;}while(cur);return out;}
function plainTitle(page,prop){return page.properties?.[prop]?.title?.map(t=>t.plain_text).join('').trim()||''}
async function upsert(db,titleName,title,props){const rows=await queryAll(db); const ex=rows.find(p=>plainTitle(p,titleName).toLowerCase()===title.toLowerCase()); if(ex){await notion(`/pages/${ex.id}`,{method:'PATCH',body:{properties:props}}); return 'updated'} await notion('/pages',{method:'POST',body:{parent:{database_id:db},properties:{[titleName]:titleProp(title),...props}}}); return 'created';}
await notion(`/blocks/${ids.comms}/children`,{method:'PATCH',body:{children:[
 h2('Via Claudia Analyse — 18.05.2026'),
 callout('🏕️','Nicht gesendet: erst Analyse/Rückfragen vorbereitet. Aktueller Gruppenstand eher 10–12 Personen; Juli/10.07 wirkt besser als 26.06.', 'blue_background'),
 h3('Aus Mail / PDF'),
 bul('Angeboten/gebucht: Seeblick Standardplatz Plus 081–084, 26.06.–28.06., 2 Nächte, kalkuliert für 8 Erwachsene.'),
 bul('Gesamtbetrag im PDF: 387,20 €; Anzahlung 40,00 € bis 26.05.2026; Rest vor Ort bar/EC.'),
 bul('Standard-Plus laut Website/Unterlagen: ca. 80–100 m², 16A Strom, Wasserstellen in der Umgebung.'),
 bul('Zeltwiesen sind nicht vorreservierbar; normale Stellplätze sind reservierbar, genaue Platznummern aber nicht garantiert.'),
 bul('Anreise ab 14:00, Abreise bis 11:00; Anreise möglichst bis 18:00, später nur mit Info; Nachtruhe 22:00–07:00.'),
 bul('Storno: bis 30 Tage vorher 10 € Bearbeitungsgebühr pro Buchung; ab 30 Tage Stornogebühr in Höhe der Anzahlung.'),
 h3('Offene Kernfragen für nächste Anfrage'),
 bul('Aktualisiertes Angebot für 10, 11 und 12 Erwachsene.'),
 bul('Verfügbarkeit 03.07.–05.07., 10.07.–12.07., 17.07.–19.07.'),
 bul('Wie viele Personen/Zelte pro Standard-Plus-Stellplatz erlaubt bzw. realistisch sind.'),
 bul('Ob je Platz ein Auto stehen darf und wie 2–3 Autos abgestellt/bezahlt werden.'),
 bul('Ob Strom verpflichtend oder optional ist.'),
 bul('Wie einzelne Ausfälle/Personenzahländerungen erstattet oder angepasst werden.'),
 bul('Ob 3/4/5 Stellplätze nachträglich änderbar sind.'),
 bul('Gruppenregeln und späte Freitag-Anreise aus Dortmund.'),
 h3('Draft-Status'),
 code('Anfrageentwurf liegt lokal unter data/bayern_trip/via_claudia_analysis_2026-05-18.md — noch NICHT gesendet.')
]}});
const t1=await upsert(ids.tasks,'Aufgabe','Via Claudia Rückfragen finalisieren',{Bereich:selectProp('Camping'),Status:selectProp('Jetzt'),Owner:richProp('Endrit/EOS'),Notiz:richProp('Fragenkatalog vorbereitet; vor Versand Zieltermin und Personenzahl bestätigen.')});
const t2=await upsert(ids.tasks,'Aufgabe','Via Claudia aktualisiertes Angebot anfragen',{Bereich:selectProp('Camping'),Status:selectProp('Wartet'),Owner:richProp('Endrit'),Notiz:richProp('Nicht senden, bis Endrit Zieltermine/Personenrahmen freigibt.')});
const l1=await upsert(ids.logistics,'Punkt','Via Claudia Standard-Plus Stellplätze 081–084',{Typ:selectProp('Camping'),Status:selectProp('In Klärung'),Owner:richProp('Endrit/EOS'),Details:richProp('26.06-Angebot für 8 Erwachsene: 4 Standard-Plus Plätze Seeblick, 387,20 €, Anzahlung 40 €. Für 10–12 Personen und Juli neu anfragen.')});
console.log(JSON.stringify({ok:true,tasks:[t1,t2],logistics:l1},null,2));

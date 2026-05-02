#!/usr/bin/env node
import { mkdir, copyFile } from 'node:fs/promises';
import path from 'node:path';
import { edgeTTS } from '/data/.npm-global/lib/node_modules/openclaw/dist/extensions/microsoft/tts.js';

const args = process.argv.slice(2);
const opts = {};
for (let i = 0; i < args.length; i += 1) {
  const a = args[i];
  if (a.startsWith('--')) opts[a.slice(2)] = args[++i] ?? '';
}
const title = (opts.title || '').trim();
const text = (opts.text || '').trim();
if (!title || !text) {
  console.error('Usage: send_named_tts.mjs --title "Daily Briefing" --text "..."');
  process.exit(2);
}
const safeTitle = title.replace(/[\\/\0]/g, ' ').trim();
const outDir = '/data/.openclaw/media/outbound/eos-named';
await mkdir(outDir, { recursive: true });
const tmpPath = path.join(outDir, `${safeTitle}.${Date.now()}.mp3`);
const finalPath = path.join(outDir, `${safeTitle}.mp3`);
await edgeTTS({
  text,
  outputPath: tmpPath,
  timeoutMs: 60000,
  config: {
    voice: 'de-DE-KatjaNeural',
    lang: 'de-DE',
    outputFormat: 'audio-24khz-48kbitrate-mono-mp3'
  }
});
await copyFile(tmpPath, finalPath);
console.log(JSON.stringify({ ok: true, title, filename: `${safeTitle}.mp3`, path: finalPath }));

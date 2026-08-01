// Step 3: clean, filter spam, deduplicate, and export final CSV
const fs = require('fs');

function csvEscape(val) {
  const s = String(val ?? '');
  if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function decodeEntities(str) {
  return str
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#8217;/g, '’')
    .replace(/&#8216;/g, '‘')
    .replace(/&#8211;/g, '–')
    .replace(/&#8212;/g, '—')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
}

function wordCount(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function median(nums) {
  const sorted = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

// Spam / self-promo signals per Step 3 instructions
const PHONE_RE = /(\+?\d[\d\-\s]{7,}\d)/; // 8+ digit runs, allowing spaces/dashes (Nigerian numbers etc.)
const URL_RE = /(https?:\/\/|www\.)\S+/i;
const SPAM_PHRASES_RE = /\b(contact me|contact us|whatsapp|subscribe to my channel|dm me|inbox me|click the link|link in bio)\b/i;

function isSpam(text) {
  return PHONE_RE.test(text) || URL_RE.test(text) || SPAM_PHRASES_RE.test(text);
}

function main() {
  const raw = JSON.parse(fs.readFileSync('raw_comments.json', 'utf8'));
  console.log(`Raw comments loaded: ${raw.length}`);

  // Decode HTML entities in video titles and text
  const decoded = raw.map(r => ({
    ...r,
    video_title: decodeEntities(r.video_title),
    text: decodeEntities(r.text).trim(),
  }));

  // Drop spam/self-promo
  const noSpam = decoded.filter(r => !isSpam(r.text));
  console.log(`After spam filter: ${noSpam.length} (removed ${decoded.length - noSpam.length})`);

  // Deduplicate identical comment text
  const seen = new Set();
  const deduped = [];
  for (const row of noSpam) {
    const key = row.text;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(row);
  }
  console.log(`After dedup: ${deduped.length} (removed ${noSpam.length - deduped.length} exact duplicates)`);

  // Add word_count, drop <5 words
  const withCounts = deduped.map(r => ({ ...r, word_count: wordCount(r.text) }));
  const wordFiltered = withCounts.filter(r => r.word_count >= 5);
  console.log(`After dropping <5 words: ${wordFiltered.length} (removed ${withCounts.length - wordFiltered.length})`);

  // Cap any single video's contribution so one high-engagement video (e.g. a comedy
  // skit whose comments are mostly reactions to the actors, not insurance opinions)
  // doesn't drown out the other videos. Random sample, capped at 35 per video.
  const PER_VIDEO_CAP = 35;
  const byVideo = new Map();
  for (const r of wordFiltered) {
    if (!byVideo.has(r.video_id)) byVideo.set(r.video_id, []);
    byVideo.get(r.video_id).push(r);
  }
  const final = [];
  for (const [videoId, rows] of byVideo) {
    if (rows.length <= PER_VIDEO_CAP) {
      final.push(...rows);
    } else {
      const shuffled = [...rows].sort(() => Math.random() - 0.5);
      const sample = shuffled.slice(0, PER_VIDEO_CAP);
      final.push(...sample);
      console.log(`  [cap] ${videoId}: ${rows.length} -> ${PER_VIDEO_CAP} (random sample)`);
    }
  }
  console.log(`After per-video cap: ${final.length} (removed ${wordFiltered.length - final.length})`);

  // Write CSV
  const cols = ['source', 'video_id', 'video_title', 'text', 'like_count', 'date', 'word_count'];
  const lines = [cols.join(',')];
  for (const row of final) {
    lines.push(cols.map(c => csvEscape(row[c])).join(','));
  }
  fs.writeFileSync('youtube_comments.csv', lines.join('\n'), 'utf8');

  // Stats
  const totalComments = final.length;
  const numVideos = new Set(final.map(r => r.video_id)).size;
  const medianWc = median(final.map(r => r.word_count));
  const count20plus = final.filter(r => r.word_count >= 20).length;

  console.log('\n=== FINAL STATS ===');
  console.log(`Total comments: ${totalComments}`);
  console.log(`Number of videos: ${numVideos}`);
  console.log(`Median word count: ${medianWc}`);
  console.log(`Comments with 20+ words: ${count20plus} (${((count20plus/totalComments)*100).toFixed(1)}%)`);
  console.log(`\nSaved to youtube_comments.csv`);
}

main();

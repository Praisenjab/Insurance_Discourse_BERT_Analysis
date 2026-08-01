// Step 1: discover Nigerian insurance-related videos via YouTube Data API search
require('dotenv').config();
const fs = require('fs');

const KEY = process.env.YOUTUBE_API_KEY;
if (!KEY) { console.error('Missing YOUTUBE_API_KEY in .env'); process.exit(1); }

const QUERIES = [
  'insurance Nigeria explained',
  'NHIS Nigeria',
  'HMO Nigeria',
  'health insurance Nigeria',
  'car insurance Nigeria',
  'is insurance worth it Nigeria',
  'insurance scam Nigeria',
  'Reliance HMO',
  'AXA Mansard',
  'Leadway insurance',
];

const RESULTS_PER_QUERY = 15;
// search.list costs 100 units per call regardless of maxResults (up to 50 per page).
// 15 results fits in a single page (maxResults=15), so 1 call = 100 units per query.
const SEARCH_COST = 100;

let quotaUsed = 0;
function trackQuota(units, label) {
  quotaUsed += units;
  console.log(`  [quota] +${units} (${label}) -> running total: ${quotaUsed}`);
}

async function searchQuery(q) {
  const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=${RESULTS_PER_QUERY}&q=${encodeURIComponent(q)}&key=${KEY}`;
  const res = await fetch(url);
  const json = await res.json();
  trackQuota(SEARCH_COST, `search: "${q}"`);
  if (json.error) {
    console.error(`  API ERROR for "${q}":`, JSON.stringify(json.error.errors || json.error));
    return [];
  }
  return json.items || [];
}

async function main() {
  const videos = new Map(); // videoId -> {title, description, channelTitle(not stored per ethics), queries}

  for (const q of QUERIES) {
    console.log(`Searching: "${q}" ...`);
    const items = await searchQuery(q);
    console.log(`  -> ${items.length} results`);
    for (const it of items) {
      const id = it.id.videoId;
      if (!id) continue;
      const title = it.snippet.title;
      const description = it.snippet.description;
      if (!videos.has(id)) {
        videos.set(id, { videoId: id, title, description, queries: new Set() });
      }
      videos.get(id).queries.add(q);
    }
  }

  const list = [...videos.values()].map(v => ({
    videoId: v.videoId,
    title: v.title,
    description: v.description,
    queries: [...v.queries].join(';'),
  }));

  fs.writeFileSync('videos.json', JSON.stringify(list, null, 2));
  console.log(`\n=== DONE: ${list.length} unique videos found ===`);
  console.log(`Estimated quota used: ${quotaUsed} units`);
  for (const v of list) {
    console.log(`- [${v.videoId}] ${v.title}  (${v.queries})`);
  }
}

main();

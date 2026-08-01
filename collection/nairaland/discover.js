// Step 1: discover insurance-related thread URLs on Nairaland
const fs = require('fs');

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const DELAY_MS = 1700;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function fetchPage(url) {
  try {
    const res = await fetch(url, { headers: { 'User-Agent': UA } });
    if (!res.ok) {
      console.error(`  [skip] ${url} -> HTTP ${res.status}`);
      return null;
    }
    return await res.text();
  } catch (e) {
    console.error(`  [skip] ${url} -> ${e.message}`);
    return null;
  }
}

// Matches "/8715647/why-ai-ocr-changing-way" style thread links, capturing id+slug and title text
const THREAD_LINK_RE = /<a href="\/(\d{4,})\/([a-z0-9-]+)(?:\/\d+)?(?:#\d+)?"[^>]*>([^<]*)<\/a>/gi;

const RELEVANCE_RE = /insurance|\bhmo\b|assurance|naicom/i;

function decodeEntities(str) {
  return str
    .replace(/&#x27;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#8217;/g, "’")
    .replace(/&#8216;/g, "‘")
    .replace(/&#8211;/g, "–")
    .replace(/&#8212;/g, "—");
}

function extractThreads(html) {
  const found = new Map(); // url -> title
  let m;
  THREAD_LINK_RE.lastIndex = 0;
  while ((m = THREAD_LINK_RE.exec(html)) !== null) {
    const [, id, slug, rawTitle] = m;
    let title = decodeEntities(rawTitle).trim();
    if (title.startsWith('Re: ')) title = title.slice(4);
    if (!title) continue;
    const url = `https://www.nairaland.com/${id}/${slug}`;
    if (!found.has(url)) found.set(url, title);
  }
  return found;
}

async function main() {
  const allThreads = new Map(); // url -> {title, sources: Set}

  function addThreads(map, source) {
    for (const [url, title] of map) {
      if (!RELEVANCE_RE.test(title)) continue;
      if (!allThreads.has(url)) allThreads.set(url, { title, sources: new Set() });
      allThreads.get(url).sources.add(source);
    }
  }

  // --- Approach A: search endpoint across keyword variants ---
  const keywords = ['insurance', 'health insurance', 'hmo', 'motor insurance', 'insurance claim', 'life insurance'];
  const PAGES_PER_KEYWORD = 4; // pages are 0-indexed on nairaland's /search/.../N

  for (const kw of keywords) {
    const q = encodeURIComponent(kw.toLowerCase().replace(/\s+/g, '-'));
    // nairaland collapses spaces; test shows plain word works for single-word queries.
    // For multi-word we still pass the raw phrase URL-encoded with spaces as %20.
    const qParam = encodeURIComponent(kw);
    for (let page = 0; page < PAGES_PER_KEYWORD; page++) {
      const url = `https://www.nairaland.com/search/${qParam}/0/0/0/${page}`;
      console.log(`Fetching search: "${kw}" page ${page + 1} ...`);
      const html = await fetchPage(url);
      await sleep(DELAY_MS);
      if (!html) continue;
      const threads = extractThreads(html);
      const before = allThreads.size;
      addThreads(threads, `search:${kw}`);
      console.log(`  -> ${threads.size} links seen, +${allThreads.size - before} new relevant threads (total ${allThreads.size})`);
    }
  }

  // --- Approach B: board index pages, filtered by title ---
  const boards = [
    { slug: 'business', pages: 12 },
    { slug: 'health', pages: 12 },
    { slug: 'autos', pages: 8 },
  ];

  for (const board of boards) {
    for (let page = 0; page < board.pages; page++) {
      const url = page === 0
        ? `https://www.nairaland.com/${board.slug}`
        : `https://www.nairaland.com/${board.slug}/${page}`;
      console.log(`Fetching board: ${board.slug} page ${page + 1} ...`);
      const html = await fetchPage(url);
      await sleep(DELAY_MS);
      if (!html) continue;
      const threads = extractThreads(html);
      const before = allThreads.size;
      addThreads(threads, `board:${board.slug}`);
      console.log(`  -> ${threads.size} links seen, +${allThreads.size - before} new relevant threads (total ${allThreads.size})`);
    }
  }

  const list = [...allThreads.entries()].map(([url, { title, sources }]) => ({
    url, title, sources: [...sources].join(';'),
  }));

  fs.writeFileSync('threads.json', JSON.stringify(list, null, 2));
  console.log(`\n=== DONE: ${list.length} unique relevant threads found ===`);
  for (const t of list) {
    console.log(`- ${t.title}  [${t.url}]  (${t.sources})`);
  }
}

main();

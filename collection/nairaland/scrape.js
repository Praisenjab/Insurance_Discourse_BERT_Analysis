// Step 3: scrape all posts from discovered insurance-related threads
const fs = require('fs');

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const MIN_DELAY = 1500;
const MAX_DELAY = 2000;
const MAX_PAGES_PER_THREAD = 30;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function politeDelay() {
  const ms = MIN_DELAY + Math.random() * (MAX_DELAY - MIN_DELAY);
  return sleep(ms);
}

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

function decodeEntities(str) {
  return str
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#8217;/g, '’')
    .replace(/&#8216;/g, '‘')
    .replace(/&#8211;/g, '–')
    .replace(/&#8212;/g, '—')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
}

function stripTags(html) {
  return html.replace(/<[^>]+>/g, '');
}

function cleanPostText(rawHtml) {
  // Drop quoted-reply blocks (confirmed non-nested on nairaland)
  let text = rawHtml.replace(/<blockquote[^>]*>[\s\S]*?<\/blockquote>/gi, '');
  text = decodeEntities(text);
  text = stripTags(text);
  // collapse whitespace: trim each line, drop blank-line runs
  text = text
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0)
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text;
}

function extractTitle(html) {
  const m = html.match(/<title>(.*?) - [^-]+ - Nigeria<\/title>/);
  return m ? decodeEntities(m[1]).trim() : null;
}

function extractMaxPage(html) {
  let max = 1;
  const re = /<a href="\/\d+\/[a-z0-9-]+\/(\d+)" class="pgn">(\d+)<\/a>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const label = parseInt(m[2], 10);
    if (label > max) max = label;
  }
  return max;
}

function extractPosts(html) {
  const posts = [];
  const re = /id="pb\d+" class="l w pd"><div class=narrow[^>]*>([\s\S]*?)<div class="s button-row"/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const text = cleanPostText(m[1]);
    if (text) posts.push(text);
  }
  return posts;
}

function pageUrl(threadUrl, pageIndex1based) {
  return pageIndex1based === 1 ? threadUrl : `${threadUrl}/${pageIndex1based - 1}`;
}

async function scrapeThread(threadUrl, fallbackTitle) {
  const rows = [];
  console.log(`\n=== Scraping thread: ${threadUrl} ===`);
  const firstHtml = await fetchPage(threadUrl);
  await politeDelay();
  if (!firstHtml) {
    console.error(`  Could not fetch first page, skipping thread.`);
    return rows;
  }
  const title = extractTitle(firstHtml) || fallbackTitle;
  const maxPage = Math.min(extractMaxPage(firstHtml), MAX_PAGES_PER_THREAD);
  console.log(`  Title: "${title}"  Pages: ${maxPage}`);

  const firstPosts = extractPosts(firstHtml);
  console.log(`  Page 1: ${firstPosts.length} posts`);
  for (const text of firstPosts) {
    rows.push({ source: 'nairaland', thread_url: threadUrl, thread_title: title, page_url: threadUrl, text });
  }

  for (let p = 2; p <= maxPage; p++) {
    const url = pageUrl(threadUrl, p);
    const html = await fetchPage(url);
    await politeDelay();
    if (!html) continue;
    const posts = extractPosts(html);
    console.log(`  Page ${p}: ${posts.length} posts`);
    for (const text of posts) {
      rows.push({ source: 'nairaland', thread_url: threadUrl, thread_title: title, page_url: url, text });
    }
  }
  return rows;
}

async function main() {
  const args = process.argv.slice(2);
  const testMode = args.includes('--test');
  const threads = JSON.parse(fs.readFileSync('threads.json', 'utf8'));
  const targets = testMode ? threads.slice(0, 1) : threads;

  let allRows = [];
  for (const t of targets) {
    const rows = await scrapeThread(t.url, t.title);
    allRows = allRows.concat(rows);
  }

  const outFile = testMode ? 'raw_posts_test.json' : 'raw_posts.json';
  fs.writeFileSync(outFile, JSON.stringify(allRows, null, 2));
  console.log(`\n=== DONE: ${allRows.length} raw posts saved to ${outFile} ===`);
}

main();

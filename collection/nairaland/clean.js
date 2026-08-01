// Step 4: clean, deduplicate, and export final CSV
const fs = require('fs');

function csvEscape(val) {
  const s = String(val ?? '');
  if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function wordCount(text) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  return words.length;
}

function median(nums) {
  const sorted = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function main() {
  const raw = JSON.parse(fs.readFileSync('raw_posts.json', 'utf8'));
  console.log(`Raw posts loaded: ${raw.length}`);

  // Deduplicate identical post text (exact match, trimmed)
  const seen = new Set();
  const deduped = [];
  for (const row of raw) {
    const key = row.text.trim();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(row);
  }
  console.log(`After dedup: ${deduped.length} (removed ${raw.length - deduped.length} exact duplicates)`);

  // Add word_count, drop <5 words
  const withCounts = deduped.map(r => ({ ...r, word_count: wordCount(r.text) }));
  const final = withCounts.filter(r => r.word_count >= 5);
  console.log(`After dropping <5 words: ${final.length} (removed ${withCounts.length - final.length})`);

  // Write CSV
  const cols = ['source', 'thread_url', 'thread_title', 'text', 'word_count'];
  const lines = [cols.join(',')];
  for (const row of final) {
    lines.push(cols.map(c => csvEscape(row[c])).join(','));
  }
  fs.writeFileSync('nairaland_posts.csv', lines.join('\n'), 'utf8');

  // Stats
  const totalPosts = final.length;
  const numThreads = new Set(final.map(r => r.thread_url)).size;
  const medianWc = median(final.map(r => r.word_count));
  const count20plus = final.filter(r => r.word_count >= 20).length;

  console.log('\n=== FINAL STATS ===');
  console.log(`Total posts: ${totalPosts}`);
  console.log(`Number of threads: ${numThreads}`);
  console.log(`Median word count: ${medianWc}`);
  console.log(`Posts with 20+ words: ${count20plus} (${((count20plus/totalPosts)*100).toFixed(1)}%)`);
  console.log(`\nSaved to nairaland_posts.csv`);
}

main();

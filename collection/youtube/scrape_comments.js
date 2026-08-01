// Step 2: pull all top-level comments + replies for each discovered video
require('dotenv').config();
const fs = require('fs');

const KEY = process.env.YOUTUBE_API_KEY;
if (!KEY) { console.error('Missing YOUTUBE_API_KEY in .env'); process.exit(1); }

const DAILY_QUOTA_BUDGET = 10000;
const ALREADY_SPENT = 1000; // Step 1 discovery cost
const SAFETY_MARGIN = 200; // stop before actually hitting 0
const OUT_FILE = process.argv.includes('--test') ? 'raw_comments_test.json' : 'raw_comments.json';
const DELAY_MS = 250;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

let quotaUsed = ALREADY_SPENT;
function trackQuota(units, label) {
  quotaUsed += units;
  console.log(`  [quota] +${units} (${label}) -> running total: ${quotaUsed} / ${DAILY_QUOTA_BUDGET}`);
}
function quotaExhausted() {
  return quotaUsed >= (DAILY_QUOTA_BUDGET - SAFETY_MARGIN);
}

class QuotaExceededError extends Error {}

async function apiGet(url, label) {
  const res = await fetch(url);
  const json = await res.json();
  trackQuota(1, label);
  if (json.error) {
    const reason = json.error.errors && json.error.errors[0] && json.error.errors[0].reason;
    if (reason === 'quotaExceeded' || reason === 'dailyLimitExceeded') {
      throw new QuotaExceededError(reason);
    }
    return { error: json.error, reason };
  }
  return json;
}

function commentRow(videoId, videoTitle, snippet) {
  return {
    source: 'youtube',
    video_id: videoId,
    video_title: videoTitle,
    text: (snippet.textOriginal || snippet.textDisplay || '').trim(),
    like_count: snippet.likeCount ?? 0,
    date: snippet.publishedAt || '',
  };
}

async function fetchAllReplies(videoId, videoTitle, parentId, alreadyHave) {
  // fetch replies beyond what commentThreads already embedded
  const rows = [];
  let pageToken = '';
  let skipped = 0;
  do {
    const url = `https://www.googleapis.com/youtube/v3/comments?part=snippet&parentId=${parentId}&maxResults=100&textFormat=plainText${pageToken ? `&pageToken=${pageToken}` : ''}&key=${KEY}`;
    const json = await apiGet(url, `comments.list (replies of ${parentId})`);
    if (json.error) {
      console.error(`    [skip replies] ${parentId} -> ${json.reason || JSON.stringify(json.error)}`);
      return rows;
    }
    for (const item of json.items || []) {
      if (skipped < alreadyHave) { skipped++; continue; } // avoid double-counting embedded replies
      rows.push(commentRow(videoId, videoTitle, item.snippet));
    }
    pageToken = json.nextPageToken;
    if (pageToken) await sleep(DELAY_MS);
  } while (pageToken);
  return rows;
}

async function scrapeVideoComments(videoId, videoTitle) {
  const rows = [];
  let pageToken = '';
  let pageNum = 1;
  do {
    const url = `https://www.googleapis.com/youtube/v3/commentThreads?part=snippet,replies&videoId=${videoId}&maxResults=100&textFormat=plainText${pageToken ? `&pageToken=${pageToken}` : ''}&key=${KEY}`;
    const json = await apiGet(url, `commentThreads (${videoId} pg${pageNum})`);
    if (json.error) {
      console.error(`  [skip video] ${videoId} -> ${json.reason || JSON.stringify(json.error)}`);
      return rows;
    }
    for (const thread of json.items || []) {
      const topSnippet = thread.snippet.topLevelComment.snippet;
      rows.push(commentRow(videoId, videoTitle, topSnippet));

      const totalReplies = thread.snippet.totalReplyCount || 0;
      const embeddedReplies = (thread.replies && thread.replies.comments) || [];
      for (const r of embeddedReplies) {
        rows.push(commentRow(videoId, videoTitle, r.snippet));
      }
      if (totalReplies > embeddedReplies.length) {
        await sleep(DELAY_MS);
        const parentId = thread.snippet.topLevelComment.id;
        const extra = await fetchAllReplies(videoId, videoTitle, parentId, embeddedReplies.length);
        rows.push(...extra);
      }
      if (quotaExhausted()) throw new QuotaExceededError('budget-cap');
    }
    pageToken = json.nextPageToken;
    pageNum++;
    if (pageToken) await sleep(DELAY_MS);
  } while (pageToken && !quotaExhausted());
  return rows;
}

function saveProgress(allRows) {
  fs.writeFileSync(OUT_FILE, JSON.stringify(allRows, null, 2));
}

async function main() {
  const args = process.argv.slice(2);
  const testMode = args.includes('--test');
  let videos = JSON.parse(fs.readFileSync('videos.json', 'utf8'));
  if (testMode) videos = videos.slice(0, 3);
  const allRows = [];
  let videosDone = 0;
  let videosSkipped = 0;

  for (const v of videos) {
    if (quotaExhausted()) {
      console.log('\n[STOP] Quota budget nearly exhausted, stopping before next video.');
      break;
    }
    console.log(`\n=== ${v.videoId} | ${v.title} ===`);
    try {
      const rows = await scrapeVideoComments(v.videoId, v.title);
      console.log(`  -> ${rows.length} comments (incl. replies)`);
      if (rows.length === 0) videosSkipped++;
      allRows.push(...rows);
      videosDone++;
      saveProgress(allRows); // flush after every video so partial progress is never lost
    } catch (e) {
      if (e instanceof QuotaExceededError) {
        console.log(`\n[STOP] Quota exceeded (${e.message}). Saving what we have so far.`);
        saveProgress(allRows);
        console.log(`Saved ${allRows.length} comments from ${videosDone} videos to ${OUT_FILE}.`);
        console.log(`Remaining ${videos.length - videosDone - videosSkipped} videos were not processed — rerun tomorrow once quota resets.`);
        return;
      }
      console.error(`  [unexpected error] ${v.videoId}: ${e.message}`);
    }
    await sleep(DELAY_MS);
  }

  saveProgress(allRows);
  console.log(`\n=== DONE: ${allRows.length} raw comments from ${videosDone} videos saved to ${OUT_FILE} ===`);
  console.log(`Videos with 0 comments (disabled or empty): ${videosSkipped}`);
  console.log(`Final estimated quota used: ${quotaUsed} / ${DAILY_QUOTA_BUDGET}`);
}

main();

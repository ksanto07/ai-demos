# Signal engine

## How to run

From this directory.

```bash
cd demos/2026-10-15-signal-engine-last30days
python3 -m unittest test_engine.py
python3 run_e2e.py
```

`python3 run_e2e.py` is the one live command. It runs the digest, opens the rendered HTML page, then last30days on item 1. The three steps below are the same work, split apart.

Copy `.env.example` to `.env` and set `XAI_API_KEY` when you want the Grok keep/drop pass. This recording has no key. The keyword scorer writes the digest and prints `keyword scorer (no Grok key)`.

`--date YYYY-MM-DD` names the digest file. It does not change the 24 hour lookback.

## What this does

`python3 render_html.py` reads that markdown file and writes `digests/YYYY-MM-DD.html`. Open the HTML file in a browser. It is a dark page with large type, the date, and the top 5.

`python3 run_digest.py` reads GitHub releases, Hacker News stories, and YouTube videos from the last 24 hours. With no `XAI_API_KEY` it prints fetch counts for GitHub, Hacker News, and YouTube, then the cheap-filter drops (old, future, duplicate, cap) with a few titles, then `keyword scorer (no Grok key)` with a few KEEP scores and DROP lines marked `no keyword`. It drops future items, items older than the lookback, items whose title and snippet miss every keyword, and duplicate ids. The first copy wins. GitHub comes before Hacker News, and Hacker News comes before YouTube. When `XAI_API_KEY` is set, one Grok call keeps or drops the remaining items and the keyword-scorer caption is not printed. Rank is always a keyword count. The script writes the top 5 to `digests/YYYY-MM-DD.md`. The `--date` flag names that file. It does not change the lookback.

`XAI_API_KEY` lives in `.env`, which is gitignored. `.env.example` has the name only.

`python3 run_deepdive.py` reads item 1 from that file. It prints this command, then runs it when the script is on disk. `LAST30DAYS_HOST` stays unset. The child process only receives `PATH`, `HOME`, and `LANG`.

```bash
env -u LAST30DAYS_HOST python3 skills/last30days/scripts/last30days.py "<topic>" --search reddit,hackernews,polymarket,github
```

Set `last30days_checkout` in `config.json` to a clone of the skill. The script path is that directory plus `skills/last30days/scripts/last30days.py`. If the script is missing, the printed command is the result and the process exits 0.

The 2026-10-15 e2e take used a local clone, not a vendored copy. last30days has no install dependencies (`pyproject.toml` lists `dependencies = []`). Python 3.12 is enough. `LAST30DAYS_HOST` stays unset. The child process only receives `PATH`, `HOME`, and `LANG`, and `--search` is the free sources `reddit,hackernews,polymarket,github`.

```bash
git clone --depth 1 https://github.com/mvanhorn/last30days-skill.git /home/ubuntu/src/last30days-skill
```

`config.json` sets `last30days_checkout` to `/home/ubuntu/src/last30days-skill`. There is no `XAI_API_KEY` in this environment, so the keep/drop step is the keyword scorer.

To run the dive yourself.

```bash
git clone --depth 1 https://github.com/mvanhorn/last30days-skill.git
env -u LAST30DAYS_HOST python3 last30days-skill/skills/last30days/scripts/last30days.py "<topic>" --search reddit,hackernews,polymarket,github
```

On 2026-10-15 a separate checkout of last30days ran here on the number 1 title. That check added `--quick` to the command above. It exited 0. Hacker News returned 4 stories. Reddit returned HTTP 403. Polymarket and GitHub returned nothing for that query. With `last30days_checkout` empty, `run_deepdive.py` only prints the command and exits 0.

The e2e recording is [docs/recordings/2026-10-15-signal-engine-e2e-v2.mp4](../../docs/recordings/2026-10-15-signal-engine-e2e-v2.mp4). It is one live take on 2026-10-15 with no `XAI_API_KEY`, full-screen, and large type. The screen shows one command, then github 90, hn 20, and youtube 60, then cheap filters (old 115, future 0, duplicate 0, cap 10) with two dropped titles, then `keyword scorer (no Grok key)` with KEEP scores and DROP lines marked `no keyword` (keep 31, drop 14). The top 5 are a rendered HTML page, not the raw markdown. last30days then ran on item 1, "How I Keep Up with AI Without Drowning in It (Free Skill)", with `LAST30DAYS_HOST` unset and `--search reddit,hackernews,polymarket,github`. It exited 0. Reddit returned HTTP 403 and 0 threads. Hacker News returned 4 stories. GitHub returned 4 results. Polymarket returned 0 markets. Grok keep/drop is not in that take. The length is 68.0 seconds. There is no narration.

An earlier take is [docs/recordings/2026-10-15-signal-engine-e2e.mp4](../../docs/recordings/2026-10-15-signal-engine-e2e.mp4). The v2 file is the one to watch.

## What this does not do

It does not use OpenRouter. It does not use a database, a web UI, or a plugin loader. It does not call paid last30days backends. It does not vendor last30days. A missing key still writes a digest.

## Credits

Cole Medin's [build-signal-engine](https://github.com/coleam00/skills/tree/main/.claude/skills/build-signal-engine) skill is the pattern for cheap filters before a model, then one digest.

Matt Van Horn's [last30days](https://github.com/mvanhorn/last30days-skill) is the deep dive on item 1. This demo uses only the free sources.

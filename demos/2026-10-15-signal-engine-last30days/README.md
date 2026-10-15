# Signal engine

## How to run

From this directory.

```bash
cd demos/2026-10-15-signal-engine-last30days
python3 -m unittest test_engine.py
python3 run_digest.py
python3 run_deepdive.py
```

Copy `.env.example` to `.env` and set `XAI_API_KEY` when you want the Grok keep/drop pass. With no key, the keyword scorer still writes the digest.

`--date YYYY-MM-DD` names the digest file. It does not change the 24 hour lookback.

## What this does

`python3 run_digest.py` reads GitHub releases, Hacker News stories, and YouTube videos from the last 24 hours. It drops future items, items older than the lookback, items whose title and snippet miss every keyword, and duplicate ids. The first copy wins. GitHub comes before Hacker News, and Hacker News comes before YouTube. When `XAI_API_KEY` is set, one Grok call keeps or drops the remaining items. Rank is always a keyword count. The script writes the top 5 to `digests/YYYY-MM-DD.md`. The `--date` flag names that file. It does not change the lookback.

`XAI_API_KEY` lives in `.env`, which is gitignored. `.env.example` has the name only.

`python3 run_deepdive.py` reads item 1 from that file. It prints this command, then runs it when the script is on disk. `LAST30DAYS_HOST` stays unset. The child process only receives `PATH`, `HOME`, and `LANG`.

```bash
env -u LAST30DAYS_HOST python3 skills/last30days/scripts/last30days.py "<topic>" --search reddit,hackernews,polymarket,github
```

Set `last30days_checkout` in `config.json` to a clone of the skill. The script path is that directory plus `skills/last30days/scripts/last30days.py`. If the script is missing, the printed command is the result and the process exits 0.

To run the dive yourself.

```bash
git clone --depth 1 https://github.com/mvanhorn/last30days-skill.git
env -u LAST30DAYS_HOST python3 last30days-skill/skills/last30days/scripts/last30days.py "<topic>" --search reddit,hackernews,polymarket,github
```

On 2026-10-15 that command ran here against the number 1 title. It exited 0. Hacker News returned stories. Reddit returned HTTP 403. Polymarket and GitHub returned nothing for that query. `--quick` is optional and was used for that check.

## What this does not do

It does not use OpenRouter. It does not use a database, a web UI, or a plugin loader. It does not call paid last30days backends. It does not vendor last30days. A missing key still writes a digest.

## Credits

Cole Medin's [build-signal-engine](https://github.com/coleam00/skills/tree/main/.claude/skills/build-signal-engine) skill is the pattern for cheap filters before a model, then one digest.

Matt Van Horn's [last30days](https://github.com/mvanhorn/last30days-skill) is the deep dive on item 1. This demo uses only the free sources.

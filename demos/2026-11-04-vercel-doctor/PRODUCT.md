# Product

<!-- impeccable:product-schema 1 -->

Assumptions below are inferred from the demo brief. There was no question tool to confirm them.

## Platform

terminal

## Stack

Inferred. Vercel CLI 65.11.0 on a logged-out machine. Node is only how the CLI was installed.

## Users

Inferred. A reviewer runs `vercel doctor` in this folder, edits `vercel.json`, and runs doctor again.

## Product Purpose

The folder is a specimen. `vercel doctor` reports a failed `vercel.json` check on the keys `src` and `dest`. Success is that fail on the shipped file, then one rename to `source` and `destination` that clears only that check. Login stays Failed.

## Positioning

Doctor validates `vercel.json` without a login or a linked project. It never prompts, logs in, or links.

## Operating Context

The operator runs `vercel doctor` in a desktop terminal. The recording is 60 to 90 seconds, with captions and no voiceover.

## Capabilities and Constraints

The rewrite uses the copy that already produced the `src` error in an off-camera dry run. There is no page and no button that applies the fix. Doctor must leave the source unchanged. Login, team, project, and the install warning stay as measured.

## Brand Commitments

The terminal title is `vercel doctor`. No other brand assets were provided.

## Evidence on Hand

The dry run on 2026-11-04 used Vercel CLI 65.11.0. Doctor exited 0 on both runs. Do not invent customers, benchmarks, or a second screen.

## Product Principles

- The live doctor table is the thing under test.
- Ship the file before the fix.
- One fix changes both rewrite keys.
- Doctor stdout is the proof.

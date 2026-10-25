# Product

<!-- impeccable:product-schema 1 -->

Assumptions below are inferred from the demo brief. There was no question tool to confirm them.

## Platform

web

## Stack

Inferred. Electron 33.4.11 loads one static HTML page and one CSS file. The brief named Electron.

## Users

Inferred. A reviewer starts the window and runs Impeccable against the open page.

## Product Purpose

The window is a specimen. Impeccable 4.7.0 reads it over CDP and reports `straggler` and `unbalanced-heading`. Success is those two advisories on the shipped page, then one `text-wrap: pretty` edit that removes only `straggler`.

## Positioning

The scan reads the rendered lines in the open window. A static file scan does not report these two rules.

## Operating Context

The app listens on DevTools port 9222. The operator runs `impeccable detect --cdp 9222` in a separate shell. The recording is 60 to 90 seconds, with captions and no voiceover.

## Capabilities and Constraints

The heading and the paragraph use the copy and the measures that already produced both advisories in an off-camera dry run. The shipped page has no button that applies a fix. The scan must leave the source unchanged. On Linux the window needs `--no-sandbox` and `--disable-gpu`.

## Brand Commitments

The window title is Ledger, taken from the heading. No other brand assets were provided.

## Evidence on Hand

The dry run on 2026-10-25 used impeccable 4.7.0 and Electron 33.4.11. Do not invent customers, benchmarks, or a second screen.

## Product Principles

- The open window is the thing under test.
- Ship the page before the fix.
- One fix changes one declaration.
- The detector output is the proof.

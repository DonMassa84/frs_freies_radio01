# FRS Pages repair — 2026-10-08

Base commit: 41d5623007cee76a2608f85ba05e4812fcf99d3a.

## Cause

GitHub Pages returned HTTP 301 to http://schattenmacher.de/projektportal/. This host redirected to https://www.schattenmacher.de/projektportal/; final request timed out. Public DNS (Google DNS over HTTPS) returned apex A 82.212.214.7, not GitHub Pages. External website purpose and ownership were not verified; no external DNS was changed.

## Prior work

DonMassa84/shadowops, branch docs/schattenmacher-pages-autopilot-20261008, docs/deployment/SCHATTENMACHER_PAGES_AUTOPILOT.md contains an implementation prompt, not proof of completed setup. It separates public domain DNS from Proton VPN/local routing. No VPN settings changed. User-machine folders are not accessible in this workspace. No AGENTS.md found in the FRS repository tree.

## Repair

Remove docs/CNAME from FRS branch publishing. Redirect docs/index.html to ./projektportal/ with a fallback link. Preserve original PWA entry verbatim as docs/radio.html at the same asset-relative depth. Expand deployment trigger to docs/**.

## Verification / rollback

Check preserved PWA bytes, redirect target, local portal assets, deployment trigger before commit. Verify public HTTP responses after deployment. Pages settings API unavailable through connector. If domain remains attached, remove Custom domain in repository Settings > Pages; do not change external DNS.
Rollback only changed files to the base revision, preserving concurrent work. Restoring CNAME reinstates the broken domain redirect.

PRE_PROJECT and portal content remain unchanged. No private documents published.

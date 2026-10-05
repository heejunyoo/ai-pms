# Harness Kit — current build, 2026-09-30

## Authoritative source

- `current_content.py`: reviewed Korean and English content, with identical section identities.
- `build_current.py`: every current page, legacy alias, language reference bundle, explicit implementation export, and discovery files.
- `check_current.py`: route completeness, language/structure parity, private-data boundaries, HTML/JS, local links, offline resource constraints, bundles, and Vercel security headers.
- `check_site.py` and `check_codex.py`: compatible validation entrypoints for the new contract.
- The bundled ELI skill is ELI20-only in Codex and Claude. Ponytail and Graphify are optional third-party installs described in the bilingual skills guide; their code and local graphs are not exported.
- The reader path starts at `index` and the ELI20 `guide`: problem and terms → component responsibilities → a fictional end-to-end code change → verification limits → tool-specific setup. Keep the bilingual reference ZIP aligned with these pages.

## Local validation and publication

Run `python3 ~/.claude/harness/build/build_current.py` then `python3 ~/.claude/harness/build/check_site.py`.
The build also runs the live Codex/Claude/Handoff local checks and records only public, non-personal check status.
Use `~/.claude/harness/site/publish.sh --check` for build and validation without deployment.
When publication is requested, `~/.claude/harness/site/publish.sh` deploys the validated output to the existing Vercel project.
Check desktop/mobile rendering, all five guide controls, both language switches, public content equality, and headers.
Do not call script checks proof of application hook trust/delivery or performance improvement.

## Compatibility and historical material

Every previously published HTML route is regenerated from the current canonical page. Dated URLs no longer freeze stale instructions.
The default build also refreshes matching local `.claude/docs` pages, generic aliases, and downloads so local navigation uses the same release.
Old `body_*.html`, `kit*`, translation snapshots, and legacy reconstruction tests document the earlier format and are not current source.
The pre-update source is preserved in the local audit backup. Do not run old generators to publish current content.
Legacy generators retained in this directory are historical tooling; `publish.sh` calls only the current generator and checker.
The old checker's forced-low/layout assertions were replaced by assertions for inherited reasoning, expected-failure acceptance, all routes, and bilingual parity. Existing safety/session tests remain and additional regressions run.

## Trust boundary

Pages and downloads are references, not authorization and not automatic installers. Never export local config, memory, permission rules, credentials, or personal paths.
The reference ZIPs contain fully localized Markdown. The shared implementation ZIP intentionally preserves source comments and diagnostics and contains only explicitly allowlisted code and schemas.
Keep CSP, nosniff, frame restrictions, discovery files, and language links intact.

## AI PMS connectivity release, 2026-10-01

Canonical `ai-pms.html` and `ai-pms-en.html` explain central multi-user, multi-session projects, document/step/revision completion, observed versus declared MCP/data references, safe local hook examples and privacy limits. Navigation, index discovery and both reference ZIPs include the pages. Public links target https://ai-pms-dashboard.vercel.app, its `/report.html`, and https://github.com/heejunyoo/ai-pms; the parent release verifies availability and deployed bytes.

The implementation allowlist now includes `activity/connectivity.py` alongside the logger. Build only after the backend package is complete; run build_current.py then check_current.py. The old local activity viewer remains a personal reference, not the central product. The public dashboard is a synthetic static sample; automatic collection, production backend/authentication and real multi-user app-hook delivery remain outside its proof. No remote sender or trust settings are installed by this build.

## STE writing release, 2026-10-05

The bilingual skills guide explains the separate asd-ste100-interactive skill, Korean/English modes, ELI20 composition, complete-folder installation and heuristic limits. The implementation ZIP exports exactly five reviewed files from the installed Codex skill under skills/asd-ste100-interactive/. The Korean guide and both offline HTML tools are included; official rules and dictionaries are not. Do not describe the Korean adaptation as an official STE standard or automated compliance proof. Reference ZIPs include the same localized guidance.

## Two understanding paths, 2026-10-05

Keep guide.html / guide-en.html as the existing ELI20 path. ste.html adds a Korean STE-inspired harness guide; ste-en.html adds an English ASD-STE100-oriented guide. Each STE edition explains the full Kit scope of the existing ELI20 guide: purpose, terms, component responsibilities, the five-step fictional task, all five mechanisms, contents and verification boundaries, and agent setup links. Keep section identities aligned, link both editions in navigation and a page selector, and include ste.md in each reference ZIP. English examples are not certified compliant and dictionary approval is unverified.

## PMS adoption release, 2026-10-05

PMS-related Kit scope is local hook capture only. The implementation ZIP must have no `pms/` central runtime. Preserve all other Kit features and optional offline activity tools. Full dashboard/receiver/sender adoption lives at https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md. Public default dashboard is a fictional document-first adoption example with current execution unconfirmed; recorded-example.html is a separate synthetic recorded example.

Retain existing executable runtime smoke checks in check_current.py against the local reviewed runtime. Independently repeat --help, seven-writer demo setup, credential permissions and authenticated pilot checks from the downloaded public repository using scripts/verify_adoption.py. Packaging changes do not remove runtime coverage. Never interpret local stdin checks as native application hook delivery.

## Selective STE application release, 2026-10-05

Keep STE optional for technical wording. Updated ELI20, Handoff, analysis, independent-panel, improvement-loop and audit skill sources preserve their execution contracts. The skills guide includes bilingual application guidance; Handoff, expert analysis, ELI20 and PMS pages link the relevant use cases. The implementation ZIP includes the updated installed sources. AI PMS adoption and Live instructions preserve commands and constraints; dashboard changes clarify blocked status and separate cursor detail from human-readable connection status. No new API, hook, trust setting, completion rule or external model call is introduced. Archify installation is deferred.

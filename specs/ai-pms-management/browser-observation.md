# Central management v3 browser acceptance — 2026-10-02

Parent author observed actual Chrome UI; these are saved observations, not a browser automation replay.

## Production dashboard

URL: https://ai-pms-dashboard.vercel.app/

- Alice company outcome assignment showed Company → Alice, acceptance, goal version, and business outcome explicitly unobserved. Resolved blocker linked the failed and passing same-criterion attempts, owner and next action; loop improvement connected before/after evidence; Graphify freshness was current.
- Plan/check tab showed original requirement, plan version/reason, test design reason/excluded scope, command, file hashes and fail exit1 → pass exit0 with actor/environment/session and artifact/plan hashes.
- MCP/data tab showed server/tool, requested/completed records, logical database reference and explicit document reference; declared data and actual database audit remained distinct.
- Pasted invalid `{"schema_version":3}` through the visible JSON dialog. Error explicitly retained prior state; Alice detail name remained unchanged. Cancel closed the dialog.
- Dashboard at 390×844: viewport and document scroll width were both390; screenshot showed readable detail and horizontally scrollable tab strip. Console error log was empty.
- Clicked the production export button. Newly downloaded `ai-pms-snapshot (3).json` was parsed locally and exactly equalled the published v3 snapshot (five projects). The browser download-event wait had timed out previously, but the actual file outcome was verified independently.

## Local current-source observations before deployment

Company task/Bob showed open blocker, hypothesis/owner/next action and no resolved evidence. Personal/Carol remained independent with test-plan v2 changes, revalidation and stale graph. Goal-type filter selected the company-outcome project. Keyboard End selected the MCP tab. Valid minimal v3 JSON paste replaced the portfolio with one unknown project; malformed paste preserved the existing portfolio. Mobile overview and detail panels had no document-wide overflow.

## Public report and Kit

- https://ai-pms-dashboard.vercel.app/report.html: clicked all four example buttons. Visible completion state changed from implementation/no whole-project test → complete under configured criteria → revalidation after revision change → initial design. At390×844, document width was390.
- https://harness-kit.vercel.app/ai-pms.html and ai-pms-en.html: actual published pages explain company/personal goals, test design/provenance, blockers/improvements, optional Graphify and recorder commands. Korean page exposes dashboard/report/public-source links.
- Korean and English index pages expose implementation.zip and their respective reference-ko.zip/reference-en.zip links. `public-bytes.json` independently verifies exact production ZIP/page bytes against the canonical build, including the packaged v3 template and complete JSON field guide.

## Limits

Native file chooser is unverified; extension permission was not expanded. Paste/import validation and backend-to-UI parity were verified separately. The new production export file was verified as described above; earlier export observations remain historical evidence.

These observations use public synthetic sample users and local controlled execution fixtures. They do not demonstrate automatic collection from multiple real PCs, external provider execution, business outcome achievement or authenticated operation. Graph generation is optional and no global hook was installed.

## Documentation visibility follow-up — 2026-10-02

The previous canonical Kit release label incorrectly remained2026-09-30; the GitHub landing README did not highlight v3. Corrected the release label to2026-10-02, added a bilingual first-section change summary and direct template/field-guide/recorder/ZIP links, and updated the public README entry points. Actual Chrome reload of the public Kit page showed the new update section and field-guide link. Existing open tabs retain their old loaded DOM until refreshed.

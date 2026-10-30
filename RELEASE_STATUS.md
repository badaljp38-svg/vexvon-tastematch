# TasteMatch release receipt — October 30, 2026

## Published artifacts
- Application: https://vexvon-tastematch.vercel.app
- Source: https://github.com/badaljp38-svg/vexvon-tastematch
- License: MIT, detected by GitHub
- Version: 0.6.0
- Runtime source commit: 3526f9afd039f3ecaf12405caad3982d3302221e
- Submission story commit: b4619ba7889c1f4f75594ac6271e8a834c87cb15
- Vercel production deployment: dpl_PpWBXXxo3VZ6u1roXXMXnxx3AgxR — READY
- Deployment URL: https://vexvon-tastematch-6ztyhkxqf-badaljp38-4542.vercel.app
- Hosting account: badaljp38-4542, existing Hobby plan
- This release was uploaded as source files. Automatic Git deployment linking has not been configured.

## Verification
- 21 unit and HTTP tests passed; Qloo upstream responses in these tests are fixtures.
- JavaScript syntax check passed.
- Anonymous HTTP GET checks: app, status, OpenAPI and JavaScript returned 200.
- Hosted Search returned 503 key_missing. Hosted discovery returned 400 for a fabricated ID and 503 for a valid-format fixture ID without a credential.
- Desktop browser: labeled sample loaded; saved one item, skipped one, requested alternatives and changed from places to books.
- Mobile viewport check: document width matched viewport width; controls remained visible without horizontal overflow.
- No application JavaScript exception was observed during the checked sample interactions. An unrelated installed browser extension reported a native-host error.
- Download control enables after saving; file contents are produced by reviewed client code, but a completed browser download was not separately verified.

## Devpost
- Project: Vexvon TasteMatch
- Project page: https://devpost.com/software/vexvon-tastematch
- Submission: 1272234
- Saved status: Draft, 4/5 steps done
- Team, project overview, project story, technology tags, demo/source links and additional information are saved.
- Preview confirmed the project story and both links, and showed “Incomplete submission.”
- The rules/terms checkbox was left unchecked. Submit project was not pressed.
- Optional thumbnail upload was not confirmed; the browser disconnected during that attempt.
- No submission receipt exists yet.

## Remaining work
1. Configure the organizer-issued QLOO_API_KEY privately on the TasteMatch server runtime and redeploy.
2. Verify live Search, confirmed entity selection, Insights recommendations and exclusion refinement. Record only sanitized evidence.
3. Update the README and submission story to reflect the actual live-validation outcome.
4. Review the Devpost entry, confirm the owner's agreement to the Official Rules and Devpost Terms, and submit before October 30, 2026 at 8:45 PM PDT.
5. Save the actual submission receipt. Until then this is not a completed competition entry.

The fictional sample is not Qloo evidence. No paid services were purchased and no live API success is claimed.

# Vexvon TasteMatch

**Follow your taste across culture.** TasteMatch turns a few confirmed cultural favorites into a shortlist of films, artists, books, places or destinations. It provides two bounded Qloo tools for an AI assistant, plus a standalone interface for people who want to explore directly.

## Current release: 0.6.0

The real Qloo Search → entity confirmation → Insights adapter is implemented. **Organizer-issued API access is still pending, so live API validation has not been completed.** The interface includes an explicitly fictional sample. Sample results are never substituted into a failed live request and are not evidence of live Qloo integration.

No autonomous LLM, paid model service, existing assistant connection or production customer adoption is claimed. The agent-facing component is a documented tool API. An assistant can choose when to call it; the web interface uses a user-directed workflow.

## What you can do

1. Search a named favorite in one category. Review the returned name and distinguishing metadata; confirm the exact entity.
2. Add up to five favorites, choose another category and optionally a city for places.
3. Request Qloo Insights using those entity IDs. Inspect source IDs and the query trace.
4. Save promising discoveries, skip others and request alternatives with explicit exclusions.
5. Download a text shortlist containing source labels and query provenance. Selections stay in the current tab and disappear on reset or reload.

This is designed for cultural discovery and early concierge research. It does not check opening hours, availability, travel suitability or an individual's likely behavior. Qloo's aggregate affinities are not individual probabilities. No comparison claiming improved accuracy over an LLM has been measured.

## Run locally

Python 3.12+; no third-party dependencies:

```sh
python server.py
```

Open `http://127.0.0.1:8000`. Without a key, the interface works in the explicitly labeled sample mode; live requests return an actionable error.

For live access, configure `QLOO_API_KEY` privately in the runtime environment. Never commit or paste the credential into source, screenshots or the browser app. The server uses only `https://hackathon.api.qloo.com`. `.env.example` documents names; the server does not automatically load `.env` files. The obsolete v0.5 unverified-adapter switch has been removed.

## Deploy to Vercel

Import this repository as an **Other** project. `api/index.py` exports the standard-library HTTP handler, and `vercel.json` routes requests to it. Configure `QLOO_API_KEY` as an encrypted/sensitive server environment variable and redeploy. Use the production URL for judge access. Do not enable a paid plan for this prototype.

Alternatively, build the supplied Dockerfile, inject the environment at runtime and map port 8000. Docker binds to `0.0.0.0`; the direct local server defaults to loopback.

## Use as agent tools

OpenAPI 3.1 schema: `GET /api/openapi.json`.

- `POST /api/search`: `{"query":"Spirited Away","category":"urn:entity:movie"}`
- `POST /api/recommend`: `{"seeds":["<confirmed entity UUID>"],"category":"urn:entity:book","exclude":[]}`
- `GET /api/status`: version and configuration status only. A configured key does **not** mean a successful live call.

Tool policy for a calling assistant:

1. Search named cultural favorites. Do not send personal records, account credentials or sensitive attributes.
2. Ask the user to disambiguate matches; never invent an entity ID.
3. Call discovery with confirmed IDs. Preserve the returned provenance and distinguish ranking from certainty.
4. After feedback, request alternatives with skipped IDs. Stop when the user has a shortlist, there are no usable results, or an error occurs. Do not retry automatically on authentication/rate-limit errors.

One search or discovery invocation makes at most one upstream request. The server caps result counts and input sizes, uses a 12-second upstream timeout, caches up to 128 responses for five minutes and permits at most 30 uncached requests per minute per running process. **This in-memory limit is not a deployment-wide quota**, especially on serverless hosts. Organizer account limits still apply; a larger public rollout requires a shared limit store. No background polling, bulk scraping or credential fallback is implemented.

## Validation

```sh
python -m unittest discover -s tests -v
node --check static/app.js
```

21 unit/HTTP tests cover entity resolution, request parameters, exclusions, Unicode names, response shapes, error handling, credential handling, redirects, cache behavior, invalid inputs, protected file paths and the search-to-recommend contract. Upstream tests use fixtures. They do not demonstrate live Qloo access.

Before submitting: configure the event key, run a live search and discovery, verify the public URL end to end, and obtain the Devpost submission receipt. A fictional sample alone does not satisfy the hackathon's functional Qloo requirement.

## Implementation and sources

- Python standard library backend; plain HTML, CSS and JavaScript frontend.
- No third-party frontend assets, tracking, user database, paid model dependency or private VIK OS code.
- Qloo data is returned by the provider at runtime; the MIT license covers this project's code, not Qloo's data or trademarks.
- Built with AI coding assistance under the project owner's direction.

Official references used for the adapter:

- [Qloo entity search](https://github.com/qloo/docs-public/blob/main/reference/get-search.md)
- [Qloo Insights parameters](https://github.com/qloo/docs-public/blob/main/reference/insights-api-deep-dive.md)
- [Qloo Insights response example](https://github.com/qloo/docs-public/blob/main/reference/basic-insights-use-case.md)
- [Event access and limits](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md)
- [Hackathon rules](https://qloo.devpost.com/rules)

## License

[MIT](LICENSE), copyright 2026 Badal Patel.

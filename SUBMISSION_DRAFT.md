## Inspiration
A person's taste rarely fits one category. A favorite film, artist or book can be a better starting point for a thoughtful recommendation than another generic “top ten” list. Vexvon TasteMatch explores that connection for curious people and, eventually, concierge assistants.

## What it does
TasteMatch turns confirmed cultural favorites into an editable shortlist across films, music artists, books, places and destinations.

The workflow is explicit:
1. Search Qloo for a favorite and confirm the exact entity.
2. Select up to five favorites, choose a discovery category and optionally a city for places.
3. Request Qloo Insights with those entity IDs.
4. Inspect the results and provenance, save promising discoveries, skip others and request alternatives.
5. Download a shortlist with source labels and query provenance.

The agent-facing component is a pair of bounded tools described by an OpenAPI 3.1 schema. An assistant can resolve an entity and request cross-domain recommendations without guessing IDs or generating an unsupported list. The standalone website provides the same capabilities through a user-directed interface. No autonomous LLM or pre-existing assistant integration is claimed.

## How Qloo is used
The server first calls Qloo Search. Confirmed entity UUIDs become the signal.interests.entities input to Qloo Insights. Discovery also uses filter.type, optional filter.location.query and filter.exclude.entities for skipped items and existing favorites.

Results retain Qloo entity IDs and supplied descriptions. Ranking is preserved; missing scores and explanations are not invented. Qloo's aggregate cultural affinities are not treated as individual probabilities.

Without Qloo, live discovery cannot return recommendations. The separately labeled fictional sample only demonstrates the interface.

## How we built it
Python's standard library powers the backend. Plain HTML, CSS and JavaScript provide a responsive interface. Vercel hosts the public application. The public GitHub repository contains the complete source, reproducible instructions, tests and an MIT license.

The server keeps the API credential out of the browser, allows only the event API host, rejects redirects, bounds inputs and response sizes, and applies a timeout. Each tool invocation makes at most one upstream call. A small, short-lived response cache reduces repeated calls. The prototype's request limit is per process, not a shared deployment-wide quota.

The project was developed with AI coding assistance under Badal Patel's direction.

## Challenges and what we learned
The earlier scaffold passed free text to an endpoint expecting structured Qloo signals. Replacing that shortcut with search, user confirmation and entity-ID-based discovery was the central integration change.

Another challenge is showing useful provenance without inventing an explanation for every cultural connection. The interface separates provider-supplied information, user choices and clearly fictional sample content.

## Validation and current limitation
The application is publicly deployed. Twenty-one unit and HTTP tests pass, including search-to-discovery contracts, exclusion handling, response parsing, authentication and rate-limit errors, credential handling and invalid input. These upstream tests use fixtures, not live Qloo responses. Hosted routes, sample saving, skipping, cross-category changes and the missing-key response have been checked.

**The organizer-issued Qloo API key is still pending. Live Qloo validation is therefore not complete, and the current sample must not be mistaken for a functional Qloo demonstration.** The application reports this explicitly. This draft will need the event key and a successful live end-to-end check before it can meet the hackathon's functional integration requirement.

## What's next
Configure the event-issued key and verify live search, discovery and refinement. Then evaluate discovery quality with real users, connect a calling assistant to the documented tools and add a shared quota guard before a wider rollout.

## Links
- App: https://vexvon-tastematch.vercel.app
- Source and MIT license: https://github.com/badaljp38-svg/vexvon-tastematch
- Agent tool specification: https://vexvon-tastematch.vercel.app/api/openapi.json

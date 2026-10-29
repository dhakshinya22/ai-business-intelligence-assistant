# AI-Assisted Development Notes

## AI tools used
- ChatGPT: architecture planning, code drafting, edge-case identification, test planning, and documentation assistance.
- Optional runtime LLM: configured through `OPENAI_API_KEY`; used only to classify a question into an approved analytics intent.

## How AI was used
AI assistance was used to break the assessment into data ingestion, database, API, question interpretation, UI, and testing tasks. The runtime LLM is not allowed to generate SQL. It only returns structured intent data. All calculations are performed by predefined SQL queries.

## Problems and debugging
During the first automated test run, the unsupported-question test treated the analytics response as if it were the parsed intent. The test failed with a KeyError. I corrected the test to assert the parser output separately from the analytics response, then reran the suite successfully: 7 tests passed.

## Improvements with one more day
- Add more flexible date-range and year filters.
- Add database migration/versioning and stronger duplicate-file handling.
- Add charts and exportable CSV reports.
- Add authentication, deployment, logging, and monitoring.
- Expand automated tests for malformed CSVs, empty datasets, and additional question phrasings.

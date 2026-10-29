# Mini AI Business Intelligence Assistant

A small Python application that answers natural-language questions about sales transactions using SQLite queries. It is built for the RSG AI-Assisted Development Challenge.

## Features

- Imports the supplied CSV into SQLite.
- Cleans/flags invalid rows and excludes them from revenue calculations.
- Supports total revenue, top product, monthly trend, top region, and two-month comparison.
- Uses an LLM to classify the question when `OPENAI_API_KEY` is configured.
- Uses a deterministic rule-based fallback when no API key is configured.
- Executes only predefined, read-only analytical SQL. The LLM never writes or executes SQL.
- FastAPI backend, Streamlit UI, and Pytest tests.

## Revenue definition and data-quality policy

`revenue = quantity * unit_price - discount_amount`

Only rows with status `Completed`, a valid date, positive quantity, non-negative discount, and non-negative non-null unit price are included. Returned transactions, zero/non-positive quantities, and missing/invalid prices are retained in the database with `is_valid = 0` and an `exclusion_reason`, but excluded from analytics.

For the supplied CSV: 51 rows loaded, 48 valid rows, 3 excluded rows. Expected total revenue is ₹14,39,200.

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

The LLM is optional. To enable LLM-based interpretation, add your API key to `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Without a key, the application uses its local rule-based question interpreter. Calculations are always performed by SQL, not by the LLM.

## Run

Open two terminals in the project folder.

Terminal 1 — backend:

```bash
uvicorn main:app --reload
```

Backend docs: http://127.0.0.1:8000/docs

Terminal 2 — frontend:

```bash
streamlit run streamlit_app.py
```

Open the Streamlit URL shown in the terminal (normally http://localhost:8501).

On first backend startup, the CSV is imported into `sales.db`. To reload the CSV after replacing it, call `POST /reload-data` from `/docs`.

## API

`POST /ask`

Request:

```json
{"question": "Which product generated the highest revenue?"}
```

The response contains `success`, `title`, `answer`, `supporting_data`, `calculation`, and `question_interpreter`.

`GET /health` checks backend availability.

## Architecture

```text
CSV file
   |
   v
Pandas validation and cleaning
   |
   v
SQLite sales table (validity flag + exclusion reason)
   |
User question --> Streamlit UI --> FastAPI /ask
                                  |
                                  v
                       Question interpreter
                       (LLM JSON intent or rules)
                                  |
                                  v
                       Allow-listed analytics
                       (parameterized SQL)
                                  |
                                  v
                       Structured JSON answer
                                  |
                                  v
                       Streamlit answer + figures
```

## Safety and reliability

- The LLM returns an intent, not SQL.
- The intent must match a fixed allow-list.
- SQL statements are predefined and read-only.
- Month filters use SQL parameters.
- Invalid/unsupported questions return a clear error.
- Database loading records why a row was excluded.
- LLM/API failures fall back to the local parser.

## Tests

```bash
pytest -q
```

Tests cover total revenue, top product, monthly trend, top region, month comparison, unsupported questions, and invalid-row exclusion.

## Known limitations

- The rule-based fallback supports common English phrasings, not every possible wording.
- The LLM mode requires an API key and internet access.
- The sample dataset contains dates from January to June 2026; questions for periods without data return zero or an empty trend.
- The current application uses one SQLite database and is intended as a small assessment project, not a production multi-user service.
- The comparison parser orders months chronologically; it is intended for the dataset's 2026 period.

## AI usage and development notes

This project uses ChatGPT as an AI coding and design assistant to help plan the architecture, draft implementation code, identify edge cases, and prepare tests/documentation. The optional LLM integration is limited to classifying the user's question into a supported intent. SQL performs all numerical calculations.

Before submission, the developer should run the tests, manually try all example questions, inspect the generated SQL logic, and be prepared to explain and modify each module. Add a truthful note here about any debugging issues encountered during your own run and how you resolved them.

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from data_loader import load_csv
from question_parser import parse_question
from analytics import answer_question

app = FastAPI(title="Mini AI Business Intelligence Assistant", version="1.0.0")

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)

@app.on_event("startup")
def startup():
    db_path = os.getenv("DATABASE_PATH", "sales.db")
    csv_path = os.getenv("CSV_PATH", "sales_data.csv")
    if not Path(db_path).exists():
        load_csv(csv_path, db_path)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    parsed, mode = parse_question(question)
    result = answer_question(question, parsed, mode)
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error", "Unsupported question."))
    return result

@app.post("/reload-data")
def reload_data():
    try:
        return load_csv()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not reload data: {exc}")

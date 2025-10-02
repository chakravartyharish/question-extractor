#!/usr/bin/env python3
r"""
NEET 2024 Physics Question Extractor and Structuring Pipeline

- Extract raw text from the NEET_2024_Physics.pdf using PyMuPDF
- Parse question blocks using regex r'(\d+)\.\s+(.*?)(?=\d+\.|$)'
- For each question, call Perplexity (sonar model) to structure data according to JSON schema
- Validate outputs using jsonschema
- Write final file neet_2024_physics.json with metadata
"""

import json
import re
import time
from pathlib import Path

import requests
import fitz  # PyMuPDF
from jsonschema import Draft7Validator, ValidationError

# Perplexity API configuration
PPLX_API_KEY = os.getenv('PERPLEXITY_API_KEY')  # Load from environment
PPLX_ENDPOINT = "https://api.perplexity.ai/chat/completions"
PPLX_MODEL = "sonar"  # Updated to current valid model (Feb 2025)

# File locations
PDF_PATH = Path("/home/harish/Desktop/neet-learning-platform/NEET_2024_Physics.pdf")
OUTPUT_PATH = Path("/home/harish/Desktop/NEET2025/question_extractor/neet_2024_physics.json")

# Rate limiting and retry
RATE_LIMIT_DELAY = 1.0   # 1 second between calls
ERROR_DELAY = 5.0        # 5 seconds on error
MAX_RETRIES = 5

# Complete NEET Questions Database JSON Schema
NEET_DB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "NEET Questions Database Schema",
    "description": "Schema for NEET exam questions with detailed solutions and metadata",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "lastUpdated": {"type": "string", "format": "date-time"},
                "totalQuestions": {"type": "integer", "minimum": 0},
                "subject": {"type": "string", "enum": ["Physics", "Chemistry", "Biology"]},
                "yearRange": {"type": "string", "pattern": "^\\d{4}-\\d{4}$"}
            },
            "required": ["version", "lastUpdated", "totalQuestions", "subject", "yearRange"]
        },
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^neet_\\d{4}_[a-z]{3}_\\d{3}$"},
                    "questionNumber": {"type": "integer", "minimum": 1},
                    "examInfo": {
                        "type": "object",
                        "properties": {
                            "year": {"type": "integer", "minimum": 1988, "maximum": 2030},
                            "examType": {"type": "string", "enum": ["NEET", "AIPMT", "AIIMS", "JIPMER"]},
                            "paperCode": {"type": "string"},
                            "setCode": {"type": "string"}
                        },
                        "required": ["year", "examType", "paperCode"]
                    },
                    "title": {"type": "string", "minLength": 10},
                    "questionText": {"type": "string", "minLength": 20},
                    "questionImages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "format": "uri-reference"},
                                "altText": {"type": "string", "minLength": 5},
                                "caption": {"type": "string"},
                                "position": {"type": "string", "enum": ["below-question", "inline", "after-steps"]},
                                "width": {"type": "integer", "minimum": 100},
                                "height": {"type": "integer", "minimum": 100}
                            },
                            "required": ["url", "altText", "caption", "position"]
                        }
                    },
                    "options": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "enum": ["A", "B", "C", "D"]},
                                "text": {"type": "string", "minLength": 1},
                                "isCorrect": {"type": "boolean"},
                                "analysis": {"type": "string", "minLength": 10}
                            },
                            "required": ["id", "text", "isCorrect", "analysis"]
                        }
                    },
                    "correctOption": {"type": "string", "enum": ["A", "B", "C", "D"]},
                    "classification": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "enum": ["Physics", "Chemistry", "Biology"]},
                            "chapter": {"type": "string", "minLength": 2},
                            "topic": {"type": "string", "minLength": 2},
                            "subtopic": {"type": "string"},
                            "ncertClass": {"type": "integer", "enum": [11, 12]},
                            "difficulty": {"type": "string", "enum": ["Easy", "Medium", "Hard"]},
                            "estimatedTime": {"type": "integer", "minimum": 1, "maximum": 10},
                            "conceptTags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1
                            },
                            "bloomsLevel": {"type": "string", "enum": ["remember", "understand", "apply", "analyze", "evaluate", "create"]}
                        },
                        "required": ["subject", "chapter", "topic", "ncertClass", "difficulty", "estimatedTime", "conceptTags", "bloomsLevel"]
                    },
                    "stepByStep": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "minLength": 5},
                                "content": {"type": "string", "minLength": 20},
                                "formula": {"type": "string"},
                                "insight": {"type": "string"},
                                "stepImages": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string", "format": "uri-reference"},
                                            "altText": {"type": "string"},
                                            "caption": {"type": "string"},
                                            "position": {"type": "string", "enum": ["inline", "below-step"]},
                                            "width": {"type": "integer"},
                                            "height": {"type": "integer"}
                                        },
                                        "required": ["url", "altText", "caption"]
                                    }
                                }
                            },
                            "required": ["title", "content"]
                        }
                    },
                    "solutionImages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "format": "uri-reference"},
                                "altText": {"type": "string"},
                                "caption": {"type": "string"},
                                "position": {"type": "string", "enum": ["after-steps", "inline"]},
                                "width": {"type": "integer"},
                                "height": {"type": "integer"}
                            },
                            "required": ["url", "altText", "caption", "position"]
                        }
                    },
                    "quickMethod": {
                        "type": "object",
                        "properties": {
                            "trick": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "steps": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["title", "steps"]
                            },
                            "timeManagement": {
                                "type": "object",
                                "properties": {
                                    "totalTime": {"type": "string", "pattern": "^\\d+\\s+(min|sec)$"}
                                },
                                "required": ["totalTime"]
                            }
                        }
                    },
                    "premiumContentId": {"type": "string"}
                },
                "required": [
                    "id", "questionNumber", "examInfo", "title", "questionText",
                    "options", "correctOption", "classification", "stepByStep"
                ]
            }
        }
    },
    "required": ["metadata", "questions"]
}

QUESTION_PATTERN = re.compile(r'(\d+)\.\s+(.*?)(?=\d+\.|$)', re.S)


def process_pdf(pdf_path: Path) -> str:
    """Extract all text from PDF using PyMuPDF."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path}")
    chunks = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            chunks.append(page.get_text())
    return "\n".join(chunks)


def extract_questions(raw_text: str):
    """
    Extract questions using the given regex pattern.
    Returns a list of dicts: [{"number": int, "text": str}, ...]
    """
    results = []
    for match in QUESTION_PATTERN.finditer(raw_text):
        try:
            number = int(match.group(1))
        except Exception:
            # Fallback if conversion fails
            number = match.group(1)
        text = match.group(2).strip()
        results.append({"number": number, "text": text})
    return results


def extract_json_from_text(text: str):
    """
    Extract the first JSON object from a text block.
    Tries raw braces and fenced code blocks.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        snippet = text[start:end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            s = p.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    return json.loads(s)
                except Exception:
                    continue
    raise ValueError("Could not parse JSON from model response")


def call_perplexity(question: dict, schema: dict) -> dict:
    """
    Sends the question to Perplexity with instructions to produce JSON
    conforming to the provided schema. Implements retry and rate limiting.
    """
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json"
    }

    # Create a comprehensive prompt
    user_prompt = f"""Convert this NEET 2024 Physics question into structured JSON following this schema:

Question {question["number"]}: {question["text"]}

Required JSON structure:
- id: Format as "neet_2024_phy_{question['number']:03d}"
- questionNumber: {question['number']}
- examInfo: {{year: 2024, examType: "NEET", paperCode: "2024-PHY"}}
- title: Brief descriptive title
- questionText: The full question text
- options: Array of 4 objects with id (A-D), text, isCorrect (boolean), analysis
- correctOption: "A", "B", "C", or "D"
- classification: {{
    subject: "Physics",
    chapter: (identify chapter),
    topic: (identify topic),
    subtopic: (if applicable),
    ncertClass: 11 or 12,
    difficulty: "Easy", "Medium", or "Hard",
    estimatedTime: 1-10 minutes,
    conceptTags: [list of concepts],
    bloomsLevel: one of "remember", "understand", "apply", "analyze", "evaluate", "create"
  }}
- stepByStep: Array of solution steps with title and content (minimum)
- quickMethod: Optional shortcut approach
- questionImages, solutionImages, stepImages: Use empty arrays [] if no images

Return ONLY valid JSON, no additional text."""

    payload = {
        "model": PPLX_MODEL,
        "messages": [
            {"role": "system", "content": "You are a NEET question formatter. Return only valid JSON matching the schema exactly."},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(PPLX_ENDPOINT, headers=headers, json=payload, timeout=90)
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            obj = extract_json_from_text(content)
            if isinstance(obj, dict):
                # Ensure essential fields exist
                obj.setdefault("id", f"neet_2024_phy_{question['number']:03d}")
                obj.setdefault("questionNumber", question["number"])
                obj.setdefault("questionText", question["text"])
                return obj
            raise ValueError("Model returned non-dict JSON")
        except Exception as e:
            last_error = e
            print(f"[Perplexity] Q{question['number']} attempt {attempt} failed: {e}")
            time.sleep(ERROR_DELAY)
        finally:
            time.sleep(RATE_LIMIT_DELAY)

    raise RuntimeError(f"Perplexity call failed after {MAX_RETRIES} attempts: {last_error}")


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Reading PDF: {PDF_PATH}")
    raw_text = process_pdf(PDF_PATH)
    print("Extracting question candidates...")
    questions = extract_questions(raw_text)
    print(f"Found {len(questions)} question candidates.")

    results = []
    failures = []

    for idx, q in enumerate(questions, 1):
        print(f"\nProcessing question {idx}/{len(questions)} (Q{q.get('number')})...")
        try:
            item = call_perplexity(q, NEET_DB_SCHEMA)
            results.append(item)
            print(f"✓ Successfully structured Q{q.get('number')}")
        except Exception as e:
            print(f"✗ Error structuring Q{q.get('number')}: {e}")
            failures.append(q.get("number"))
            # Minimal fallback on failure
            results.append({
                "id": f"neet_2024_phy_{q.get('number', 0):03d}",
                "questionNumber": q.get("number"),
                "examInfo": {"year": 2024, "examType": "NEET", "paperCode": "2024-PHY"},
                "title": f"Question {q.get('number')}",
                "questionText": q.get("text"),
                "options": [],
                "correctOption": "A",
                "classification": {
                    "subject": "Physics",
                    "chapter": "Unknown",
                    "topic": "Unknown",
                    "ncertClass": 12,
                    "difficulty": "Medium",
                    "estimatedTime": 3,
                    "conceptTags": ["physics"],
                    "bloomsLevel": "understand"
                },
                "stepByStep": [{"title": "Solution", "content": "Extraction failed"}]
            })

    dataset = {
        "metadata": {
            "version": "1.0",
            "lastUpdated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "totalQuestions": len(results),
            "subject": "Physics",
            "yearRange": "2024-2024"
        },
        "questions": results
    }

    print("\n" + "="*60)
    print("Validating dataset against schema...")
    try:
        Draft7Validator(NEET_DB_SCHEMA).validate(dataset)
        print("✓ Schema validation passed.")
    except ValidationError as ve:
        print("✗ Schema validation error (non-blocking):")
        print(f"  Path: {list(ve.path)}")
        print(f"  Message: {ve.message}")

    print(f"\nWriting output JSON: {OUTPUT_PATH}")
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print("="*60)
    print(f"✓ Done! Total items: {len(results)}. Failures: {len(failures)}")
    if failures:
        print(f"Failed question numbers: {failures[:20]}" + (" ..." if len(failures) > 20 else ""))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Configuration module for NEET Question Extractor.
Loads settings from environment variables using python-dotenv.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for Anthropic API and model settings."""
    
    api_key: str
    base_url: str
    anthropic_version: str
    model_name: str
    temperature: float
    max_tokens: int
    rate_limit_delay: float
    error_delay: float
    max_retries: int
    
    def __post_init__(self):
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Create a .env file and add your API key."
            )


@dataclass(frozen=True)
class PathConfig:
    """Configuration for file paths."""
    
    pdf_path: Path
    output_path: Path
    batches_dir: Path
    logs_dir: Path
    progress_file: Path
    failed_log: Path
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Invalid content patterns for filtering out exam instructions
INVALID_PATTERNS = [
    re.compile(r'test.*duration.*hours', re.I),
    re.compile(r'blue.*black.*ball.*point.*pen', re.I),
    re.compile(r'rough.*work', re.I),
    re.compile(r'admit.*card', re.I),
    re.compile(r'OMR.*sheet', re.I),
    re.compile(r'candidates.*governed', re.I),
    re.compile(r'marking.*scheme.*\d+.*marks', re.I),
    re.compile(r'general.*instructions', re.I),
    re.compile(r'use.*HB.*pencil', re.I),
    re.compile(r'do.*not.*fold', re.I),
    re.compile(r'follow.*instructions', re.I),
    re.compile(r'negative.*marking.*deduct', re.I),
    re.compile(r'test.*booklet.*contains', re.I),
    re.compile(r'maximum.*marks.*are', re.I),
    re.compile(r'read.*the.*following.*instructions', re.I),
    re.compile(r'darken.*the.*correct.*choice', re.I),
]

# Section headers for identifying Physics section
SECTION_START_PATTERNS = [
    re.compile(r'PHYSICS', re.I),
    re.compile(r'SECTION.*A.*PHYSICS', re.I),
    re.compile(r'Physics\s+Section', re.I),
    re.compile(r'PART.*A.*PHYSICS', re.I),
]

SECTION_END_PATTERNS = [
    re.compile(r'CHEMISTRY', re.I),
    re.compile(r'BIOLOGY', re.I),
    re.compile(r'BOTANY', re.I),
    re.compile(r'ZOOLOGY', re.I),
    re.compile(r'SECTION.*B', re.I),
]

# Enhanced regex patterns for NEET question extraction
# Matches: "123. Question text here"
QUESTION_PATTERN = re.compile(
    r'(\d+)\.\s+(.*?)(?=\s*\(\d\)|\n\d+\.|\Z)',
    re.DOTALL
)

# Matches: "(1) Option text" or "(2) Option text"
OPTION_PATTERN = re.compile(
    r'\(([1-4])\)\s*(.+?)(?=\s*\(\d\)|\n\d+\.|\Z)',
    re.DOTALL
)

# Placeholder patterns to detect in validation
PLACEHOLDER_PATTERNS = [
    r'placeholder',
    r'text\s+here',
    r'option\s+[A-D]\s+text',
    r'sample.*question',
    r'analysis\s+not\s+provided',
    r'chapter\s+name\s+here',
    r'topic\s+name\s+here',
]


def get_model_config() -> ModelConfig:
    """Load model configuration from environment variables."""
    return ModelConfig(
        api_key=os.getenv('ANTHROPIC_API_KEY', ''),
        base_url=os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
        anthropic_version=os.getenv('ANTHROPIC_VERSION', '2023-06-01'),
        model_name=os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
        temperature=float(os.getenv('TEMPERATURE', '0')),
        max_tokens=int(os.getenv('MAX_TOKENS', '4000')),
        rate_limit_delay=float(os.getenv('RATE_LIMIT_DELAY', '1.0')),
        error_delay=float(os.getenv('ERROR_DELAY', '5.0')),
        max_retries=int(os.getenv('MAX_RETRIES', '5')),
    )


def get_path_config(
    pdf_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> PathConfig:
    """Load path configuration with optional overrides."""
    base_dir = Path(__file__).parent
    
    default_pdf = Path("/home/harish/Desktop/neet-learning-platform/NEET_2024_Physics.pdf")
    default_output = base_dir / "neet_2024_physics.json"
    
    config = PathConfig(
        pdf_path=Path(pdf_path) if pdf_path else Path(os.getenv('PDF_PATH', str(default_pdf))),
        output_path=Path(output_path) if output_path else Path(os.getenv('OUTPUT_PATH', str(default_output))),
        batches_dir=base_dir / "batches",
        logs_dir=base_dir / "logs",
        progress_file=base_dir / "processing_progress.json",
        failed_log=base_dir / "failed_questions.log",
    )
    
    config.ensure_directories()
    return config


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
                    "questionImages": {"type": "array"},
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
                                "insight": {"type": "string"}
                            },
                            "required": ["title", "content"]
                        }
                    },
                    "solutionImages": {"type": "array"},
                    "quickMethod": {"type": "object"}
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

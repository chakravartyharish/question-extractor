#!/usr/bin/env python3
"""
PDF extraction module for NEET Question Extractor.
Extracts Physics section and parses questions with options.
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import fitz  # PyMuPDF

from config import (
    SECTION_START_PATTERNS,
    SECTION_END_PATTERNS,
    QUESTION_PATTERN,
    OPTION_PATTERN
)
from question_validator import is_valid_physics_question


def extract_text_from_pdf(pdf_path: Path) -> List[str]:
    """
    Extract text from each page of PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of text strings, one per page
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    pages = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            # Keep original formatting - don't normalize too aggressively
            pages.append(text)
    
    return pages


def find_section_bounds(pages: List[str]) -> Tuple[int, int]:
    """
    Find start and end page indices for Physics section.
    
    Args:
        pages: List of page texts
        
    Returns:
        Tuple of (start_page, end_page) indices (inclusive)
    """
    start_page = -1
    end_page = len(pages)
    
    # Find Physics section start
    for i, page_text in enumerate(pages):
        for pattern in SECTION_START_PATTERNS:
            if pattern.search(page_text):
                start_page = i
                break
        if start_page >= 0:
            break
    
    if start_page < 0:
        # Fallback: assume Physics starts early
        start_page = 0
    
    # Find Physics section end (where Chemistry/Biology starts)
    for i in range(start_page + 1, len(pages)):
        for pattern in SECTION_END_PATTERNS:
            if pattern.search(pages[i]):
                end_page = i
                break
        if end_page < len(pages):
            break
    
    return start_page, end_page


def normalize_text(text: str) -> str:
    """Normalize text for better parsing."""
    # Fix common OCR issues
    text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    # Normalize parentheses
    text = text.replace('（', '(').replace('）', ')')
    # Only normalize horizontal whitespace, preserve newlines
    text = re.sub(r'[ \t]+', ' ', text)
    return text


def parse_options(text: str) -> List[Dict[str, str]]:
    """
    Parse options from question text.
    
    Args:
        text: Text containing options marked (1), (2), (3), (4)
        
    Returns:
        List of option dicts with 'id' and 'text' keys
    """
    options = []
    option_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
    
    matches = OPTION_PATTERN.findall(text)
    for num, opt_text in matches:
        if num in option_map:
            options.append({
                'id': option_map[num],
                'text': opt_text.strip()
            })
    
    # Ensure we have 4 options
    while len(options) < 4:
        options.append({
            'id': option_map[str(len(options) + 1)],
            'text': ''
        })
    
    return options[:4]


def extract_physics_questions_improved(pdf_path: Path) -> List[Dict]:
    """
    Extract Physics questions from PDF with correct answers.
    
    Args:
        pdf_path: Path to NEET PDF
        
    Returns:
        List of question dicts with number, text, options, and correct_answer
    """
    print(f"📄 Reading PDF: {pdf_path}")
    pages = extract_text_from_pdf(pdf_path)
    
    print(f"📑 Total pages: {len(pages)}")
    start_page, end_page = find_section_bounds(pages)
    print(f"🔍 Physics section: pages {start_page+1} to {end_page}")
    
    # Extract Physics section only
    physics_pages = pages[start_page:end_page]
    physics_text = '\n'.join(physics_pages)
    physics_text = normalize_text(physics_text)
    
    # Find where actual PHYSICS questions start (after instructions)
    physics_start_match = re.search(r'PHYSICS\s*\n', physics_text, re.IGNORECASE)
    if physics_start_match:
        physics_text = physics_text[physics_start_match.end():]
    
    print(f"📝 Extracting questions from {len(physics_text)} characters...")
    
    questions = []
    
    # Enhanced pattern that captures: NUMBER. QUESTION_TEXT (1) OPT1 (2) OPT2 (3) OPT3 (4) OPT4 Answer (X)
    pattern = re.compile(
        r'(\d+)\.\s*\n'  # Question number with newline
        r'(.*?)'  # Question text (non-greedy)
        r'\(1\)\s*(.*?)'  # Option 1
        r'\(2\)\s*(.*?)'  # Option 2  
        r'\(3\)\s*(.*?)'  # Option 3
        r'\(4\)\s*(.*?)'  # Option 4
        r'Answer\s*\((\d)\)',  # Answer
        re.DOTALL
    )
    
    # Map option numbers to letters
    num_to_letter = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
    
    matches = pattern.findall(physics_text)
    
    for match in matches:
        try:
            q_num, q_text, opt1, opt2, opt3, opt4, answer_idx = match
            
            number = int(q_num)
            
            # Clean up texts
            q_text = ' '.join(q_text.split())
            opt1 = ' '.join(opt1.split())
            opt2 = ' '.join(opt2.split())
            opt3 = ' '.join(opt3.split())
            opt4 = ' '.join(opt4.split())
            
            # Skip if question too short
            if len(q_text) < 20:
                print(f"  ⏭️  Skipping Q{number}: Question too short")
                continue
            
            # Map answer to letter
            correct_index = int(answer_idx)
            correct_answer = num_to_letter.get(answer_idx)
            
            if not correct_answer:
                print(f"  ⚠️  Q{number}: Invalid answer index {answer_idx}")
                continue
            
            options_dict = {
                'A': opt1,
                'B': opt2,
                'C': opt3,
                'D': opt4
            }
            
            questions.append({
                'number': number,
                'text': q_text,  # Full text
                'question_text': q_text,  # Clean question
                'options': options_dict,
                'correct_index': correct_index,
                'correct_answer': correct_answer,
                'has_answer': True
            })
            
            print(f"  ✅ Q{number}: Answer ({correct_index}) → {correct_answer}")
            
        except (ValueError, AttributeError) as e:
            print(f"  ⚠️  Error parsing question: {e}")
            continue
    
    print(f"✅ Extracted {len(questions)} valid Physics questions")
    with_answers = sum(1 for q in questions if q.get('has_answer'))
    print(f"✅ {with_answers} questions have answers from PDF")
    return questions


def extract_questions_simple(pdf_path: Path, max_questions: Optional[int] = None) -> List[Dict]:
    """
    Simplified extraction for testing - extracts all questions without filtering.
    
    Args:
        pdf_path: Path to PDF
        max_questions: Maximum number to extract (None for all)
        
    Returns:
        List of question dicts
    """
    pages = extract_text_from_pdf(pdf_path)
    all_text = '\n'.join(pages)
    all_text = normalize_text(all_text)
    
    questions = []
    matches = list(QUESTION_PATTERN.finditer(all_text))
    
    if max_questions:
        matches = matches[:max_questions]
    
    for match in matches:
        try:
            number = int(match.group(1))
            text = match.group(2).strip()
            options = parse_options(text)
            
            questions.append({
                'number': number,
                'text': text,
                'options': options,
                'raw_block': text
            })
        except:
            continue
    
    return questions

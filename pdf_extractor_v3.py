#!/usr/bin/env python3
"""
Enhanced PDF extraction module for NEET Question Extractor.
Extracts Physics section, questions with options, AND correct answers from PDF.
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import fitz  # PyMuPDF

from config import (
    SECTION_START_PATTERNS,
    SECTION_END_PATTERNS,
)


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
            # Normalize whitespace
            text = re.sub(r'[ \t]+', ' ', text)
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


def extract_physics_questions_with_answers(pdf_path: Path) -> List[Dict]:
    """
    Extract Physics questions from PDF WITH correct answers.
    
    This is the enhanced version that extracts:
    - Question number
    - Question text
    - Four options (1-4 in PDF, mapped to A-D)
    - Correct answer from "Answer (X)" line
    
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
    
    # Normalize text
    physics_text = physics_text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    physics_text = physics_text.replace('（', '(').replace('）', ')')
    
    print(f"📝 Extracting questions from {len(physics_text)} characters...")
    
    questions = []
    
    # Enhanced regex to capture question blocks with answers
    # Pattern: Question number -> question text -> options (1)-(4) -> Answer (X)
    question_block_pattern = re.compile(
        r'(\d+)\.\s*'  # Question number
        r'(.*?)'  # Question text (non-greedy)
        r'(?=\(\d\)|\nAnswer|\n\d+\.|\Z)',  # Stop at options or answer or next question
        re.DOTALL
    )
    
    # Option pattern: (1) text, (2) text, etc.
    option_pattern = re.compile(
        r'\(([1-4])\)\s*([^\(]*?)(?=\s*\([1-4]\)|Answer|Sol\.|$)',
        re.DOTALL
    )
    
    # Answer pattern: Answer (X) where X is 1-4
    answer_pattern = re.compile(
        r'Answer\s*\((\d)\)',
        re.IGNORECASE
    )
    
    # Map option numbers to letters
    num_to_letter = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
    
    # Find all question blocks
    matches = list(question_block_pattern.finditer(physics_text))
    
    for i, match in enumerate(matches):
        try:
            number = int(match.group(1))
            full_block = match.group(2).strip()
            
            # Skip if too short
            if len(full_block) < 20:
                continue
            
            # Find the end of this question block (start of next question or end of text)
            if i < len(matches) - 1:
                next_start = matches[i + 1].start()
                block_text = physics_text[match.start():next_start]
            else:
                block_text = physics_text[match.start():]
            
            # Extract options
            option_matches = option_pattern.findall(block_text)
            options_dict = {}
            
            for opt_num, opt_text in option_matches:
                opt_text = opt_text.strip()
                # Remove newlines and extra whitespace
                opt_text = ' '.join(opt_text.split())
                if opt_num in num_to_letter:
                    options_dict[num_to_letter[opt_num]] = opt_text
            
            # Must have exactly 4 options
            if len(options_dict) != 4:
                print(f"  ⚠️  Q{number}: Found {len(options_dict)} options, skipping")
                continue
            
            # Extract question text (remove options from it)
            question_text = full_block
            for opt_match in option_pattern.finditer(full_block):
                question_text = question_text.replace(opt_match.group(0), '')
            question_text = question_text.strip()
            question_text = ' '.join(question_text.split())  # Normalize whitespace
            
            # Extract correct answer
            answer_match = answer_pattern.search(block_text)
            correct_answer = None
            correct_index = None
            
            if answer_match:
                correct_index = int(answer_match.group(1))
                if 1 <= correct_index <= 4:
                    correct_answer = num_to_letter[str(correct_index)]
                    print(f"  ✅ Q{number}: Answer ({correct_index}) → {correct_answer}")
                else:
                    print(f"  ⚠️  Q{number}: Invalid answer index {correct_index}")
            else:
                print(f"  ⚠️  Q{number}: No answer found in PDF")
            
            questions.append({
                'number': number,
                'question_text': question_text,
                'options': options_dict,
                'correct_index': correct_index,
                'correct_answer': correct_answer,
                'full_text': full_block,
                'has_answer': correct_answer is not None
            })
            
        except (ValueError, AttributeError) as e:
            print(f"  ⚠️  Error parsing question: {e}")
            continue
    
    print(f"✅ Extracted {len(questions)} Physics questions")
    with_answers = sum(1 for q in questions if q['has_answer'])
    print(f"✅ {with_answers} questions have answers from PDF")
    
    return questions

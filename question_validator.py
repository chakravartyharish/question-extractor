#!/usr/bin/env python3
"""
Question validation module for NEET Question Extractor.
Filters invalid content and validates question completeness.
"""

import re
from typing import Tuple, List

from config import INVALID_PATTERNS, PLACEHOLDER_PATTERNS


def is_valid_physics_question(text: str) -> bool:
    """
    Determine if text represents a valid physics question.
    
    Filters out exam instructions, general instructions, and non-physics content.
    
    Args:
        text: Question text to validate
        
    Returns:
        True if valid physics question, False otherwise
    """
    if not text or len(text.strip()) < 20:
        return False
    
    text_lower = text.lower()
    
    # Check against invalid patterns
    for pattern in INVALID_PATTERNS:
        if pattern.search(text):
            return False
    
    # Additional heuristic checks
    # Questions should have some substance
    words = text.split()
    if len(words) < 10:
        return False
    
    # Physics questions typically contain certain markers
    # but instructions don't have these
    has_question_markers = any(marker in text for marker in ['?', 'calculate', 'find', 'determine', 'if', 'when'])
    
    # Instructions often have imperative verbs
    instruction_verbs = ['read', 'fill', 'write', 'darken', 'use only', 'do not', 'ensure']
    starts_with_instruction = any(text_lower.strip().startswith(verb) for verb in instruction_verbs)
    
    if starts_with_instruction and not has_question_markers:
        return False
    
    return True


def validate_question_completeness(question: dict) -> Tuple[bool, List[str]]:
    """
    Validate that a structured question contains complete and valid data.
    
    Args:
        question: Structured question dictionary
        
    Returns:
        Tuple of (is_valid: bool, error_reasons: List[str])
    """
    errors = []
    
    # Check required fields exist
    required_fields = ['id', 'questionText', 'options', 'correctOption', 'classification']
    for field in required_fields:
        if field not in question:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate question text
    question_text = question.get('questionText', '')
    if len(question_text) < 50:
        errors.append(f"Question text too short: {len(question_text)} chars")
    
    # Check for placeholder content
    text_lower = question_text.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text_lower):
            errors.append(f"Found placeholder pattern: {pattern}")
            break
    
    # Validate options
    options = question.get('options', [])
    if len(options) != 4:
        errors.append(f"Expected 4 options, got {len(options)}")
    else:
        # Check each option
        option_ids = [opt.get('id') for opt in options]
        if set(option_ids) != {'A', 'B', 'C', 'D'}:
            errors.append(f"Invalid option IDs: {option_ids}")
        
        # Check for placeholder text in options
        for opt in options:
            opt_text = opt.get('text', '').lower()
            if 'text here' in opt_text or 'option' in opt_text and 'text' in opt_text:
                errors.append(f"Placeholder found in option {opt.get('id')}")
                break
    
    # Validate correct option
    correct_option = question.get('correctOption')
    if correct_option not in ['A', 'B', 'C', 'D']:
        errors.append(f"Invalid correctOption: {correct_option}")
    
    # Validate classification
    classification = question.get('classification', {})
    
    chapter = classification.get('chapter', '')
    if not chapter or chapter.lower() in ['unknown', 'chapter name here']:
        errors.append("Chapter is missing or placeholder")
    
    topic = classification.get('topic', '')
    if not topic or topic.lower() in ['unknown', 'topic name here']:
        errors.append("Topic is missing or placeholder")
    
    concept_tags = classification.get('conceptTags', [])
    if not concept_tags or len(concept_tags) < 2:
        errors.append(f"Insufficient concept tags: {len(concept_tags)}")
    elif any('concept' in str(tag).lower() and not tag.lower().startswith('concept') 
             for tag in concept_tags):
        errors.append("Placeholder concepts found")
    
    # Validate step by step solution
    steps = question.get('stepByStep', [])
    if not steps:
        errors.append("Missing stepByStep solution")
    elif len(steps) < 2:
        errors.append(f"Solution too brief: {len(steps)} steps")
    
    return len(errors) == 0, errors


def get_validation_summary(questions: List[dict]) -> dict:
    """
    Generate validation summary for a list of questions.
    
    Args:
        questions: List of structured questions
        
    Returns:
        Summary dictionary with counts and details
    """
    summary = {
        'total': len(questions),
        'valid': 0,
        'invalid': 0,
        'error_breakdown': {},
    }
    
    for q in questions:
        is_valid, errors = validate_question_completeness(q)
        if is_valid:
            summary['valid'] += 1
        else:
            summary['invalid'] += 1
            for error in errors:
                summary['error_breakdown'][error] = summary['error_breakdown'].get(error, 0) + 1
    
    return summary

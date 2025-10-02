#!/usr/bin/env python3
"""
Enhanced NEET Question Extractor with improved security, validation, and batch processing.

Major improvements:
- Secure API key management via environment variables
- Physics section detection and filtering
- Question validation and quality checks
- Batch processing with resume capability
- Cost tracking and monitoring
- Enhanced error handling and logging
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests
from jsonschema import Draft7Validator

from config import get_model_config, get_path_config, NEET_DB_SCHEMA
from pdf_extractor import extract_physics_questions_improved
from question_validator import is_valid_physics_question, validate_question_completeness
from cost_tracker import CostTracker


# Setup logging
def setup_logging(log_dir: Path):
    """Configure logging to file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def extract_json_from_response(text: str) -> dict:
    """Extract JSON from API response, handling code blocks and markdown."""
    # Try to find JSON object
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1 and start < end:
        json_str = text[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Try code blocks
    if '```' in text:
        parts = text.split('```')
        for part in parts:
            part = part.strip()
            if part.startswith('json'):
                part = part[4:].strip()
            if part.startswith('{') and part.endswith('}'):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue
    
    raise ValueError("Could not extract valid JSON from response")


def call_perplexity_api(
    question: dict,
    model_config,
    logger: logging.Logger,
    cost_tracker: CostTracker
) -> Optional[dict]:
    """
    Call Perplexity API to structure a question.
    
    Args:
        question: Raw question dict with number and text
        model_config: Model configuration
        logger: Logger instance
        cost_tracker: Cost tracking instance
        
    Returns:
        Structured question dict or None on failure
    """
    headers = {
        'Authorization': f'Bearer {model_config.api_key}',
        'Content-Type': 'application/json'
    }
    
    # Construct comprehensive prompt
    user_prompt = f"""You are a NEET question formatter. Convert this Physics question into structured JSON.

Question {question['number']}: {question.get('question_text', question['text'])}

EXTRACTED OPTIONS:
{json.dumps(question.get('options', []), indent=2)}

Return a JSON object with this EXACT structure:
{{
  "id": "neet_2024_phy_{question['number']:03d}",
  "questionNumber": {question['number']},
  "examInfo": {{
    "year": 2024,
    "examType": "NEET",
    "paperCode": "2024-PHY"
  }},
  "title": "Brief descriptive title (max 80 chars)",
  "questionText": "Full question text without options",
  "options": [
    {{
      "id": "A",
      "text": "Option A text",
      "isCorrect": true/false,
      "analysis": "Why this option is correct/incorrect"
    }},
    // ... 3 more options for B, C, D
  ],
  "correctOption": "A" or "B" or "C" or "D",
  "classification": {{
    "subject": "Physics",
    "chapter": "Specific chapter name from NCERT",
    "topic": "Specific topic",
    "subtopic": "If applicable",
    "ncertClass": 11 or 12,
    "difficulty": "Easy" or "Medium" or "Hard",
    "estimatedTime": 2-5 (minutes),
    "conceptTags": ["concept1", "concept2", "concept3"],
    "bloomsLevel": "remember"/"understand"/"apply"/"analyze"/"evaluate"/"create"
  }},
  "stepByStep": [
    {{
      "title": "Step 1: Understand the Problem",
      "content": "Detailed explanation",
      "formula": "F = ma (if applicable)",
      "insight": "Key insight for solving"
    }},
    // ... more steps
  ],
  "quickMethod": {{
    "trick": {{
      "title": "Quick approach title",
      "steps": ["step1", "step2"]
    }},
    "timeManagement": {{
      "totalTime": "2 min"
    }}
  }},
  "questionImages": [],
  "solutionImages": []
}}

CRITICAL REQUIREMENTS:
1. Identify the CORRECT answer based on physics principles
2. Provide detailed analysis for EACH option
3. Use real NCERT chapter names (e.g., "Electrostatics", "Motion in a Plane")
4. Provide at least 3-4 solution steps
5. Include 3-5 relevant concept tags
6. NO placeholders like "text here" or "chapter name here"

Return ONLY valid JSON. No additional text."""

    payload = {
        'model': model_config.model_name,
        'messages': [
            {
                'role': 'system',
                'content': 'You are an expert NEET Physics question analyzer. Return only valid JSON matching the schema exactly. Use your physics knowledge to identify correct answers and provide detailed solutions.'
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ],
        'temperature': model_config.temperature,
        'max_tokens': model_config.max_tokens
    }
    
    last_error = None
    for attempt in range(1, model_config.max_retries + 1):
        try:
            logger.info(f"  API call attempt {attempt}/{model_config.max_retries}")
            
            response = requests.post(
                f"{model_config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code >= 400:
                error_msg = response.text[:300]
                logger.error(f"  HTTP {response.status_code}: {error_msg}")
                raise RuntimeError(f"API error: {error_msg}")
            
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Extract token usage if available
            usage = data.get('usage', {})
            input_tokens = usage.get('prompt_tokens', cost_tracker.estimate_tokens_from_text(user_prompt))
            output_tokens = usage.get('completion_tokens', cost_tracker.estimate_tokens_from_text(content))
            
            cost_tracker.record_call(input_tokens, output_tokens, success=True)
            
            # Parse JSON response
            result = extract_json_from_response(content)
            
            # Ensure required fields
            result.setdefault('id', f"neet_2024_phy_{question['number']:03d}")
            result.setdefault('questionNumber', question['number'])
            result.setdefault('questionText', question.get('question_text', question['text']))
            
            logger.info(f"  ✅ Successfully parsed response")
            return result
            
        except Exception as e:
            last_error = e
            logger.warning(f"  ❌ Attempt {attempt} failed: {e}")
            cost_tracker.record_call(0, 0, success=False)
            
            if attempt < model_config.max_retries:
                time.sleep(model_config.error_delay)
        finally:
            # Rate limiting
            time.sleep(model_config.rate_limit_delay)
    
    logger.error(f"  ⛔ All retries exhausted. Last error: {last_error}")
    return None


def load_progress(progress_file: Path) -> dict:
    """Load processing progress from file."""
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {
        'last_completed_batch': -1,
        'next_question_index': 0,
        'processed_question_ids': []
    }


def save_progress(progress_file: Path, progress: dict):
    """Save processing progress to file."""
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def save_batch(batch_dir: Path, batch_num: int, questions: List[dict]):
    """Save a batch of processed questions."""
    batch_file = batch_dir / f"batch_{batch_num:04d}.json"
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


def log_failed_question(failed_log: Path, question_num: int, reason: str):
    """Append failed question to log."""
    with open(failed_log, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | Q{question_num} | {reason}\n")


def process_questions_in_batches(
    questions: List[dict],
    model_config,
    path_config,
    logger: logging.Logger,
    batch_size: int = 10,
    resume: bool = True,
    dry_run: bool = False
) -> List[dict]:
    """
    Process questions in batches with progress tracking.
    
    Args:
        questions: List of raw question dicts
        model_config: Model configuration
        path_config: Path configuration
        logger: Logger instance
        batch_size: Number of questions per batch
        resume: Whether to resume from previous progress
        dry_run: If True, skip API calls (testing only)
        
    Returns:
        List of successfully processed questions
    """
    cost_tracker = CostTracker()
    all_results = []
    
    # Load progress
    progress = load_progress(path_config.progress_file) if resume else {
        'last_completed_batch': -1,
        'next_question_index': 0,
        'processed_question_ids': []
    }
    
    start_idx = progress['next_question_index']
    logger.info(f"📦 Processing from question index {start_idx}")
    
    # Process in batches
    for batch_num, i in enumerate(range(start_idx, len(questions), batch_size)):
        actual_batch_num = progress['last_completed_batch'] + 1 + batch_num
        batch = questions[i:i + batch_size]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Processing Batch {actual_batch_num} ({len(batch)} questions)")
        logger.info(f"{'='*60}")
        
        batch_results = []
        
        for q in batch:
            q_num = q['number']
            logger.info(f"\n📝 Processing Q{q_num}")
            
            # Skip if already processed
            if q_num in progress['processed_question_ids']:
                logger.info(f"  ⏭️  Already processed, skipping")
                continue
            
            # Validate question
            if not is_valid_physics_question(q['text']):
                logger.warning(f"  ⚠️  Invalid physics question, skipping")
                log_failed_question(path_config.failed_log, q_num, "Invalid physics content")
                continue
            
            if dry_run:
                logger.info(f"  🧪 DRY RUN - Skipping API call")
                continue
            
            # Call API
            structured = call_perplexity_api(q, model_config, logger, cost_tracker)
            
            if not structured:
                logger.error(f"  ❌ API call failed")
                log_failed_question(path_config.failed_log, q_num, "API call failed")
                continue
            
            # Validate completeness
            is_valid, errors = validate_question_completeness(structured)
            
            if not is_valid:
                logger.warning(f"  ⚠️  Validation failed: {'; '.join(errors[:3])}")
                log_failed_question(path_config.failed_log, q_num, f"Validation: {errors[0]}")
                # Still add it but log the issues
            
            batch_results.append(structured)
            progress['processed_question_ids'].append(q_num)
            all_results.append(structured)
            
            logger.info(f"  ✅ Successfully processed Q{q_num}")
        
        # Save batch
        if batch_results and not dry_run:
            save_batch(path_config.batches_dir, actual_batch_num, batch_results)
            logger.info(f"\n💾 Saved batch {actual_batch_num} ({len(batch_results)} questions)")
        
        # Update progress
        progress['last_completed_batch'] = actual_batch_num
        progress['next_question_index'] = min(i + batch_size, len(questions))
        save_progress(path_config.progress_file, progress)
        
        # Print cost summary so far
        logger.info(f"\n💰 Cost so far: ${cost_tracker.estimate_cost():.4f}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Batch processing complete!")
    logger.info(f"{'='*60}")
    
    cost_tracker.print_summary()
    
    return all_results


def merge_batches(batches_dir: Path, output_path: Path, logger: logging.Logger):
    """Merge all batch files into final output."""
    logger.info("\n🔗 Merging batch files...")
    
    batch_files = sorted(batches_dir.glob("batch_*.json"))
    all_questions = []
    seen_ids = set()
    
    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_questions = json.load(f)
            
        for q in batch_questions:
            q_id = q.get('id')
            if q_id and q_id not in seen_ids:
                all_questions.append(q)
                seen_ids.add(q_id)
    
    # Create final dataset
    dataset = {
        'metadata': {
            'version': '2.0',
            'lastUpdated': datetime.now().isoformat(),
            'totalQuestions': len(all_questions),
            'subject': 'Physics',
            'yearRange': '2024-2024',
            'processingMethod': 'Enhanced extraction with validation'
        },
        'questions': all_questions
    }
    
    # Validate schema
    try:
        Draft7Validator(NEET_DB_SCHEMA).validate(dataset)
        logger.info("✅ Schema validation passed")
    except Exception as e:
        logger.warning(f"⚠️  Schema validation warning: {e}")
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Merged {len(all_questions)} questions to {output_path}")
    
    return dataset


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Enhanced NEET Physics Question Extractor'
    )
    parser.add_argument(
        '--pdf',
        type=str,
        help='Path to input PDF (overrides config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to output JSON (overrides config)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of questions per batch (default: 10)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='Resume from previous progress (default: True)'
    )
    parser.add_argument(
        '--no-resume',
        dest='resume',
        action='store_false',
        help='Start from beginning, ignoring previous progress'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Extract and validate only, skip API calls'
    )
    parser.add_argument(
        '--start-question',
        type=int,
        help='Start from specific question number'
    )
    parser.add_argument(
        '--end-question',
        type=int,
        help='End at specific question number'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        model_config = get_model_config()
        path_config = get_path_config(args.pdf, args.output)
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Create a .env file from .env.example and add your PERPLEXITY_API_KEY")
        return 1
    
    # Setup logging
    logger = setup_logging(path_config.logs_dir)
    
    logger.info("="*60)
    logger.info("🚀 NEET Question Extractor v2.0")
    logger.info("="*60)
    logger.info(f"Model: {model_config.model_name}")
    logger.info(f"PDF: {path_config.pdf_path}")
    logger.info(f"Output: {path_config.output_path}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Resume: {args.resume}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("="*60)
    
    # Extract questions from PDF
    try:
        questions = extract_physics_questions_improved(path_config.pdf_path)
        
        # Filter by question number range if specified
        if args.start_question or args.end_question:
            start = args.start_question or 0
            end = args.end_question or float('inf')
            questions = [q for q in questions if start <= q['number'] <= end]
            logger.info(f"📌 Filtered to questions {start}-{end}: {len(questions)} questions")
        
        if not questions:
            logger.error("❌ No questions extracted!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {e}")
        return 1
    
    # Process questions
    try:
        results = process_questions_in_batches(
            questions,
            model_config,
            path_config,
            logger,
            batch_size=args.batch_size,
            resume=args.resume,
            dry_run=args.dry_run
        )
        
        if not args.dry_run:
            # Merge batches into final output
            final_dataset = merge_batches(
                path_config.batches_dir,
                path_config.output_path,
                logger
            )
            
            logger.info(f"\n🎉 Processing complete!")
            logger.info(f"📊 Total valid questions: {len(final_dataset['questions'])}")
            logger.info(f"📁 Output: {path_config.output_path}")
        else:
            logger.info(f"\n🧪 Dry run complete - no API calls made")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        logger.info("💾 Progress has been saved. Run with --resume to continue.")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Processing failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())

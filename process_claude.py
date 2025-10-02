#!/usr/bin/env python3
"""
Claude-based NEET Question Processor.
CRITICAL: AI must NEVER guess answers - only use answers extracted from PDF.
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests

from config import get_model_config, get_path_config, NEET_DB_SCHEMA
from pdf_extractor import extract_physics_questions_improved
from cost_tracker import CostTracker


def setup_logging(log_dir: Path):
    """Configure logging to file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"claude_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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
    """Extract JSON from Claude response."""
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


def call_claude_api(
    question: dict,
    model_config,
    logger: logging.Logger,
    cost_tracker: CostTracker
) -> Optional[dict]:
    """
    Call Claude API to structure a question.
    CRITICAL: Uses the correct answer from PDF, does NOT guess.
    """
    headers = {
        'x-api-key': model_config.api_key,
        'anthropic-version': model_config.anthropic_version,
        'content-type': 'application/json'
    }
    
    # Construct prompt that FORCES use of PDF answer
    user_prompt = f"""You are a NEET Physics question analyzer. Your task is to explain the solution, NOT to find the answer.

Question {question['number']}: {question['question_text']}

Options:
A) {question['options']['A']}
B) {question['options']['B']}
C) {question['options']['C']}
D) {question['options']['D']}

**CORRECT ANSWER FROM PDF: Option {question['correct_answer']}**

This is Answer ({question['correct_index']}) from the official NEET 2024 answer key.

**CRITICAL: The correct answer is {question['correct_answer']}. DO NOT change or question this answer. Your job is to EXPLAIN why it's correct.**

Your task:
1. Provide detailed step-by-step reasoning explaining WHY option {question['correct_answer']} is the correct answer
2. Explain WHY each of the other options is incorrect
3. Include relevant physics formulas and calculations with proper units
4. Use clear, educational language suitable for NEET preparation
5. Include NCERT chapter references where applicable

Return ONLY valid JSON matching this structure:
{{
  "id": "neet_2024_phy_{question['number']:03d}",
  "questionNumber": {question['number']},
  "examInfo": {{
    "year": 2024,
    "examType": "NEET",
    "paperCode": "2024-PHY"
  }},
  "title": "Brief descriptive title (max 80 chars)",
  "questionText": "{question['question_text'][:200]}...",
  "options": [
    {{
      "id": "A",
      "text": "{question['options']['A'][:50]}...",
      "isCorrect": {"true" if question['correct_answer'] == 'A' else "false"},
      "analysis": "Detailed explanation"
    }},
    {{
      "id": "B",
      "text": "{question['options']['B'][:50]}...",
      "isCorrect": {"true" if question['correct_answer'] == 'B' else "false"},
      "analysis": "Detailed explanation"
    }},
    {{
      "id": "C",
      "text": "{question['options']['C'][:50]}...",
      "isCorrect": {"true" if question['correct_answer'] == 'C' else "false"},
      "analysis": "Detailed explanation"
    }},
    {{
      "id": "D",
      "text": "{question['options']['D'][:50]}...",
      "isCorrect": {"true" if question['correct_answer'] == 'D' else "false"},
      "analysis": "Detailed explanation"
    }}
  ],
  "correctOption": "{question['correct_answer']}",
  "classification": {{
    "subject": "Physics",
    "chapter": "Specific NCERT chapter name",
    "topic": "Specific topic",
    "subtopic": "If applicable",
    "ncertClass": 11 or 12,
    "difficulty": "Easy", "Medium", or "Hard",
    "estimatedTime": 2-5,
    "conceptTags": ["concept1", "concept2", "concept3"],
    "bloomsLevel": "remember", "understand", "apply", "analyze", "evaluate", or "create"
  }},
  "stepByStep": [
    {{
      "title": "Step 1: Understand the Problem",
      "content": "Detailed explanation",
      "formula": "Relevant formula",
      "insight": "Key insight"
    }}
  ],
  "quickMethod": {{
    "trick": {{
      "title": "Quick approach",
      "steps": ["step1", "step2"]
    }},
    "timeManagement": {{
      "totalTime": "2-3 min"
    }}
  }},
  "questionImages": [],
  "solutionImages": []
}}

REMEMBER: correctOption MUST be "{question['correct_answer']}" - do not change it!
"""

    payload = {
        'model': model_config.model_name,
        'max_tokens': model_config.max_tokens,
        'temperature': model_config.temperature,
        'system': 'You are a NEET Physics expert. Generate detailed step-by-step solutions explaining the provided correct answer. NEVER guess or change the correct answer provided. Your job is to EXPLAIN, not to SOLVE.',
        'messages': [{
            'role': 'user',
            'content': user_prompt
        }]
        # Web search disabled to reduce costs (55x token reduction)
        # Can be re-enabled by uncommenting the tools section below:
        # 'tools': [{
        #     'type': 'web_search_20250305',
        #     'name': 'web_search',
        #     'max_uses': 3
        # }]
    }
    
    last_error = None
    for attempt in range(1, model_config.max_retries + 1):
        try:
            logger.info(f"  API call attempt {attempt}/{model_config.max_retries}")
            
            response = requests.post(
                f"{model_config.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code >= 400:
                error_msg = response.text[:300]
                logger.error(f"  HTTP {response.status_code}: {error_msg}")
                raise RuntimeError(f"API error: {error_msg}")
            
            data = response.json()
            
            # Extract content from Claude response
            content_blocks = data.get('content', [])
            content = ''
            
            for block in content_blocks:
                if block.get('type') == 'text':
                    content += block.get('text', '')
            
            # Track token usage
            usage = data.get('usage', {})
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            
            cost_tracker.record_call(input_tokens, output_tokens, success=True)
            logger.info(f"  Tokens: {input_tokens} in, {output_tokens} out")
            
            # Parse JSON response
            result = extract_json_from_response(content)
            
            # CRITICAL: Verify answer wasn't changed
            if result.get('correctOption') != question['correct_answer']:
                logger.error(f"  ❌ AI tried to change answer from {question['correct_answer']} to {result.get('correctOption')}!")
                logger.error(f"  🔒 FORCING correct answer: {question['correct_answer']}")
                result['correctOption'] = question['correct_answer']
                
                # Also fix in options array
                for opt in result.get('options', []):
                    opt['isCorrect'] = (opt['id'] == question['correct_answer'])
            
            # Ensure required fields
            result.setdefault('id', f"neet_2024_phy_{question['number']:03d}")
            result.setdefault('questionNumber', question['number'])
            result.setdefault('questionText', question['question_text'])
            result.setdefault('correctOption', question['correct_answer'])
            
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


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Claude-based NEET Physics Question Processor (No Guessing)'
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
        path_config = get_path_config()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Create a .env file and add your ANTHROPIC_API_KEY")
        return 1
    
    # Setup logging
    logger = setup_logging(path_config.logs_dir)
    
    logger.info("="*60)
    logger.info("🚀 NEET Question Processor with Claude (No Guessing)")
    logger.info("="*60)
    logger.info(f"Model: {model_config.model_name}")
    logger.info(f"PDF: {path_config.pdf_path}")
    logger.info("="*60)
    
    # Extract questions from PDF
    try:
        questions = extract_physics_questions_improved(path_config.pdf_path)
        
        # Filter by question number range if specified
        if args.start_question or args.end_question:
            start = args.start_question or 1
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
    cost_tracker = CostTracker()
    all_results = []
    
    for q in questions:
        q_num = q['number']
        logger.info(f"\n📝 Processing Q{q_num}")
        
        # CRITICAL: Skip if no answer from PDF
        if not q.get('correct_answer'):
            logger.warning(f"  ⚠️  No answer in PDF, skipping (NO GUESSING ALLOWED)")
            continue
        
        logger.info(f"  📄 PDF Answer: {q['correct_answer']} (Option {q['correct_index']})")
        
        # Call Claude
        structured = call_claude_api(q, model_config, logger, cost_tracker)
        
        if not structured:
            logger.error(f"  ❌ API call failed")
            continue
        
        all_results.append(structured)
        logger.info(f"  ✅ Successfully processed Q{q_num}")
        
        # Print cost so far
        logger.info(f"\n💰 Cost so far: ${cost_tracker.estimate_cost():.4f}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Processing complete!")
    logger.info(f"{'='*60}")
    
    cost_tracker.print_summary()
    
    # Save results
    output = {
        'metadata': {
            'version': '3.0',
            'lastUpdated': datetime.now().isoformat(),
            'totalQuestions': len(all_results),
            'subject': 'Physics',
            'yearRange': '2024-2024',
            'processingMethod': 'Claude with PDF answers (no guessing)',
            'model': model_config.model_name
        },
        'questions': all_results
    }
    
    output_path = path_config.output_path.parent / 'neet_2024_physics_claude.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n📁 Saved to: {output_path}")
    logger.info(f"📊 Total questions: {len(all_results)}")
    
    return 0


if __name__ == '__main__':
    exit(main())

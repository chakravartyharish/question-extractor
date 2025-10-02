# NEET Question Extractor - Claude Migration Implementation Plan

## ✅ COMPLETED

1. **Environment Setup**
   - Updated `.env` with Anthropic API credentials
   - Model: `claude-sonnet-4-20250514`
   - API Key configured (not to be committed to git)

2. **Config Updates**
   - Modified `config.py` to use Anthropic instead of Perplexity
   - Added `anthropic_version` parameter
   - Updated environment variable names

3. **PDF Extraction Testing**
   - Created `test_extraction.py` that successfully extracts Q1-5 with correct answers
   - Confirmed extraction format works correctly
   - **CRITICAL FINDINGS:**
     - Question 1: Answer is C (0.5 A) - NOT A as previously generated
     - Question 2: Answer is B - NOT A as previously generated  
     - Question 3: Answer is C ✓
     - Question 4: Answer is C ✓

## 🚧 TODO - CRITICAL FIXES NEEDED

### 1. Fix PDF Extractor (HIGH PRIORITY)
**File:** `pdf_extractor.py` or create new `pdf_extractor_fixed.py`

**Problem:** Current extractor misses Questions 1 & 2 because options have newlines between number and text.

**Solution:** Use the pattern from `test_extraction.py`:
```python
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
```

### 2. Remove Question Validator (HIGH PRIORITY)
**File:** `question_validator.py`

**Problem:** `is_valid_physics_question()` is too strict and rejects valid questions

**Solution:** Either:
- Remove validation entirely, OR
- Make it only check for minimum length and 4 options
- DO NOT reject based on keywords/units

### 3. Replace Perplexity with Claude API (HIGH PRIORITY)
**File:** `process_questions_v2.py`

**Changes needed:**
```python
# NEW: Anthropic API call
headers = {
    'x-api-key': model_config.api_key,
    'anthropic-version': model_config.anthropic_version,
    'content-type': 'application/json'
}

payload = {
    'model': model_config.model_name,
    'max_tokens': model_config.max_tokens,
    'temperature': model_config.temperature,
    'system': 'You are a NEET Physics expert. Generate detailed step-by-step solutions. NEVER guess or change the correct answer provided.',
    'messages': [{
        'role': 'user',
        'content': prompt_text
    }]
}

response = requests.post(
    f"{model_config.base_url}/v1/messages",
    headers=headers,
    json=payload
)
```

### 4. Update Prompt to Use PDF Answer (CRITICAL)
**File:** `process_questions_v2.py`

**NEW PROMPT STRUCTURE:**
```python
prompt_text = f"""You are a NEET Physics question analyzer.

Question {question['number']}: {question['question_text']}

Options:
A) {question['options']['A']}
B) {question['options']['B']}
C) {question['options']['C']}
D) {question['options']['D']}

**CORRECT ANSWER FROM PDF: Option {question['correct_answer']} (Option {question['correct_index']})**

**CRITICAL: The correct answer is {question['correct_answer']}. DO NOT change or question this answer.**

Your task:
1. Provide detailed step-by-step reasoning explaining WHY option {question['correct_answer']} is correct
2. Explain WHY each of the other options (A, B, C, D except {question['correct_answer']}) is incorrect
3. Include relevant physics formulas and calculations
4. Use clear, educational language suitable for NEET preparation

Return ONLY valid JSON matching this schema:
{{
  "id": "neet_2024_phy_{question['number']:03d}",
  "questionNumber": {question['number']},
  "questionText": "{question['question_text']}",
  "options": [...],
  "correctOption": "{question['correct_answer']}",
  "classification": {{...}},
  "stepByStep": [...]
}}
"""
```

### 5. Add Safeguards (HIGH PRIORITY)
**File:** `process_questions_v2.py`

```python
# BEFORE calling Claude
if not question.get('correct_answer'):
    logger.warning(f"Q{question['number']}: No correct answer in PDF, skipping")
    log_failed_question(failed_log, question['number'], "No answer in PDF")
    continue

# AFTER receiving response
structured = call_claude_api(question, ...)

# Verify answer wasn't changed
if structured.get('correctOption') != question['correct_answer']:
    logger.error(f"Q{question['number']}: AI changed answer from {question['correct_answer']} to {structured.get('correctOption')}!")
    structured['correctOption'] = question['correct_answer']  # Force correct
```

## 📋 STEP-BY-STEP IMPLEMENTATION

### Phase 1: Fix Extraction (30 min)
1. Copy pattern from `test_extraction.py` to `pdf_extractor.py`
2. Test with Q1-10 to verify all extract correctly
3. Verify all questions have `correct_answer` field

### Phase 2: Update API Integration (45 min)
1. Update `process_questions_v2.py` to use Claude API
2. Update prompt to force usage of PDF answer
3. Add validation that answer isn't changed
4. Test with 1-2 questions first

### Phase 3: Full Test Run (20 min)
1. Process Q1-5 end-to-end
2. Verify:
   - Question 1 is included
   - All correct answers match PDF
   - Solutions are detailed and accurate
3. Compare with PDF manually

### Phase 4: Documentation (15 min)
1. Update README with new setup instructions
2. Document the "no guessing" guarantee
3. Add troubleshooting section

## 🔍 VERIFICATION CHECKLIST

Before considering this complete, verify:

- [ ] Question 1 appears in output
- [ ] Question 1 answer is C (0.5 A) - NOT A
- [ ] Question 2 answer is B - NOT A  
- [ ] Question 3 answer is C
- [ ] Question 4 answer is C
- [ ] Question 5 answer is D (from earlier test)
- [ ] All solutions explain the correct answer
- [ ] No "guessing" or "alternative answers" in solutions
- [ ] Question numbering preserved (Q1 is number 1, not 0)

## 🚨 CRITICAL ERRORS FOUND IN CURRENT SYSTEM

1. **Wrong Answer for Q1**: System said A, PDF says C
2. **Wrong Answer for Q2**: System said A, PDF says B
3. **Question 1 Missing**: Validation rejected it
4. **AI Guessing**: Prompt told AI to "identify correct answer based on physics principles" instead of using PDF answer

## 💡 KEY INSIGHTS

- PDF format: `Answer (1)` means option 1 → 'A'
- PDF format: `Answer (2)` means option 2 → 'B'
- PDF format: `Answer (3)` means option 3 → 'C'
- PDF format: `Answer (4)` means option 4 → 'D'

The mapping is straightforward: Option number in PDF → Letter (1=A, 2=B, 3=C, 4=D)

## 📞 NEXT ACTIONS FOR USER

1. Review this document
2. Run the implementation in phases
3. Start with Phase 1 (fix extraction)
4. Test thoroughly before moving to next phase
5. DO NOT proceed to full processing until Q1-5 are verified correct

## 🔧 QUICK FIX SCRIPT

To immediately get correct Q1-5, run:
```bash
cd /home/harish/Desktop/NEET2025/question_extractor
python3 test_extraction.py
cat test_q1_5.json
```

This gives you the correctly extracted questions with PDF answers as a reference.

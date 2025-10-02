#!/usr/bin/env python3
"""
Test script to manually extract Q1-5 with correct answers from PDF.
"""

import fitz
import re
import json

# Open PDF
pdf = fitz.open('/home/harish/Desktop/neet-learning-platform/NEET_2024_Physics.pdf')
text = pdf[1].get_text()  # Page 2 has questions 1-4
text2 = pdf[2].get_text()  # Page 3 has more questions
full_text = text + "\n" + text2

# Manual extraction with better regex
questions = []

# Pattern to match: "NUMBER. QUESTION_TEXT (1) OPT1 (2) OPT2 (3) OPT3 (4) OPT4 Answer (X)"
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

matches = pattern.findall(full_text)

for match in matches:
    q_num, q_text, opt1, opt2, opt3, opt4, answer_idx = match
    
    # Clean up texts
    q_text = ' '.join(q_text.split())
    opt1 = ' '.join(opt1.split())
    opt2 = ' '.join(opt2.split())
    opt3 = ' '.join(opt3.split())
    opt4 = ' '.join(opt4.split())
    
    # Map to letters
    num_to_letter = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
    correct_letter = num_to_letter[answer_idx]
    
    question_dict = {
        'number': int(q_num),
        'question_text': q_text,
        'options': {
            'A': opt1,
            'B': opt2,
            'C': opt3,
            'D': opt4
        },
        'correct_answer': correct_letter,
        'correct_index': int(answer_idx)
    }
    
    questions.append(question_dict)
    
    if len(questions) >= 5:
        break

# Print results
print(f"Extracted {len(questions)} questions\n")
for q in questions:
    print(f"Q{q['number']}: {q['question_text'][:80]}...")
    print(f"  Correct Answer: {q['correct_answer']} (Option {q['correct_index']})")
    print()

# Save to JSON
output = {
    'test_extraction': 'Questions 1-5',
    'questions': questions
}

with open('test_q1_5.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Saved to test_q1_5.json")

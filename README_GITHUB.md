# NEET Question Extractor with Claude AI

**AI-powered extraction and structuring of NEET Physics questions from PDF with guaranteed correct answers.**

## 🌟 Key Features

- ✅ **Zero Guessing Guarantee**: AI never guesses answers - only uses PDF-extracted correct answers
- 📄 **PDF Answer Extraction**: Automatically extracts "Answer (X)" annotations from PDF
- 🤖 **Claude AI Integration**: Uses Anthropic's Claude with web search to generate detailed explanations
- 🔍 **Web Search Enhanced**: Claude uses web search to verify physics concepts and enhance explanations
- 🔒 **Answer Validation**: Post-processing validation ensures AI doesn't change correct answers
- 📊 **Cost Tracking**: Real-time token usage and cost estimation
- 🎯 **Batch Processing**: Process specific question ranges or all questions
- 📝 **Structured Output**: JSON format compatible with learning platforms

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- NEET Physics PDF with answer key

### Installation

```bash
# Clone the repository
git clone git@github.com:chakravartyharish/question-extractor.git
cd question-extractor

# Install dependencies
pip3 install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Usage

```bash
# Process questions 1-5 (testing)
python3 process_claude.py --start-question 1 --end-question 5

# Process all questions
python3 process_claude.py

# Process specific range
python3 process_claude.py --start-question 10 --end-question 20
```

## 📋 How It Works

### Phase 1: PDF Extraction
```
PDF → Extract Physics Section → Parse Questions → Extract "Answer (X)" → Map to A/B/C/D
```

The extractor finds questions and their official answers using regex patterns:
- Question pattern: `1.\s*In the circuit shown...`
- Answer pattern: `Answer (3)` → maps to option `C`

### Phase 2: Claude Processing with Web Search
```
Question + PDF Answer → Claude API (with web search) → Enhanced Explanation → Validation → JSON Output
```

**Web Search Usage:**
- Claude can search the web to verify physics concepts and formulas
- Looks up NCERT references and standard values
- Enhances explanations with up-to-date information
- Max 3 web searches per question to control costs

**Critical Safeguards:**
1. **Pre-flight**: Skip questions without PDF answers
2. **Prompt**: Explicitly states the correct answer and forbids changing it
3. **Post-validation**: Force-corrects if Claude tries to change the answer

### Phase 3: Output
```json
{
  "id": "neet_2024_phy_001",
  "questionNumber": 1,
  "correctOption": "C",
  "options": [
    {
      "id": "A",
      "text": "1.5 A",
      "isCorrect": false,
      "analysis": "This is incorrect because..."
    },
    {
      "id": "C",
      "text": "0.5 A",
      "isCorrect": true,
      "analysis": "This is correct because..."
    }
  ],
  "stepByStep": [...],
  "classification": {...}
}
```

## 🔐 Security & Best Practices

- ✅ `.env` excluded from Git (secrets never committed)
- ✅ PDF files excluded (too large for Git)
- ✅ Generated outputs excluded (can be regenerated)
- ✅ API keys loaded from environment variables

## 💰 Cost Estimation

**Claude Sonnet 4.5 Pricing:**
- Input: ~$1/1M tokens
- Output: ~$5/1M tokens

**Per Question (average):**
- ~1,000 input tokens + ~1,400 output tokens
- **Cost: ~$0.008 per question**

**For 45 questions:**
- Total cost: ~$0.36

## 📊 Example Run

```
🚀 NEET Question Processor with Claude (No Guessing)
============================================================
Model: claude-sonnet-4-20250514
PDF: /path/to/NEET_2024_Physics.pdf
============================================================

📝 Processing Q1
  📄 PDF Answer: C (Option 3)
  API call attempt 1/5
  Tokens: 879 in, 1221 out
  ✅ Successfully parsed response
  
💰 Cost so far: $0.0070

============================================================
✅ Processing complete!
============================================================

💰 API COST SUMMARY
============================================================
Total API Calls:     5
  ✅ Successful:     5
  ❌ Failed:         0

Token Usage:
  Input tokens:      5,035
  Output tokens:     6,839
  Total tokens:      11,874

Cost Estimate:
  Input cost:        $0.0050
  Output cost:       $0.0342
  Total cost:        $0.0392
============================================================
```

## 🛠️ Configuration

### Environment Variables (.env)

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_URL=https://api.anthropic.com
ANTHROPIC_VERSION=2023-06-01

# File Paths
PDF_PATH=/path/to/NEET_2024_Physics.pdf
OUTPUT_PATH=output/neet_2024_physics_claude.json
LOGS_DIR=logs
```

## 📁 Project Structure

```
question_extractor/
├── process_claude.py          # Main Claude-based processor
├── pdf_extractor.py            # PDF parsing with answer extraction
├── config.py                   # Configuration management
├── cost_tracker.py             # Token usage and cost tracking
├── question_validator.py       # Question validation rules
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧪 Testing

```bash
# Test extraction on first 5 questions
python3 process_claude.py --start-question 1 --end-question 5

# Verify output
cat neet_2024_physics_claude.json | python3 -m json.tool
```

## 🐛 Troubleshooting

### "No API key found"
```bash
# Make sure .env exists and contains:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### "No questions extracted"
- Check PDF path in .env
- Ensure PDF has "PHYSICS" section header
- Verify "Answer (X)" annotations are present

### "API rate limit"
- The processor includes automatic retry with backoff
- Default: 5 retries with 2-second delay

## 📝 Changelog

### Version 3.0 (2025-10-02)
- ✅ Migrated from Perplexity to Anthropic Claude
- ✅ Enhanced PDF extraction to capture "Answer (X)" annotations
- ✅ Added zero-guessing guarantee with validation
- ✅ Fixed Question 1 extraction (was previously skipped)
- ✅ Fixed answer numbering (now starts at 1, not 0)
- ✅ Added comprehensive logging and cost tracking
- ✅ Improved prompt to enforce PDF answer usage

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Anthropic Claude API for AI processing
- PyPDF2 for PDF parsing
- NEET 2024 Physics question paper

---

**Made with ❤️ for NEET aspirants**

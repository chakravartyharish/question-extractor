# NEET Question Extractor v2.0 - Setup Guide

## 🚀 Quick Start

### 1. Set up your API key

```bash
cd /home/harish/Desktop/NEET2025/question_extractor

# Copy the example environment file
cp .env.example .env

# Edit .env and add your Perplexity API key
nano .env  # or use your preferred editor
```

Your `.env` file should look like:
```
PERPLEXITY_API_KEY=your-api-key-here
MODEL_NAME=sonar-reasoning-pro
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Run the extractor

```bash
# Test extraction without API calls (dry run)
python3 process_questions_v2.py --dry-run

# Extract first 5 questions only
python3 process_questions_v2.py --start-question 1 --end-question 5 --batch-size 5

# Full extraction (all physics questions)
python3 process_questions_v2.py

# Resume from where you left off
python3 process_questions_v2.py --resume
```

---

## 📋 System Requirements

- Python 3.8 or higher
- 2GB RAM minimum (4GB recommended)
- Internet connection for API calls
- PDF file: NEET_2024_Physics.pdf

---

## 🎯 Features

### ✅ Improvements Over v1

| Feature | v1 | v2 |
|---------|-----|-----|
| **Security** | ❌ Hardcoded API key | ✅ Environment variables |
| **Filtering** | ❌ Includes instructions | ✅ Physics questions only |
| **Validation** | ⚠️ Basic | ✅ Comprehensive checks |
| **Processing** | ⚠️ All at once | ✅ Batches with resume |
| **Cost Tracking** | ❌ None | ✅ Real-time monitoring |
| **Logging** | ⚠️ Console only | ✅ File + console |
| **Model** | `sonar` | `sonar-reasoning-pro` |

---

## 📁 Project Structure

```
question_extractor/
├── config.py                   # Configuration and constants
├── pdf_extractor.py           # PDF parsing and section detection
├── question_validator.py      # Quality control
├── cost_tracker.py            # API cost monitoring
├── process_questions_v2.py    # Main processing script
├──process_questions.py         # Legacy script (v1)
├── .env                       # Your API key (DO NOT COMMIT)
├── .env.example               # Template for .env
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── batches/                   # Processing batches
│   ├── batch_0000.json
│   ├── batch_0001.json
│   └── ...
├── logs/                      # Processing logs
│   └── processing_YYYYMMDD_HHMMSS.log
├── processing_progress.json   # Resume state
├── failed_questions.log       # Failed questions log
└── neet_2024_physics.json    # Final output
```

---

## ⚙️ Configuration Options

### Environment Variables (.env)

```bash
# Required
PERPLEXITY_API_KEY=your_key_here

# Optional (defaults shown)
MODEL_NAME=sonar-reasoning-pro
TEMPERATURE=0.2
MAX_TOKENS=3000
BATCH_SIZE=10
RATE_LIMIT_DELAY=1.0
ERROR_DELAY=5.0
MAX_RETRIES=5
```

### Command Line Options

```bash
python3 process_questions_v2.py [OPTIONS]

Options:
  --pdf PATH              Input PDF path (overrides config)
  --output PATH           Output JSON path (overrides config)
  --batch-size N          Questions per batch (default: 10)
  --resume                Resume from previous progress (default)
  --no-resume             Start from beginning
  --dry-run               Extract without API calls (testing)
  --start-question N      Start from question N
  --end-question N        End at question N
  -h, --help              Show help message
```

###Examples

```bash
# Extract questions 10-20
python3 process_questions_v2.py --start-question 10 --end-question 20

# Use larger batches for faster processing
python3 process_questions_v2.py --batch-size 20

# Process different PDF
python3 process_questions_v2.py --pdf /path/to/other.pdf

# Test extraction without API costs
python3 process_questions_v2.py --dry-run --batch-size 5
```

---

## 💰 Cost Estimation

### Perplexity Pricing (2025)
- **Input tokens**: $1 per 1M tokens
- **Output tokens**: $5 per 1M tokens

### Example Costs

| Questions | Estimated Cost |
|-----------|----------------|
| 10 questions | $0.50 - $1.00 |
| 50 questions | $2.50 - $5.00 |
| 200 questions | $10.00 - $20.00 |

**Note**: Actual costs depend on question complexity. The `cost_tracker` provides real-time estimates during processing.

---

## 🔍 Question Validation

### What Gets Filtered Out

The system automatically skips:
- Exam instructions ("Read the following instructions...")
- Marking scheme explanations
- General guidelines
- Page headers/footers
- Non-physics content

### Quality Checks

Each question must have:
- ✅ At least 50 characters
- ✅ All 4 options (A, B, C, D)
- ✅ Valid correct answer
- ✅ Real chapter/topic names
- ✅ At least 2 concept tags
- ✅ Minimum 2 solution steps
- ✅ No placeholder text ("text here", etc.)

---

## 🔄 Batch Processing & Resume

### How It Works

1. **Questions are processed in batches** (default: 10)
2. **Each batch is saved** to `batches/batch_NNNN.json`
3. **Progress is tracked** in `processing_progress.json`
4. **On interruption** (Ctrl+C), current progress is saved
5. **Resume with** `--resume` flag (default behavior)

### Resume After Interruption

```bash
# Process was interrupted...
^CInterrupted by user
Progress has been saved. Run with --resume to continue.

# Resume from where you left off
python3 process_questions_v2.py --resume
```

### Start Fresh

```bash
# Ignore previous progress
python3 process_questions_v2.py --no-resume
```

---

## 📊 Output Format

### Final JSON Structure

```json
{
  "metadata": {
    "version": "2.0",
    "lastUpdated": "2025-10-02T20:00:00Z",
    "totalQuestions": 45,
    "subject": "Physics",
    "yearRange": "2024-2024",
    "processingMethod": "Enhanced extraction with validation"
  },
  "questions": [
    {
      "id": "neet_2024_phy_001",
      "questionNumber": 1,
      "examInfo": {
        "year": 2024,
        "examType": "NEET",
        "paperCode": "2024-PHY"
      },
      "title": "Newton's Laws of Motion",
      "questionText": "A body of mass 5 kg...",
      "options": [
        {
          "id": "A",
          "text": "10 m/s²",
          "isCorrect": true,
          "analysis": "Using F = ma..."
        },
        // ... 3 more options
      ],
      "correctOption": "A",
      "classification": {
        "subject": "Physics",
        "chapter": "Laws of Motion",
        "topic": "Newton's Second Law",
        "ncertClass": 11,
        "difficulty": "Medium",
        "estimatedTime": 3,
        "conceptTags": ["force", "acceleration", "mass"],
        "bloomsLevel": "apply"
      },
      "stepByStep": [
        {
          "title": "Step 1: Identify given values",
          "content": "Mass m = 5 kg, Force F = 50 N",
          "formula": "F = ma",
          "insight": "Remember to use consistent units"
        },
        // ... more steps
      ],
      "quickMethod": {
        "trick": {
          "title": "Direct application",
          "steps": ["Identify F and m", "Apply F = ma", "Solve for a"]
        },
        "timeManagement": {
          "totalTime": "2 min"
        }
      }
    }
    // ... more questions
  ]
}
```

---

## 🐛 Troubleshooting

### API Key Issues

**Error**: "Configuration Error: PERPLEXITY_API_KEY environment variable is required"

**Solution**:
```bash
# Check if .env exists
ls -la .env

# If not, create it
cp .env.example .env
nano .env  # Add your API key
```

### Invalid Model Error

**Error**: "Invalid model 'llama-3.1-sonar-small-128k-online'"

**Solution**: Use `sonar-reasoning-pro` (already set in v2)
```bash
# In .env file
MODEL_NAME=sonar-reasoning-pro
```

### PDF Not Found

**Error**: "PDF not found: /path/to/pdf"

**Solution**:
```bash
# Check PDF location
ls -la /home/harish/Desktop/neet-learning-platform/NEET_2024_Physics.pdf

# Or specify custom path
python3 process_questions_v2.py --pdf /path/to/your/pdf
```

### No Questions Extracted

**Issue**: "Extracted 0 valid Physics questions"

**Possible causes**:
1. PDF format is different
2. Section markers not found
3. All questions filtered as invalid

**Solution**:
```bash
# Try with less strict filtering
python3 -c "from pdf_extractor import extract_questions_simple; \
from pathlib import Path; \
print(len(extract_questions_simple(Path('path/to/pdf'), 10)))"
```

### API Rate Limiting

**Error**: "HTTP 429: Too Many Requests"

**Solution**: Increase `RATE_LIMIT_DELAY` in `.env`:
```bash
RATE_LIMIT_DELAY=2.0  # 2 seconds between calls
```

---

## 📝 Logs and Debugging

### Check Processing Logs

```bash
# View latest log
tail -f logs/processing_*.log

# Search for errors
grep "ERROR" logs/processing_*.log

# Check failed questions
cat failed_questions.log
```

### Failed Questions Log Format

```
2025-10-02T20:15:30Z | Q15 | Invalid physics content
2025-10-02T20:17:45Z | Q27 | API call failed
2025-10-02T20:20:10Z | Q38 | Validation: Chapter is missing or placeholder
```

---

## 🔒 Security Best Practices

### ✅ DO:
- ✅ Use `.env` for API keys
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment-specific `.env` files (`.env.development`, `.env.production`)
- ✅ Rotate API keys regularly

### ❌ DON'T:
- ❌ Commit `.env` to Git
- ❌ Hardcode API keys in code
- ❌ Share `.env` files
- ❌ Use same API key across projects

---

## 🚀 Performance Tips

### Speed Up Processing

1. **Increase batch size**:
   ```bash
   python3 process_questions_v2.py --batch-size 20
   ```

2. **Reduce delay** (if not rate-limited):
   ```env
   RATE_LIMIT_DELAY=0.5
   ```

3. **Process subset first**:
   ```bash
   python3 process_questions_v2.py --start-question 1 --end-question 20
   ```

### Reduce Costs

1. **Use dry-run mode for testing**:
   ```bash
   python3 process_questions_v2.py --dry-run
   ```

2. **Test with smaller batches**:
   ```bash
   python3 process_questions_v2.py --end-question 5
   ```

3. **Review failed_questions.log** to identify issues before full run

---

## 🆘 Support

### Check Documentation
- README.md - Project overview
- QUICKSTART.txt - Quick reference
- This file (SETUP.md) - Detailed setup

### Debugging Steps

1. Run dry-run to test extraction
2. Check logs for errors
3. Verify API key in `.env`
4. Test with small batch (5 questions)
5. Check Perplexity API status

---

## 📈 Next Steps

After successful extraction:

1. **Review output**: Check `neet_2024_physics.json`
2. **Validate quality**: Spot-check random questions
3. **Check failed questions**: Review `failed_questions.log`
4. **Cost analysis**: Review final cost summary
5. **Iterate**: Re-process failed questions if needed

---

## 🔄 Migrating from v1

If you used the old `process_questions.py`:

```bash
# Backup old output
cp neet_2024_physics.json neet_2024_physics_v1_backup.json

# Clean state
rm -rf batches/* processing_progress.json failed_questions.log

# Run v2
python3 process_questions_v2.py
```

**Key Differences**:
- v2 uses environment variables (no hardcoded keys)
- v2 filters out exam instructions
- v2 uses `sonar-reasoning-pro` model
- v2 has better validation
- v2 supports resume/batch processing

---

Happy extracting! 🎉

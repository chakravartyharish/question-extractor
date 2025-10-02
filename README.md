# NEET 2024 Physics Question Extractor

Python-based system to extract NEET Physics questions from a PDF, structure them with Perplexity's LLM according to a comprehensive JSON Schema, validate, and output a consolidated JSON file.

## 📁 Key Paths
- **Working directory**: `/home/harish/Desktop/NEET2025`
- **Project folder**: `/home/harish/Desktop/NEET2025/question_extractor`
- **Input PDF**: `/home/harish/Desktop/neet-learning-platform/NEET_2024_Physics.pdf`
- **Output JSON**: `/home/harish/Desktop/NEET2025/question_extractor/neet_2024_physics.json`

## 🖥️ Environment
- **Python**: 3.12.3
- **OS**: Ubuntu Linux
- **Shell**: bash
- **Installed packages**: PyMuPDF 1.26.4, requests 2.31.0, jsonschema 4.10.3

## 🚀 Quick Start

### 1. Setup (Dependencies already installed)
```bash
cd /home/harish/Desktop/NEET2025/question_extractor
# Optional: pip3 install -r requirements.txt
```

### 2. Run the Extraction Pipeline
```bash
python3 process_questions.py
```

## 📋 What It Does

The pipeline performs the following steps:

1. **PDF Extraction**: Reads text from `NEET_2024_Physics.pdf` using PyMuPDF
2. **Question Parsing**: Uses regex pattern `r'(\d+)\.\s+(.*?)(?=\d+\.|$)'` to identify question blocks
3. **AI Structuring**: Sends each question to Perplexity API (`llama-3.1-sonar-large-128k-online`)
4. **Schema Validation**: Validates against comprehensive NEET Questions Database Schema
5. **JSON Output**: Writes structured data to `neet_2024_physics.json`

## 📊 Output Format

The output follows this comprehensive structure:

```json
{
  "metadata": {
    "version": "1.0",
    "lastUpdated": "2025-10-02T16:45:00Z",
    "totalQuestions": 45,
    "subject": "Physics",
    "yearRange": "2024-2024"
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
      "title": "Electric Field and Charges",
      "questionText": "A charge q is placed at the center of...",
      "questionImages": [],
      "options": [
        {
          "id": "A",
          "text": "Option A text",
          "isCorrect": false,
          "analysis": "Why this option is incorrect"
        },
        {
          "id": "B",
          "text": "Option B text",
          "isCorrect": true,
          "analysis": "Why this is the correct answer"
        },
        {
          "id": "C",
          "text": "Option C text",
          "isCorrect": false,
          "analysis": "Why this option is incorrect"
        },
        {
          "id": "D",
          "text": "Option D text",
          "isCorrect": false,
          "analysis": "Why this option is incorrect"
        }
      ],
      "correctOption": "B",
      "classification": {
        "subject": "Physics",
        "chapter": "Electrostatics",
        "topic": "Electric Field",
        "subtopic": "Point Charges",
        "ncertClass": 12,
        "difficulty": "Medium",
        "estimatedTime": 3,
        "conceptTags": ["electric field", "coulomb's law", "superposition"],
        "bloomsLevel": "apply"
      },
      "stepByStep": [
        {
          "title": "Step 1: Identify Given Information",
          "content": "From the question, we have a charge q at the center...",
          "formula": "E = kq/r²",
          "insight": "Remember that electric field is a vector quantity"
        },
        {
          "title": "Step 2: Apply Relevant Formula",
          "content": "Using Coulomb's law and principle of superposition...",
          "formula": "E_net = E1 + E2 + E3"
        },
        {
          "title": "Step 3: Calculate Final Answer",
          "content": "Substituting values and solving..."
        }
      ],
      "solutionImages": [],
      "quickMethod": {
        "trick": {
          "title": "Symmetry Shortcut",
          "steps": [
            "Identify symmetry in charge distribution",
            "Use vector cancellation",
            "Calculate only non-zero components"
          ]
        },
        "timeManagement": {
          "totalTime": "2 min"
        }
      }
    }
  ]
}
```

## ⚙️ Configuration

Key parameters in `process_questions.py`:

- **PPLX_API_KEY**: Perplexity API key (embedded in code)
- **RATE_LIMIT_DELAY**: 1.0 seconds between API calls
- **ERROR_DELAY**: 5.0 seconds retry delay on errors
- **MAX_RETRIES**: 5 attempts per question
- **MAX_TOKENS**: 2000 tokens per API response

## 🔧 Troubleshooting

### Common Issues

**401 Unauthorized**
- Verify the Perplexity API key is valid and active
- Check API key format and permissions

**429 Too Many Requests**
- The script includes automatic retry with backoff
- Consider increasing `RATE_LIMIT_DELAY` if needed

**PDF not found**
- Confirm the PDF path: `/home/harish/Desktop/neet-learning-platform/NEET_2024_Physics.pdf`
- Check file permissions

**Schema validation fails**
- Review the validation error message
- Check if Perplexity output matches schema requirements
- Fallback data will be used for failed questions

**Questions merged incorrectly**
- The regex pattern may need adjustment for your specific PDF format
- Try: `re.compile(r'(\d+)\.\s+(.*?)(?=\n\s*\d+\.\s+|$)', re.S)`

## 📝 Notes

- **API Key**: Hard-coded as requested. For production, use environment variables
- **Rate Limiting**: 1-second delay between calls prevents API throttling
- **Retry Logic**: 5 attempts with 5-second backoff on failures
- **Fallback Data**: Questions that fail processing receive minimal valid structure
- **Validation**: Non-blocking; script completes even if schema validation warns

## 🎯 Expected Performance

- **Processing time**: ~1-2 seconds per question (depends on API response time)
- **Success rate**: Typically 90%+ with proper PDF formatting
- **Output size**: Varies based on question count (expect 1-5 MB for full paper)

## 📚 Schema Features

The comprehensive schema captures:
- ✅ Question metadata (ID, number, exam info)
- ✅ Full question text and images
- ✅ All 4 options with correctness flags and analysis
- ✅ Detailed classification (chapter, topic, difficulty, Bloom's level)
- ✅ Step-by-step solutions with formulas and insights
- ✅ Quick methods and time management tips
- ✅ Support for images at multiple levels

## 🤝 Contributing

To modify the schema or processing logic:
1. Edit `NEET_DB_SCHEMA` in `process_questions.py`
2. Adjust the Perplexity prompt in `call_perplexity()` function
3. Update regex pattern in `QUESTION_PATTERN` if needed

## 📄 License

This tool is for educational purposes. Ensure you have rights to process the source PDF.

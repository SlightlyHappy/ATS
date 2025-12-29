# HR Legal Module Integration

This document explains the integration of the Enhanced Agentic RAG system for HR legal assistance into your Resume Screening Application.

## 🚀 Overview

The HR Legal module adds sophisticated legal assistance capabilities to your existing resume screening application, providing:

- **Intelligent Legal Q&A**: Ask complex legal questions with customizable response formats
- **Compliance Checking**: Analyze job descriptions, policies, and documents for legal compliance
- **Document Generation**: Create legally compliant HR documents using AI
- **Multi-step Reasoning**: Handle complex legal queries with intelligent decision-making
- **Conversation Memory**: Maintain context across multiple related queries

## 📦 Installation

### 1. Install Dependencies

The HR Legal system requires additional Python packages:

```bash
pip install sentence-transformers faiss-cpu numpy scikit-learn
```

### 2. Verify Installation

Run the test script to verify everything is working:

```bash
cd backend
python test_hr_legal.py
```

### 3. Initialize the System

The HR Legal system will automatically attempt to load legal documents from the `HRlaw` folder when first initialized. If the folder is not found, the system will still work with limited functionality.

## 🔧 API Endpoints

### System Management

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/legal/status` | GET | Get system status and availability |
| `/api/legal/initialize` | POST | Initialize the legal system |
| `/api/legal/stats` | GET | Get system statistics |
| `/api/legal/rebuild-index` | POST | Rebuild the knowledge base index |
| `/api/legal/clear-cache` | POST | Clear all system caches |

### Legal Queries

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/legal/query` | POST | Process a legal query with full customization |
| `/api/legal/chat` | POST | Conversational legal queries with memory |
| `/api/legal/compliance-check` | POST | Check content for legal compliance |

### Document Management

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/legal/document-templates` | GET | Get available document templates |
| `/api/legal/generate-document` | POST | Generate legal documents using AI |

## 💡 Usage Examples

### Basic Legal Query

```javascript
const response = await fetch('/api/legal/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: "What are the notice period requirements for termination?",
        config: {
            response_length: "medium",
            response_style: "professional",
            include_citations: true,
            structured_output: true
        }
    })
});
```

### Compliance Check

```javascript
const compliance = await fetch('/api/legal/compliance-check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        content: "Job Description: Must be young and energetic...",
        type: "job_description"
    })
});
```

### Conversational Chat

```javascript
const chatResponse = await fetch('/api/legal/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "What are maternity leave policies?",
        conversation_id: "unique-conversation-id"
    })
});
```

## 🎛️ Configuration Options

### Response Length
- `short`: 50-150 words
- `medium`: 150-400 words  
- `long`: 400-800 words
- `detailed`: 800+ words
- `custom`: User-defined word count

### Response Style
- `professional`: Business-appropriate responses
- `legal`: Formal legal terminology
- `casual`: Easy-to-understand language
- `technical`: Detailed procedures
- `educational`: Explanatory responses

### Detail Level
- `brief`: Concise, key points only
- `balanced`: Key information with relevant details
- `comprehensive`: Detailed explanations with examples

### Content Options
- `include_citations`: Add legal references
- `include_confidence`: Show AI confidence scores
- `show_reasoning`: Display step-by-step reasoning
- `include_follow_ups`: Suggest related questions
- `structured_output`: Use headers and bullet points

## 🔍 System Status

Check system status at any time:

```bash
curl http://localhost:8000/api/legal/status
```

Response includes:
- System availability
- Knowledge base statistics
- Vector database information
- Performance metrics
- Error details (if any)

## 🛠️ Troubleshooting

### Common Issues

1. **"HR Legal dependencies not installed"**
   ```bash
   pip install sentence-transformers faiss-cpu numpy scikit-learn
   ```

2. **"HR Legal system not available"**
   - Check if dependencies are installed
   - Verify the system initialized successfully
   - Check logs for specific error messages

3. **Poor response quality**
   - Ensure AI provider is properly configured
   - Try rebuilding the knowledge base index
   - Check if HRlaw documents are available

4. **Slow responses**
   - Consider using GPU acceleration for sentence transformers
   - Reduce `retrieval_depth` in configuration
   - Enable caching in configuration

### Debug Information

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check system logs:
```bash
curl http://localhost:8000/api/debug/logs
```

## 🔒 Privacy & Security

- **Local Processing**: All legal analysis happens locally
- **No External Calls**: Legal knowledge base is stored locally
- **Data Privacy**: No legal queries are sent to external services
- **Temporary Storage**: Query cache can be cleared anytime

## 📈 Performance Optimization

### For Better Performance:
1. **GPU Acceleration**: Install CUDA-enabled PyTorch for faster embeddings
2. **Memory Management**: Increase system RAM for larger knowledge bases
3. **Caching**: Enable response caching for frequently asked questions
4. **Index Optimization**: Use HNSW index type for faster similarity search

### Configuration Tips:
```python
# For faster responses (lower accuracy)
config = AgenticRAGConfig(
    retrieval_depth=3,
    similarity_threshold=0.6,
    enable_caching=True
)

# For better accuracy (slower responses)
config = AgenticRAGConfig(
    retrieval_depth=10,
    similarity_threshold=0.8,
    enable_multi_step_reasoning=True
)
```

## 🤝 Integration with Resume Screening

The HR Legal system integrates seamlessly with your existing resume screening workflow:

1. **Legal Compliance for Job Descriptions**: Check job postings before publication
2. **Interview Legal Guidance**: Get real-time legal advice during hiring
3. **Documentation Support**: Generate compliant hiring documents
4. **Policy Validation**: Ensure HR policies meet legal requirements

## 📚 Next Steps

1. **Test the system** with the provided test script
2. **Initialize the legal knowledge base** via API
3. **Try sample queries** to familiarize yourself with capabilities
4. **Integrate with frontend** for user-facing legal assistance
5. **Customize configurations** based on your specific needs

## 🆘 Support

If you encounter issues:

1. Run the test script: `python test_hr_legal.py`
2. Check system status: `GET /api/legal/status`
3. Review application logs
4. Verify all dependencies are installed
5. Ensure HRlaw documents are accessible (if available)

---

**The HR Legal system is now ready to provide intelligent legal assistance for your HR processes!** 🎉

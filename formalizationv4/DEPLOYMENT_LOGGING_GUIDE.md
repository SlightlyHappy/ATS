# Deployment Logging Enhancement & Legal RAG Control

## Enhanced Logging Features

### 1. Comprehensive Startup Logging
- **Process Tracking**: Every major step in document processing is logged
- **Heartbeat Monitoring**: 30-second heartbeat logs during long operations
- **Error Context**: Full tracebacks and error types for debugging
- **Timeout Protection**: 15-minute timeout for model downloads

### 2. Model Download Monitoring
The system now provides detailed logging for:
- SentenceTransformer model initialization
- Model download progress (when possible)
- Network connectivity issues
- Model testing after successful load

### 3. Heartbeat System
During legal document processing, you'll see:
```
💓 Heartbeat 1: Legal document processing still active...
💓 Heartbeat 2: Legal document processing still active...
```
This ensures you know the system is working and not hanging.

## Legal RAG Control Options

### Option 1: Disable Legal RAG During Deployment
Set environment variable:
```bash
LEGAL_RAG_ENABLED=false
```
This completely skips legal document processing.

### Option 2: Disable Auto-Processing on Deploy
Set environment variable:
```bash
AUTO_UPDATE_ON_DEPLOY=false
```
This keeps Legal RAG enabled but skips auto-processing during deployment.

### Option 3: Use Faster Embedding Model
Set environment variable:
```bash
LEGAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
```
This uses a smaller, faster model (default is `all-mpnet-base-v2`).

## Expected Log Flow

### Normal Startup Flow:
```
📚 Checking legal document processing requirements...
📚 Legal RAG is enabled - starting document processing...
🔄 Setting up async event loop...
🔧 Creating new event loop...
🚀 Starting legal document processing...
⏰ Setting 15-minute timeout for model downloads...
🚀 Starting legal document processing for deployment
📁 Checking for legal documents...
💓 Started heartbeat monitoring
💓 Heartbeat 1: Legal document processing still active...
🤖 Initializing document processor...
🔧 About to initialize models - this may take several minutes...
⏳ Please be patient, downloading embedding models can take 5-10 minutes...
🔧 Starting document processor initialization...
📊 Target embedding model: all-mpnet-base-v2
📏 Chunk size: 512, Overlap: 50
📥 Loading SentenceTransformer model...
⏳ This may take several minutes on first run (downloading model)...
🌐 Checking internet connectivity for model download...
🚀 Starting SentenceTransformer initialization...
💓 Heartbeat 2: Legal document processing still active...
💓 Heartbeat 3: Legal document processing still active...
...
✅ SentenceTransformer model loaded successfully
🧪 Testing embedding model...
✅ Model test successful - embedding shape: (1, 768)
🔧 Initializing tokenizer...
✅ Tiktoken tokenizer initialized
🎉 Document processor initialized successfully
✅ Document processor models initialized successfully
📚 Starting document processing pipeline...
...
💓 Stopped heartbeat monitoring
📊 Legal document processing completed with result: True
✅ Legal documents processed successfully!
```

### Timeout Flow:
```
...
💓 Heartbeat 30: Legal document processing still active...
⏰ Legal document processing timed out after 15 minutes
🌐 This usually indicates network issues with model downloads
📚 Application will continue without legal RAG - can be enabled later
💡 You can manually trigger processing later via admin panel
```

### Error Flow:
```
...
❌ Failed to load embedding model: HTTPError: 503 Server Error
📋 Model error type: HTTPError
📋 Model traceback: [full traceback]
❌ Legal document processing failed: [error message]
📚 Application will continue without legal RAG - can be enabled later
💡 You can manually trigger processing later via admin panel
```

## Manual Recovery Options

### 1. Admin API Endpoints
After successful deployment, you can manually trigger:
```bash
# Diagnose legal system issues
curl -X GET /api/v1/admin/hr-templates/diagnose

# Auto-fix HR template issues
curl -X POST /api/v1/admin/hr-templates/auto-fix

# Check legal RAG health
curl -X GET /api/legal/health
```

### 2. Re-run Document Processing
```bash
python scripts/process_legal_documents.py
```

### 3. Environment Variables for Control
```bash
# Disable legal RAG entirely
LEGAL_RAG_ENABLED=false

# Keep legal RAG but skip auto-processing
AUTO_UPDATE_ON_DEPLOY=false

# Use faster model
LEGAL_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Increase timeout (in seconds)
LEGAL_RESPONSE_TIMEOUT=300
```

## Benefits

1. **No More Silent Hangs**: Heartbeat logs show the system is alive
2. **Clear Error Messages**: Detailed errors help identify issues
3. **Graceful Degradation**: App continues even if legal RAG fails
4. **Multiple Recovery Paths**: Admin APIs and manual scripts
5. **Timeout Protection**: 15-minute max prevents infinite hangs
6. **Deployment Control**: Environment variables for different scenarios

## Troubleshooting

### If logs stop after model downloads:
1. **Check network connectivity** - Model downloads require stable internet
2. **Try smaller model** - Set `LEGAL_EMBEDDING_MODEL=all-MiniLM-L6-v2`
3. **Disable auto-processing** - Set `AUTO_UPDATE_ON_DEPLOY=false`
4. **Check memory limits** - Large models need significant RAM

### If timeout occurs:
1. **Normal on first run** - Model downloads can take 10+ minutes
2. **Check Railway logs** - Look for network errors
3. **Deploy without legal RAG** - Set `LEGAL_RAG_ENABLED=false`
4. **Enable after deployment** - Use admin panel to process later

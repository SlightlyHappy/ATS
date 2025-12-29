# High-Volume Resume Processing Optimization Guide

## Overview
This document outlines the optimizations implemented to handle 100-200 resumes efficiently while maintaining accuracy and preventing crashes.

## Key Optimizations Implemented

### 1. Memory Management
- **LRU Cache System**: Only keeps 50 most recent resumes in memory
- **Disk-based Storage**: Uses SQLite + compressed file storage for persistence
- **Automatic Cleanup**: Removes old files based on configurable age (24 hours default)
- **Memory Monitoring**: Tracks usage and triggers cleanup at 80% threshold
- **Garbage Collection**: Forces cleanup after processing batches

### 2. AI Processing Optimization
- **Connection Pooling**: Maintains 4 persistent connections to Ollama
- **Response Caching**: Caches identical prompts to avoid redundant API calls
- **Adaptive Model Selection**: 
  - `qwen2.5:3b` for high-volume (20+ resumes) - faster processing
  - `qwen2.5:7b` for smaller batches - better accuracy
- **Unified Analysis**: Single AI call instead of multi-stage processing
- **Batch Processing**: Concurrent processing with configurable limits

### 3. File Processing Improvements
- **Streaming Text Extraction**: Processes files without loading everything into memory
- **Compressed Storage**: Gzip compression for processed files
- **Deduplication**: Prevents processing identical resumes
- **Chunked Processing**: Processes resumes in configurable batches (default: 10)

### 4. Database-like Storage
- **SQLite Backend**: Fast metadata queries without loading full content
- **Indexed Searches**: Optimized queries for common operations
- **Transaction Management**: Ensures data integrity during batch operations

## Configuration Options

### Memory Settings
```python
MAX_MEMORY_CACHE_SIZE = 50      # Resumes kept in memory
MEMORY_WARNING_THRESHOLD = 0.8  # 80% memory usage warning
```

### Processing Settings
```python
CHUNK_SIZE = 10                 # Resumes per batch
MAX_CONCURRENT_PROCESSING = 4   # Parallel processing limit
BATCH_ANALYSIS_THRESHOLD = 5    # Switch to batch mode at 5+ resumes
```

### Model Selection
```python
HIGH_VOLUME_MODEL = 'qwen2.5:3b'  # For 20+ resumes
ACCURACY_MODEL = 'qwen2.5:7b'     # For smaller batches
```

## Performance Benchmarks

### Expected Performance (on 6GB GPU system):
- **Small Batch (1-5 resumes)**: 2-3 minutes per resume
- **Medium Batch (6-20 resumes)**: 1.5-2 minutes per resume (concurrent processing)
- **Large Batch (21+ resumes)**: 45-60 seconds per resume (fast model + batch processing)

### Memory Usage:
- **Base Application**: ~100-200MB
- **Per Resume in Memory**: ~5-10MB
- **Peak Processing**: ~500MB-1GB (depending on batch size)

## Monitoring and Diagnostics

### Available Endpoints:
- `GET /api/stats` - System statistics and performance metrics
- `GET /api/debug/logs` - Processing logs and error tracking
- `POST /api/cleanup` - Manual cleanup trigger

### Key Metrics to Monitor:
1. **Memory Usage**: Should stay below 85%
2. **Cache Hit Rate**: Higher is better for repeated processing
3. **Processing Time**: Should decrease with larger batches
4. **Error Rate**: Should be minimal (<5%)

## Error Handling and Recovery

### Graceful Degradation:
1. **AI Failures**: Creates minimal response structure instead of crashing
2. **Memory Pressure**: Automatically reduces cache size
3. **File Corruption**: Skips problematic files and continues processing
4. **Timeout Handling**: Shorter timeouts with retry logic

### Validation System:
- **Response Validation**: Ensures AI responses contain actual data
- **Placeholder Detection**: Identifies and rejects low-quality responses
- **Scoring Validation**: Ensures scores are within valid ranges (1-100)

## Best Practices for High-Volume Processing

### 1. Pre-processing Recommendations
- Upload files in batches of 10-20 for optimal performance
- Ensure Ollama is warmed up before large batches
- Monitor system memory before starting

### 2. During Processing
- Don't interrupt batch processing once started
- Monitor logs for any errors or warnings
- Allow extra time for first batch (model loading)

### 3. Post-processing
- Export results periodically to avoid data loss
- Run manual cleanup if processing many batches
- Check system stats after large processing runs

## Troubleshooting

### High Memory Usage
```bash
# Check system stats
curl http://localhost:8000/api/stats

# Manual cleanup
curl -X POST http://localhost:8000/api/cleanup
```

### Slow Processing
1. Check Ollama model status: `ollama list`
2. Verify GPU utilization
3. Consider switching to faster model for bulk processing

### AI Analysis Failures
1. Check Ollama connection: `curl http://localhost:11434/api/tags`
2. Review debug logs: `/api/debug/logs?level=error`
3. Ensure model is properly loaded

## Scaling Beyond 200 Resumes

For even larger volumes (500+ resumes), consider:

1. **Distributed Processing**: Split across multiple machines
2. **Database Migration**: Move from SQLite to PostgreSQL
3. **Queue System**: Implement Redis/Celery for background processing
4. **Load Balancing**: Multiple Ollama instances
5. **Caching Layer**: Redis for AI response caching

## Environment Variables

```bash
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Processing Limits
MAX_CONCURRENT_PROCESSING=4
BATCH_SIZE=10

# Memory Management
MAX_MEMORY_CACHE_SIZE=50
MEMORY_WARNING_THRESHOLD=0.8
```

## Monitoring Commands

```bash
# Check memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Check disk space
df -h

# Monitor Ollama
curl http://localhost:11434/api/tags

# Check application stats
curl http://localhost:8000/api/stats
```

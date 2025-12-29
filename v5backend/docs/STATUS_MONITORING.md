# Resume Analysis Status Monitoring System

## Overview

The Status Monitoring System provides comprehensive monitoring and auto-recovery capabilities for the resume analysis pipeline. It automatically detects stuck resumes, triggers analysis for ready resumes, and provides detailed status information.

## Features

### 🔍 **Status Checking**
- **System Overview**: Real-time statistics and health metrics
- **Individual Resume Status**: Detailed analysis progress for specific resumes
- **Resume List View**: Paginated list of all resumes with status information
- **Stuck Resume Detection**: Identifies resumes stuck in processing
- **Ready Resume Detection**: Finds resumes with text but no analysis

### 🔧 **Auto-Recovery**
- **Automatic Processing**: Detects and recovers stuck resumes automatically
- **Smart Triggering**: Automatically starts analysis for ready resumes
- **Manual Triggers**: Force analysis for specific resumes
- **Background Monitoring**: Celery tasks run periodic health checks

### 📊 **Health Monitoring**
- **System Health Score**: Overall system performance assessment
- **Performance Metrics**: Processing times, confidence scores, completion rates
- **Database Statistics**: Table sizes, orphaned data detection
- **Recommendations**: Actionable suggestions for system optimization

## API Endpoints

### Status Information
```http
GET /api/status/overview                    # System overview
GET /api/status/resumes?limit=50&offset=0   # List all resumes
GET /api/status/resumes/{resume_id}         # Single resume status
GET /api/status/stuck?minutes=10            # Find stuck resumes
GET /api/status/ready                       # Find ready resumes
```

### Actions
```http
POST /api/actions/trigger/{resume_id}       # Trigger single resume
     {"force": false}                       # Optional force flag

POST /api/actions/auto-recover              # Auto-recover system
     {"dry_run": false}                     # Optional dry run

POST /api/actions/trigger-all-ready         # Trigger all ready resumes
```

## CLI Tool Usage

The `status_cli.py` provides command-line access to all monitoring functions:

```bash
# System overview
python status_cli.py overview

# List resumes
python status_cli.py list --limit 20

# Check specific resume
python status_cli.py check <resume_id>

# Find stuck resumes
python status_cli.py stuck --minutes 15

# Find ready resumes
python status_cli.py ready

# Trigger analysis
python status_cli.py trigger <resume_id> --force

# Auto-recover system
python status_cli.py auto-recover --dry-run

# Health check
python status_cli.py health
```

## Test GUI Integration

The test GUI includes a dedicated "Status Monitor" tab with:

### Control Panel
- **📊 System Overview**: Load system statistics
- **🔄 Refresh Status**: Update resume list
- **🏥 Health Check**: Perform system health assessment
- **⏰ Find Stuck**: Locate stuck resumes
- **🚀 Find Ready**: Find resumes ready for analysis  
- **🔧 Auto-Recover**: Automatically fix issues
- **Manual Actions**: Check/trigger specific resumes

### Display Areas
- **Overview Tab**: System statistics and health information
- **Resume List Tab**: Sortable table of all resumes with status
- **Details Tab**: Detailed information for specific operations

## Resume Status States

### Processing States
- **`pending`**: Initial state after upload
- **`queued`**: Queued for processing
- **`processing`**: Currently being processed
- **`complete`**: Analysis finished successfully
- **`duplicate`**: Duplicate content detected
- **`failed`**: Processing failed

### Analysis Stages
- **`queued`**: Waiting to start
- **`text_extracted`**: PDF/DOCX text extracted
- **`chunked`**: Text chunked and embedded
- **`analyzed`**: Facts extracted by AI agents
- **`complete`**: Fully processed with confidence score

## Automatic Monitoring

### Background Tasks

#### Resume Status Monitor (`monitor_resume_status`)
- **Schedule**: Every 5 minutes
- **Function**: Finds and recovers stuck resumes, triggers ready ones
- **Queue**: `io`

#### Health Check (`resume_health_check`)
- **Schedule**: Every 30 minutes  
- **Function**: Comprehensive system health assessment
- **Queue**: `io`

### Configuration
```python
# In celery_app.py
beat_schedule={
    "monitor-resume-status": {
        "task": "monitor_resume_status",
        "schedule": 300.0,  # 5 minutes
    },
    "resume-health-check": {
        "task": "resume_health_check", 
        "schedule": 1800.0,  # 30 minutes
    },
}
```

## Status Detection Logic

### Stuck Resume Detection
A resume is considered "stuck" if:
- Status is `queued` or `processing`
- Last updated > 10 minutes ago
- Not in terminal states (`complete`, `duplicate`, `failed`)

### Ready Resume Detection  
A resume is "ready for analysis" if:
- Has extracted text (`ResumeText` exists)
- No analysis facts (`ResumeFacts` missing)
- Not in error states

### Auto-Recovery Logic
1. **Find Stuck Resumes**: Identify resumes stuck > 15 minutes
2. **Determine Recovery Point**: 
   - No text → Start from IO stage
   - Has text, no chunks → Start from embedding stage  
   - Has chunks, no facts → Start from LLM stage
3. **Trigger Processing**: Queue appropriate Celery task
4. **Find Ready Resumes**: Identify resumes with text but no analysis
5. **Trigger Analysis**: Queue LLM analysis tasks

## Health Scoring

### Health Score Calculation
- **EXCELLENT ✅**: 0 stuck, >90% completion rate
- **GOOD 👍**: ≤2 stuck, >80% completion rate  
- **WARNING ⚠️**: ≤5 stuck, >60% completion rate
- **CRITICAL ❌**: >5 stuck or <60% completion rate

### Metrics Tracked
- **Total Resumes**: Count of all uploaded resumes
- **Completion Rate**: Percentage with full analysis
- **Average Confidence**: Mean confidence of completed analyses
- **Stuck Count**: Number of stuck resumes
- **Processing Pipeline**: Counts at each stage

## Error Handling

### Graceful Degradation
- **Database Errors**: Continue with cached data where possible
- **API Failures**: Provide meaningful error messages
- **Task Failures**: Log errors and continue monitoring
- **Partial Recovery**: Recover what's possible, report failures

### Logging
All monitoring operations are logged with structured data:
```python
log.info("auto_recover_stuck", resume_id=status.id, stage=status.analysis_stage)
log.error("trigger_analysis_failed", resume_id=resume_id, error=str(e))
```

## Production Deployment

### Environment Variables
```bash
# Monitoring intervals (optional)
MONITOR_INTERVAL=300        # Status monitor interval (seconds)
HEALTH_CHECK_INTERVAL=1800  # Health check interval (seconds)

# Thresholds (optional)
STUCK_THRESHOLD_MINUTES=15  # Consider stuck after N minutes
AUTO_RECOVERY_ENABLED=true  # Enable automatic recovery
```

### Monitoring Setup
1. **Enable Celery Beat**: For periodic tasks
2. **Configure Logging**: Structured logs for monitoring
3. **Set Up Alerts**: Monitor health check results
4. **Dashboard Integration**: Use API endpoints for dashboards

## Integration Examples

### Monitoring Dashboard
```python
import requests

# Get system overview
response = requests.get("https://your-api.com/api/status/overview")
stats = response.json()

print(f"Health: {stats['completion_rate']:.1f}% complete")
print(f"Issues: {stats['stuck_count']} stuck resumes")
```

### Automated Recovery
```python
# Trigger auto-recovery
response = requests.post("https://your-api.com/api/actions/auto-recover")
results = response.json()['results']

print(f"Recovered: {results['recovered']}")
print(f"Triggered: {results['triggered']}")
```

### Health Monitoring
```python
# Check system health
response = requests.get("https://your-api.com/api/status/overview")
data = response.json()

if data['stuck_count'] > 5:
    alert("High number of stuck resumes detected!")
```

## Troubleshooting

### Common Issues
1. **High Stuck Count**: Check Celery worker health, Ollama availability
2. **Low Completion Rate**: Verify model downloads, check error logs  
3. **Slow Processing**: Monitor resource usage, check concurrency settings
4. **Auto-Recovery Failures**: Verify database connectivity, check task queues

### Debug Commands
```bash
# Check specific resume
python status_cli.py check <resume_id>

# Find all stuck resumes
python status_cli.py stuck

# Dry run recovery
python status_cli.py auto-recover --dry-run

# System health check  
python status_cli.py health
```

The Status Monitoring System ensures reliable, self-healing resume analysis with comprehensive visibility into system health and performance.

# Enhanced RAG Engine with Multi-Provider AI

This enhanced RAG (Retrieval-Augmented Generation) engine now supports multiple AI providers with intelligent routing for optimal performance and cost efficiency.

## 🚀 New Features

### Multi-Provider AI Support
- **OpenAI**: GPT-3.5-turbo, GPT-4, GPT-4o
- **Anthropic**: Claude-3 Sonnet, Haiku, Opus
- **Google Gemini**: Gemini Pro
- **Together AI**: Various open-source models
- **Ollama**: Local models (qwen2.5:7b)

### Intelligent Routing
- **Query Complexity Analysis**: Automatically determines query complexity (simple/medium/complex)
- **Provider Selection**: Routes queries to optimal providers based on complexity and performance profile
- **Fallback Mechanism**: Automatic failover to alternative providers
- **Response Caching**: Caches responses to improve performance

### Performance Profiles
- **Speed Optimized**: Fastest response times
- **Quality Optimized**: Best response quality
- **Cost Optimized**: Lowest cost
- **Balanced**: Good balance of speed, quality, and cost

## 🔧 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)
Set environment variables for the providers you want to use:

```bash
# OpenAI
export OPENAI_API_KEY="your_openai_api_key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# Google Gemini
export GEMINI_API_KEY="your_gemini_api_key"

# Together AI
export TOGETHER_API_KEY="your_together_api_key"
```

### 3. Setup Local Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull qwen2.5:7b

# Start the server
ollama serve
```

## 🎯 Usage Examples

### Basic Setup
```python
from hr_legal.rag_engine import EnhancedRAGEngine
from hr_legal.config import LegalQueryContext, AgenticRAGConfig

# Initialize with smart routing
rag_engine = EnhancedRAGEngine(enable_smart_routing=True)

# Setup providers (automatically detects available providers)
providers = [
    {
        'provider_type': 'ollama',
        'model': 'qwen2.5:7b',
        'api_key': None
    },
    {
        'provider_type': 'gemini',
        'model': 'gemini-pro',
        'api_key': os.getenv('GEMINI_API_KEY')
    }
]

rag_engine.setup_multi_provider_ai(providers)
```

### Query Processing
```python
# Create query context
query_context = LegalQueryContext(
    query="What are the key provisions of employment law?",
    user_id="user123",
    session_id="session456"
)

# Configure response
config = AgenticRAGConfig(
    retrieval_depth=5,
    similarity_threshold=0.7,
    enable_caching=True
)

# Process query (automatically routes to optimal provider)
response = rag_engine.query(query_context, config)
```

### Performance Profile Selection
```python
from hr_legal.ai_config import AIProviderConfig

# Get providers for speed-optimized profile
speed_providers = AIProviderConfig.get_providers_for_profile('speed_optimized')

# Get providers for quality-optimized profile
quality_providers = AIProviderConfig.get_providers_for_profile('quality_optimized')
```

## 📊 Performance Improvements

### Speed Improvements
- **2-10x faster** responses with external APIs vs local Ollama
- **Intelligent caching** reduces redundant API calls
- **Parallel processing** for complex queries

### Quality Improvements
- **Provider specialization**: Legal queries routed to Claude/GPT-4
- **Fallback mechanisms**: Ensures responses even if primary provider fails
- **Quality validation**: Automatic response quality scoring

### Cost Optimization
- **Smart routing**: Simple queries use cheaper providers
- **Caching**: Reduces API costs
- **Fallback to local**: Free local model as backup

## 🔄 Intelligent Routing Logic

### Query Complexity Analysis
```
Simple (0-50 words):     Gemini Pro, GPT-3.5-turbo
Medium (51-200 words):   GPT-3.5-turbo, Claude Haiku
Complex (200+ words):    GPT-4, Claude Sonnet/Opus
```

### Provider Selection Criteria
1. **Query complexity** (word count, legal terms, technical terms)
2. **Performance profile** (speed/quality/cost/balanced)
3. **Provider availability** (API status, rate limits)
4. **Historical performance** (response time, success rate)

## 🛠️ Configuration

### Environment Variables
```bash
# Required for respective providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
TOGETHER_API_KEY=...

# Optional configuration
RAG_CACHE_TTL=1800          # Cache TTL in seconds
RAG_MAX_RETRIES=3           # Max fallback retries
OLLAMA_BASE_URL=http://localhost:11434
```

### Performance Profiles
Edit `hr_legal/ai_config.py` to customize:
- Provider preferences
- Complexity routing rules
- Cache settings
- Fallback configurations

## 📈 Monitoring & Analytics

### System Status
```python
status = rag_engine.get_enhanced_system_status()
print(f"Total queries: {status['engine_stats']['total_queries']}")
print(f"Success rate: {status['engine_stats']['successful_queries'] / status['engine_stats']['total_queries']:.2%}")
print(f"Avg response time: {status['engine_stats']['average_query_time']:.2f}s")
```

### Provider Statistics
```python
provider_stats = rag_engine.get_ai_provider_stats()
for provider, stats in provider_stats.items():
    print(f"{provider}: {stats['successful_requests']}/{stats['total_requests']} requests")
```

## 🚨 Troubleshooting

### Common Issues

1. **No providers available**
   - Ensure at least one API key is set or Ollama is running
   - Check `ollama list` to confirm qwen2.5:7b is installed

2. **Slow responses**
   - Check network connectivity to API providers
   - Consider using speed_optimized profile
   - Verify Ollama server is running locally

3. **API errors**
   - Verify API keys are correct and have sufficient credits
   - Check rate limits for your API plan
   - Enable fallback to local Ollama

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed routing decisions and API calls
```

## 🔮 Planned Enhancements

- **Streaming responses** for better UX
- **Custom model fine-tuning** for legal domain
- **Multi-modal support** (PDF, image analysis)
- **Advanced caching** with semantic similarity
- **Load balancing** across multiple API keys
- **Cost tracking** and budget limits

## 📝 Example Scripts

Run the example scripts to test the system:

```bash
# Test AI provider setup
python hr_legal/setup_ai_providers.py

# Run usage examples
python hr_legal/example_usage.py
```

## 🔐 Security Considerations

- API keys are loaded from environment variables
- No API keys are logged or stored in plain text
- Local Ollama provides offline capability
- Response caching excludes sensitive data

## 📚 API Reference

See individual module documentation:
- `rag_engine.py` - Main RAG engine
- `multi_provider_ai.py` - AI provider management
- `ai_config.py` - Configuration classes
- `setup_ai_providers.py` - Setup utilities

from prometheus_client import Counter, Histogram

UPLOAD_COUNTER = Counter("uploads_total", "Number of uploaded files", ["status"]) 
EXTRACT_LATENCY = Histogram("extract_latency_seconds", "Time to extract text")
EMBED_LATENCY = Histogram("embed_latency_seconds", "Time to generate embeddings")
LLM_LATENCY = Histogram("llm_latency_seconds", "Time to run LLM extraction")

# New metrics
OCR_USED = Counter("ocr_used_total", "Count of files where OCR was used")
AGENT_FALLBACKS = Counter("agent_fallbacks_total", "Number of times fallback cascade was used")
AGENT_CONFIDENCE = Histogram("agent_confidence", "Confidence score distribution of agent pipeline")

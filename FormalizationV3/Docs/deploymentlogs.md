[auth] sharing credentials for production-europe-west4-drams3a.railway-registry.com  ✔ 0 ms

Build time: 18.29 seconds

 

====================

Starting Healthcheck

====================


Path: /health

Retry window: 30s

 

Attempt #1 failed with service unavailable. Continuing to retry for 19s

Attempt #2 failed with service unavailable. Continuing to retry for 8s

 

1/1 replicas never became healthy!

Healthcheck failed!


2025-07-29 08:23:02,249 - railway_optimizer - INFO - Railway optimizations applied: ['garbage_collection', 'gc_thresholds', 'thread_switching', 'memory_limit']

2025-07-29 08:23:03,250 - app - INFO - Railway optimization result: {'success': True, 'optimizations': ['garbage_collection', 'gc_thresholds', 'thread_switching', 'memory_limit'], 'memory_usage': {'total_memory_mb': 257938.125, 'used_memory_mb': 152949.0, 'available_memory_mb': 101930.09765625, 'memory_percent': 60.5, 'process_memory_mb': 632.9921875, 'railway_limit_mb': 6000, 'within_limits': True}, 'cpu_usage': {'cpu_percent': 44.1, 'cpu_count': 32, 'load_average_1m': 17.3623046875, 'load_average_5m': 15.69580078125, 'load_average_15m': 15.15625, 'railway_cores': 32, 'within_limits': True}}

2025-07-29 08:23:03,305 - storage_manager - INFO - Directory ensured: /app/uploads

2025-07-29 08:23:03,305 - storage_manager - INFO - Directory ensured: /app/processed

2025-07-29 08:23:03,305 - storage_manager - INFO - Directory ensured: /app/temp

2025-07-29 08:23:03,305 - storage_manager - INFO - Directory ensured: /app/logs

2025-07-29 08:23:03,305 - modules.enhanced_ai.multi_provider_ai - INFO - Ollama provider initialized

2025-07-29 08:23:03,305 - modules.enhanced_ai.multi_provider_ai - INFO - OpenAI provider initialized

2025-07-29 08:23:03,305 - modules.enhanced_ai.multi_provider_ai - INFO - Anthropic provider initialized

2025-07-29 08:23:03,305 - modules.enhanced_ai.multi_provider_ai - INFO - Initialized 3 AI providers: ['ollama', 'openai', 'anthropic']

2025-07-29 08:23:03,306 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu

2025-07-29 08:23:03,306 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: all-MiniLM-L6-v2

2025-07-29 08:23:04,478 - modules.hr_legal_rag.hr_legal_rag - ERROR - Failed to load sentence transformer: 

2025-07-29 08:23:04,478 - modules.hr_legal_rag.hr_legal_rag - INFO - Enhanced fallback legal system initialized

2025-07-29 08:23:04,479 - ai_processor - INFO - Enhanced Agentic AI system initialized successfully

2025-07-29 08:23:04,479 - app - INFO - AI analyzer initialized with premium routing support

2025-07-29 08:23:04,479 - app - INFO - All components initialized successfully

2025-07-29 08:23:04,482 - __main__ - ERROR - Startup failed: 



Deployment failed during the network process

View less

Initialization

(00:14)

Build

(00:25)

Deploy

(01:17)

Network › Healthcheck

(00:55)

Healthcheck failure

Post-deploy
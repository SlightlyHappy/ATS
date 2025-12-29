"""
System resource checker and automatic configuration optimizer.
Analyzes system capabilities and sets optimal configuration for resume processing.
"""

import psutil
import requests
import os
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemOptimizer:
    """Analyzes system resources and optimizes configuration for best performance."""
    
    def __init__(self):
        self.system_info = self._gather_system_info()
        self.ollama_info = self._check_ollama_status()
        
    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather comprehensive system information."""
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_count()
        
        return {
            "total_memory_gb": memory.total / (1024**3),
            "available_memory_gb": memory.available / (1024**3),
            "memory_usage_percent": memory.percent,
            "cpu_cores": cpu,
            "logical_processors": psutil.cpu_count(logical=True)
        }
    
    def _check_ollama_status(self) -> Dict[str, Any]:
        """Check Ollama service status and available models."""
        try:
            # Check if Ollama is running
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            response = requests.get(f"{ollama_url}/api/tags", timeout=300)  # Increased from 5 to 300 seconds
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "running",
                    "available_models": [model["name"] for model in models],
                    "model_count": len(models)
                }
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    def get_recommended_config(self) -> Dict[str, Any]:
        """Generate optimized configuration based on system resources."""
        memory_gb = self.system_info["total_memory_gb"]
        cpu_cores = self.system_info["cpu_cores"]
        memory_usage = self.system_info["memory_usage_percent"]
        
        # Base configuration
        config = {
            "performance_profile": "unknown",
            "recommended_model": "qwen2.5:7b",
            "max_memory_cache_size": 50,
            "chunk_size": 10,
            "max_concurrent_processing": 4,
            "batch_analysis_threshold": 5,
            "memory_warning_threshold": 0.8,
            "warnings": [],
            "recommendations": []
        }
        
        # Determine performance profile
        if memory_gb >= 16 and cpu_cores >= 8:
            config.update({
                "performance_profile": "high_performance",
                "max_memory_cache_size": 100,
                "chunk_size": 15,
                "max_concurrent_processing": 6,
                "batch_analysis_threshold": 3
            })
            config["recommendations"].append("System is optimized for high-volume processing")
            
        elif memory_gb >= 8 and cpu_cores >= 4:
            config.update({
                "performance_profile": "balanced",
                "max_memory_cache_size": 75,
                "chunk_size": 12,
                "max_concurrent_processing": 4,
                "batch_analysis_threshold": 4
            })
            config["recommendations"].append("Balanced configuration for moderate workloads")
            
        elif memory_gb >= 4:
            config.update({
                "performance_profile": "conservative",
                "max_memory_cache_size": 25,
                "chunk_size": 8,
                "max_concurrent_processing": 2,
                "batch_analysis_threshold": 6,
                "memory_warning_threshold": 0.7
            })
            config["warnings"].append("Limited memory - using conservative settings")
            
        else:
            config.update({
                "performance_profile": "minimal",
                "max_memory_cache_size": 10,
                "chunk_size": 5,
                "max_concurrent_processing": 1,
                "batch_analysis_threshold": 8,
                "memory_warning_threshold": 0.6
            })
            config["warnings"].append("Very limited memory - minimal configuration")
        
        # Memory usage warnings
        if memory_usage > 80:
            config["warnings"].append(f"High memory usage: {memory_usage:.1f}% - consider closing other applications")
        
        # Ollama-specific recommendations
        if self.ollama_info["status"] == "running":
            available_models = self.ollama_info.get("available_models", [])
            
            # Model recommendations based on system specs
            if memory_gb < 6:
                if "qwen2.5:3b" in available_models:
                    config["recommended_model"] = "qwen2.5:3b"
                    config["recommendations"].append("Using fast 3B model for limited memory")
                else:
                    config["warnings"].append("Consider installing qwen2.5:3b model for better performance")
            
            elif memory_gb >= 8:
                if "qwen2.5:7b" in available_models:
                    config["recommended_model"] = "qwen2.5:7b"
                    config["recommendations"].append("Using balanced 7B model")
                elif "qwen2.5:3b" in available_models:
                    config["recommended_model"] = "qwen2.5:3b"
                    config["warnings"].append("7B model not available, using 3B model")
                
            if "qwen2.5:14b" in available_models and memory_gb >= 12:
                config["recommendations"].append("14B model available for maximum accuracy (slower)")
                
        else:
            config["warnings"].append(f"Ollama status: {self.ollama_info['status']}")
            if self.ollama_info["status"] == "offline":
                config["warnings"].append("Start Ollama service before processing resumes")
        
        return config
    
    def generate_env_file(self, config: Dict[str, Any]) -> str:
        """Generate optimized environment file."""
        from datetime import datetime
        
        env_content = f"""# Auto-generated optimized configuration
# Performance Profile: {config['performance_profile']}
# Generated on: {datetime.now().isoformat()}

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL={config['recommended_model']}

# Processing Configuration
MAX_MEMORY_CACHE_SIZE={config['max_memory_cache_size']}
CHUNK_SIZE={config['chunk_size']}
MAX_CONCURRENT_PROCESSING={config['max_concurrent_processing']}
BATCH_ANALYSIS_THRESHOLD={config['batch_analysis_threshold']}
MEMORY_WARNING_THRESHOLD={config['memory_warning_threshold']}

# Feature Flags
COMPRESS_PROCESSED_FILES=True
ENABLE_AI_RESPONSE_CACHING=True
ENABLE_MEMORY_MONITORING=True
ENABLE_PERSISTENT_STORAGE=True
"""
        return env_content
    
    def print_report(self):
        """Print comprehensive system analysis and recommendations."""
        print("=" * 60)
        print("RESUME PROCESSING SYSTEM OPTIMIZATION REPORT")
        print("=" * 60)
        
        print("\n📊 SYSTEM INFORMATION")
        print(f"Memory: {self.system_info['total_memory_gb']:.1f} GB total, "
              f"{self.system_info['available_memory_gb']:.1f} GB available "
              f"({self.system_info['memory_usage_percent']:.1f}% used)")
        print(f"CPU: {self.system_info['cpu_cores']} cores, "
              f"{self.system_info['logical_processors']} logical processors")
        
        print(f"\n🤖 OLLAMA STATUS")
        if self.ollama_info["status"] == "running":
            print(f"✅ Running with {self.ollama_info['model_count']} models available")
            for model in self.ollama_info.get("available_models", []):
                print(f"   - {model}")
        else:
            print(f"❌ {self.ollama_info['status'].upper()}: {self.ollama_info.get('error', 'Unknown error')}")
        
        config = self.get_recommended_config()
        
        print(f"\n⚙️  RECOMMENDED CONFIGURATION")
        print(f"Performance Profile: {config['performance_profile'].upper()}")
        print(f"Recommended Model: {config['recommended_model']}")
        print(f"Memory Cache Size: {config['max_memory_cache_size']} resumes")
        print(f"Batch Size: {config['chunk_size']} resumes")
        print(f"Concurrent Processing: {config['max_concurrent_processing']} threads")
        print(f"Batch Threshold: {config['batch_analysis_threshold']} resumes")
        
        if config.get("warnings"):
            print("\n⚠️  WARNINGS")
            for warning in config["warnings"]:
                print(f"   - {warning}")
        
        if config.get("recommendations"):
            print("\n💡 RECOMMENDATIONS")
            for rec in config["recommendations"]:
                print(f"   - {rec}")
        
        print("\n🎯 EXPECTED PERFORMANCE")
        if config["performance_profile"] == "high_performance":
            print("   - Small batches (1-5): 1-2 minutes per resume")
            print("   - Large batches (20+): 30-45 seconds per resume")
            print("   - Can handle 200+ resumes efficiently")
        elif config["performance_profile"] == "balanced":
            print("   - Small batches (1-5): 2-3 minutes per resume")
            print("   - Large batches (20+): 45-60 seconds per resume")
            print("   - Can handle 100-150 resumes efficiently")
        elif config["performance_profile"] == "conservative":
            print("   - Small batches (1-5): 3-4 minutes per resume")
            print("   - Large batches (20+): 60-90 seconds per resume")
            print("   - Recommended max: 50-75 resumes per session")
        else:
            print("   - Sequential processing recommended")
            print("   - 4-5 minutes per resume")
            print("   - Process in small batches (5-10 resumes)")
        
        print("\n" + "=" * 60)

def main():
    """Main optimization check and configuration generation."""
    optimizer = SystemOptimizer()
    optimizer.print_report()
    
    config = optimizer.get_recommended_config()
    
    # Optionally generate .env file
    generate_env = input("\nGenerate optimized .env file? (y/n): ").lower().strip()
    if generate_env == 'y':
        env_content = optimizer.generate_env_file(config)
        with open('.env.optimized', 'w') as f:
            f.write(env_content)
        print("✅ Optimized configuration saved to .env.optimized")
        print("   Rename to .env to use these settings")

if __name__ == "__main__":
    main()

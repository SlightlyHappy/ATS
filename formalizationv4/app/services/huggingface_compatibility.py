"""
Compatibility layer for Hugging Face Hub API changes.
Handles the transition from cached_download to hf_hub_download.
"""
import logging

logger = logging.getLogger(__name__)

try:
    # Try the new API first (huggingface_hub >= 0.10.0)
    from huggingface_hub import hf_hub_download
    cached_download = hf_hub_download
    logger.info("Using new Hugging Face Hub API (hf_hub_download)")
except ImportError:
    try:
        # Fallback to old API (huggingface_hub < 0.10.0)
        from huggingface_hub import cached_download
        logger.info("Using legacy Hugging Face Hub API (cached_download)")
    except ImportError:
        # Last resort: create a dummy function to prevent import errors
        logger.warning("Neither hf_hub_download nor cached_download available, creating dummy function")
        def cached_download(*args, **kwargs):
            raise NotImplementedError("Hugging Face Hub download functionality not available")

# Export the function for use in other modules
__all__ = ['cached_download']

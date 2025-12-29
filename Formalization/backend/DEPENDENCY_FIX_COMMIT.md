fix: resolve numpy dependency conflicts in requirements.txt

- Changed numpy from ==2.0.1 to >=1.24.0,<2.0.0 to fix faiss-cpu compatibility
- Updated ML packages to use version ranges instead of strict pinning:
  - pandas: >=2.2.0,<2.3.0 
  - scikit-learn: >=1.5.0,<1.6.0
  - sentence-transformers: >=3.0.0,<3.1.0
  - faiss-cpu: >=1.8.0,<1.9.0
  - together: >=1.2.0,<1.3.0
- Added test_dependencies.py script for deployment verification
- Enhanced Dockerfile with comprehensive dependency testing
- Resolves Railway deployment failure due to ResolutionImpossible error

The main issue was faiss-cpu 1.8.0.post1 requires numpy<2.0, but numpy was 
pinned to ==2.0.1. Using compatible version ranges allows pip to find a 
working solution while maintaining package stability.

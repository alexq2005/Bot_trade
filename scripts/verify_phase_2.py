import sys
import os
import importlib
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PHASE_2_VERIFIER")

def check_env_vars():
    logger.info("🔍 CHECK 1: Environment Variables")
    required_vars = ["IOL_USER", "IOL_PASSWORD"]
    missing = []
    
    # Load .env if present
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            
    if missing:
        logger.error(f"❌ MISSING ENV VARS: {missing}")
        return False
    logger.info("✅ Environment Variables Present")
    return True

def check_imports():
    logger.info("🔍 CHECK 2: Critical Imports & Circular Dependencies")
    modules_to_check = [
        "src.core.config",
        "src.services.price_service",
        "src.connectors.iol_client",
        "dashboard", # May need path adjustment
        "src.services.prediction_service" 
    ]
    
    # Add root to path
    sys.path.append(os.path.abspath("."))
    
    for module in modules_to_check:
        try:
            logger.info(f"   Importing {module}...")
            importlib.import_module(module)
        except ImportError as e:
            logger.error(f"❌ IMPORT ERROR in {module}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR importing {module}: {e}")
            return False
    
    logger.info("✅ All Critical Modules Imported Successfully")
    return True

def dry_run_iol():
    logger.info("🔍 CHECK 3: IOL Connectivity (Smoke Test)")
    try:
        from src.connectors.iol_client import IOLClient
        client = IOLClient()
        # Just check if we can get a token or if it's initialized
        if hasattr(client, 'access_token'):
             logger.info("✅ IOL Client Initialized")
        else:
             logger.warning("⚠️ IOL Client initialized but state unclear")
    except Exception as e:
        logger.error(f"❌ IOL Client Initialization Failed: {e}")
        return False
    return True

def verify_ml_deps():
    logger.info("🔍 CHECK 4: ML Dependencies")
    try:
        import tensorflow as tf
        import sklearn
        import numpy as np
        logger.info(f"✅ TensorFlow {tf.__version__} Available")
        logger.info(f"✅ Scikit-learn {sklearn.__version__} Available")
        logger.info(f"✅ NumPy {np.__version__} Available")
    except ImportError as e:
        logger.error(f"❌ ML Dependency Missing: {e}")
        return False
    return True

def main():
    logger.info("🚀 STARTING PHASE 2 SMOKE TESTS")
    checks = [
        check_env_vars(),
        check_imports(),
        verify_ml_deps(),
        dry_run_iol()
    ]
    
    if all(checks):
        logger.info("\n🎉 PASSED: System seems structurally sound (Phase 2 OK)")
        logger.info("Next Step: Execute Phase 3 (Logic Audit)")
    else:
        logger.error("\n💥 FAILED: Fix the errors above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()

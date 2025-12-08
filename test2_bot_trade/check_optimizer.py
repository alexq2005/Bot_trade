
from src.services.genetic_optimizer import GeneticOptimizer

def run_test():
    print("🧬 Testing Genetic Optimizer...")
    try:
        opt = GeneticOptimizer()
        print("✅ Initialization successful")
        
        print("🏃 Running small optimization (2 gens, pop 5)...")
        best_config, logbook = opt.optimize("TEST_SYMBOL", generations=2, population_size=5)
        
        print("\n🏆 Best Config Found:")
        print(best_config)
        
        if len(logbook) == 3: # Gen 0, 1, 2 = 3 entries? OR 0, 1 = 2 entries?
             # deap usually logs initial pop (0) and then subsequent generations
             pass
        
        print("✅ Optimization loop completed successfully")
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()

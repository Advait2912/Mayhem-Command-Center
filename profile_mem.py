import sys
import pickle
import pandas as pd
import tempfile
import os

from backend.services.inference import load_artifacts

def mb(bytes_val):
    return bytes_val / (1024 * 1024)

def catboost_size(model):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        model.save_model(f.name)
        size = os.path.getsize(f.name)
    os.unlink(f.name)
    return size

def xgb_size(model):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        model.save_model(f.name)
        size = os.path.getsize(f.name)
    os.unlink(f.name)
    return size

def run_profiling():
    print("Loading artifacts (this may take ~15 seconds)...")
    ctx = load_artifacts()
    
    print("\n--- Memory Usage Profiling ---")
    
    # 1. events dataframe
    df_mem = ctx.df_hist.memory_usage(deep=True).sum()
    print(f"events dataframe: {mb(df_mem):.2f} MB")
    
    # 2. graph object
    g_pickled = pickle.dumps(ctx.G)
    g_main_pickled = pickle.dumps(ctx.G_main)
    print(f"graph object (G): {mb(len(g_pickled)):.2f} MB (pickled approx)")
    print(f"graph object (G_main): {mb(len(g_main_pickled)):.2f} MB (pickled approx)")
    
    # 3. CBR structures
    cbr_pickled = pickle.dumps(ctx.cbr_artifacts)
    print(f"CBR structures: {mb(len(cbr_pickled)):.2f} MB (pickled approx)")
    
    # 4. loaded models
    closure_mem = catboost_size(ctx.closure_model)
    priority_mem = catboost_size(ctx.priority_model)
    fast_mem = sum(xgb_size(m) for m in ctx.fast_models.values())
    aft_pickled = len(pickle.dumps(ctx.aft_final))
    
    models_total = closure_mem + priority_mem + fast_mem + aft_pickled
    print(f"loaded models (total): {mb(models_total):.2f} MB")
    print(f"  - closure_model (CatBoost): {mb(closure_mem):.2f} MB")
    print(f"  - priority_model (CatBoost): {mb(priority_mem):.2f} MB")
    print(f"  - fast_models (XGBoost quantiles): {mb(fast_mem):.2f} MB")
    print(f"  - aft_final (Lifelines): {mb(aft_pickled):.2f} MB")
    
    # 5. Other dictionaries
    cent_mem = sys.getsizeof(ctx.centrality) + sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in ctx.centrality.items())
    base_mem = len(pickle.dumps(ctx.baseline_table))
    print(f"other metadata (centrality, baseline): {mb(cent_mem + base_mem):.2f} MB")
    
    total_approx = mb(df_mem + len(g_pickled) + len(g_main_pickled) + len(cbr_pickled) + models_total + cent_mem + base_mem)
    print(f"\nTotal approximated memory: {total_approx:.2f} MB")

if __name__ == "__main__":
    run_profiling()

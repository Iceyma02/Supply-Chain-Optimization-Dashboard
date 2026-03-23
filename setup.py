#!/usr/bin/env python3
"""
One-command project setup
Run: python setup.py
"""
import subprocess, sys, os

def run(cmd, desc):
    print(f"\n{'='*55}")
    print(f"  {desc}")
    print(f"{'='*55}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"  ✗ Failed: {cmd}")
        sys.exit(1)
    print(f"  ✓ Done")

print("\n🚛  SUPPLY CHAIN OPTIMIZER — PROJECT SETUP")
print("=" * 55)

run("pip install -r requirements.txt",           "Installing dependencies")
run("python data/generate_dataset.py",           "Generating 3-year dataset")
run("python src/preprocessing.py",              "Running preprocessing pipeline")
run("python src/model_training.py",             "Training XGBoost model")
run("python src/route_map.py",                  "Building route map")

print("\n" + "="*55)
print("  ✅  SETUP COMPLETE")
print("="*55)
print("\n  Start the dashboard:")
print("  python src/dashboard.py")
print("\n  Then open: http://localhost:8050")
print()

#!/bin/bash
# When RLHF Fails Quietly - Reproduction Script
#
# This script demonstrates the evaluation harness on local models.
# Prerequisites: Ollama installed with llama3.1 and mistral models
#
# Usage: ./reproduce.sh

set -e

echo "=================================================="
echo "When RLHF Fails Quietly - Reproduction Script"
echo "=================================================="

# Install dependencies
echo "[1/5] Installing dependencies..."
pip install -r requirements.txt --quiet

# Verify setup
echo "[2/5] Verifying scenario setup..."
python run_evals.py --list-scenarios

# Run single-model evaluation
echo "[3/5] Running epistemic compliance evaluation..."
python run_evals.py --model ollama:llama3.1 --scenario epistemic_compliance -v

# Run trajectory evaluation
echo "[4/5] Running intent drift trajectory evaluation..."
python run_evals.py --model ollama:llama3.1 --scenario intent_drift --trajectory

# Run model comparison
echo "[5/5] Running cross-model comparison..."
python run_evals.py --models ollama:llama3.1,ollama:mistral --scenario reward_hacking

# Generate report
echo "=================================================="
echo "Generating final report..."
python run_evals.py --report results/evals/

echo "=================================================="
echo "Reproduction complete. Results in results/evals/"
echo "=================================================="

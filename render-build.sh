#!/bin/bash
set -e

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Running database migrations..."
alembic upgrade head  # ← AGREGAR ESTO

echo "🌱 Running database seed..."
python -m scripts.seed_cevicheria_data

echo "✅ Build completed successfully!"
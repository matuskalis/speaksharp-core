#!/bin/bash
# Apply database schema to Railway PostgreSQL
# Usage: ./apply_schema.sh

echo "This script will apply the database schema to Railway PostgreSQL"
echo ""
echo "To use this script:"
echo "1. Get your DATABASE_URL from Railway dashboard"
echo "2. Run: export DATABASE_URL='postgresql://...'"
echo "3. Run: ./apply_schema.sh"
echo ""

if [ -z "$DATABASE_URL" ]; then
  echo "❌ ERROR: DATABASE_URL environment variable is not set"
  echo ""
  echo "Get it from Railway:"
  echo "  1. Go to https://railway.app"
  echo "  2. Open your PostgreSQL service"
  echo "  3. Go to Variables tab"
  echo "  4. Copy the DATABASE_URL value"
  echo ""
  exit 1
fi

echo "Applying schema to database..."
psql "$DATABASE_URL" < database/schema.sql

if [ $? -eq 0 ]; then
  echo "✅ Schema applied successfully!"
  echo ""
  echo "Verifying tables..."
  psql "$DATABASE_URL" -c "\dt"
else
  echo "❌ Failed to apply schema"
  exit 1
fi

#!/usr/bin/env python3
"""
Apply database schema to Railway PostgreSQL
Usage: python apply_schema.py
"""

import os
import sys
import psycopg

def main():
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set\n")
        print("To fix this:")
        print("1. Go to https://railway.app")
        print("2. Open your PostgreSQL service")
        print("3. Go to 'Variables' or 'Connect' tab")
        print("4. Copy the DATABASE_URL value")
        print("5. Run: export DATABASE_URL='your-url-here'")
        print("6. Then run this script again\n")
        sys.exit(1)

    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")

    if not os.path.exists(schema_path):
        print(f"❌ ERROR: Schema file not found at {schema_path}")
        sys.exit(1)

    print(f"📖 Reading schema from {schema_path}...")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    print(f"📊 Schema size: {len(schema_sql)} characters\n")

    # Connect to database
    print(f"🔌 Connecting to database...")
    print(f"   Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'unknown'}\n")

    try:
        with psycopg.connect(database_url) as conn:
            print("✅ Connected successfully!\n")

            with conn.cursor() as cur:
                print("🚀 Applying schema (this may take 10-20 seconds)...\n")

                # Execute the schema
                cur.execute(schema_sql)
                conn.commit()

                print("✅ Schema applied successfully!\n")

                # Verify tables were created
                print("🔍 Verifying tables...")
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                """)

                tables = cur.fetchall()

                if tables:
                    print(f"\n✅ Found {len(tables)} tables:")
                    for table in tables:
                        print(f"   ✓ {table[0]}")

                    print("\n🎉 Database setup complete!")
                    print("\nYou can now:")
                    print("   • Refresh your website at https://speaksharp-frontend.vercel.app")
                    print("   • All database errors should be gone")
                    print("   • All features should work properly")
                else:
                    print("\n⚠️  Warning: No tables found. Something may have gone wrong.")

    except psycopg.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check:")
        print("   • DATABASE_URL is correct")
        print("   • You have internet connection")
        print("   • Railway database is running")
        sys.exit(1)

    except psycopg.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

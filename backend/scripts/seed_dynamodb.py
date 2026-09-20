#!/usr/bin/env python
"""Seed script for CONTINUITY DynamoDB table.

Populates the DynamoDB table with canonical workplace demo cases (CASE-1042, CASE-1038,
CASE-8821, CASE-1050, CASE-1055) used by the CONTINUITY UI.

Usage:
    python scripts/seed_dynamodb.py [--force]
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.repositories.dynamodb_repository import DynamoDBRepository
from app.repositories.memory_repository import InMemoryRepository

def seed_dynamodb(force: bool = False):
    table_name = os.getenv("DYNAMODB_TABLE", "continuity-cases-dev")
    region = os.getenv("AWS_REGION", "ap-south-1")

    print(f"=== CONTINUITY DynamoDB Seeder ===")
    print(f"Target Table: {table_name}")
    print(f"Target Region: {region}\n")

    repo = DynamoDBRepository(table_name=table_name, region=region)

    # 1. Connectivity Check
    print("Checking DynamoDB table connectivity...")
    health = repo.health_check()
    if health.get("status") != "healthy":
        print(f"ERROR: DynamoDB table '{table_name}' is not reachable.")
        print(f"Details: {health.get('error')}")
        print("\nPlease ensure:")
        print("  1. The table exists: see infrastructure/README.md for the 'aws dynamodb create-table' command.")
        print("  2. Your AWS credentials are configured via standard boto3 credential chain.")
        sys.exit(1)

    print(f"Connected to table '{table_name}' (Status: {health.get('table_status')}).")

    # 2. Check Existing Items
    existing_cases = repo.get_all_cases()
    if existing_cases and not force:
        print(f"\nWARNING: Table already contains {len(existing_cases)} cases:")
        for c in existing_cases:
            print(f"  - {c.case_id}: {c.title} ({c.status})")
        print("\nAborting seed to prevent overwriting existing data.")
        print("To overwrite/reseed, run with the --force flag: python scripts/seed_dynamodb.py --force")
        return

    # 3. Obtain canonical demo cases from memory repository seed data
    memory_repo = InMemoryRepository(seed=True)
    demo_cases = memory_repo.get_all_cases()

    print(f"\nSeeding {len(demo_cases)} demo cases into DynamoDB...")
    for case in demo_cases:
        repo.save_case(case)
        print(f"  [SEEDED] {case.case_id} — {case.title} (Owner: {case.owner}, Status: {case.status})")

    print("\nSUCCESS: All demo cases successfully seeded into DynamoDB!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed DynamoDB with CONTINUITY demo cases.")
    parser.add_argument("--force", action="store_true", help="Overwrite/update existing cases in DynamoDB.")
    args = parser.parse_args()
    seed_dynamodb(force=args.force)

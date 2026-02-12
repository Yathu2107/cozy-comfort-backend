#!/usr/bin/env python3
"""
Database migration helper script for Cozy Comfort API
"""
import sys
import subprocess
import argparse

def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False

def create_migration(message):
    """Create a new migration file."""
    print(f"Creating migration: {message}")
    command = f'alembic revision --autogenerate -m "{message}"'
    return run_command(command)

def upgrade_database(revision="head"):
    """Upgrade database to specified revision."""
    print(f"Upgrading database to revision: {revision}")
    command = f"alembic upgrade {revision}"
    return run_command(command)

def downgrade_database(revision):
    """Downgrade database to specified revision."""
    print(f"Downgrading database to revision: {revision}")
    command = f"alembic downgrade {revision}"
    return run_command(command)

def show_current_revision():
    """Show current database revision."""
    print("Current database revision:")
    command = "alembic current"
    return run_command(command)

def show_migration_history():
    """Show migration history."""
    print("Migration history:")
    command = "alembic history"
    return run_command(command)

def main():
    parser = argparse.ArgumentParser(description="Database migration helper for Cozy Comfort API")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument("--revision", default="head", help="Target revision (default: head)")

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument("revision", help="Target revision")

    # Current command
    subparsers.add_parser("current", help="Show current revision")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if args.command == "create":
        create_migration(args.message)
    elif args.command == "upgrade":
        upgrade_database(args.revision)
    elif args.command == "downgrade":
        downgrade_database(args.revision)
    elif args.command == "current":
        show_current_revision()
    elif args.command == "history":
        show_migration_history()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

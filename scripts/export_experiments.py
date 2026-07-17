#!/usr/bin/env python3
"""CLI script to export experiment history from SQLite database to CSV or JSON format."""

import asyncio
import csv
import json
import sys
from pathlib import Path

import aiosqlite
import click

DEFAULT_DB_PATH = "experiments.sqlite"


async def export_data(db_path: str, fmt: str, output: str | None, run_id: str | None):
    """Query experiments database and write out the result to the designated format."""
    db_file = Path(db_path)
    if not db_file.exists():
        click.echo(f"Error: Database file not found at {db_path}", err=True)
        sys.exit(1)

    query = "SELECT * FROM experiments"
    params = []
    if run_id:
        query += " WHERE run_id = ?"
        params.append(run_id)

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        try:
            async with conn.execute(query, params) as cursor:
                headers = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
        except aiosqlite.OperationalError as e:
            # Handle cases where table does not exist or db is uninitialized
            click.echo(f"Error reading database: {e}", err=True)
            sys.exit(1)

    # Determine actual output path
    if not output:
        output = f"reports/experiments.{fmt}"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        click.echo("Warning: No matching experiments found in the database.")

    if fmt == "csv":
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        click.echo(f"Successfully exported {len(rows)} experiments to {output_path} (CSV)")

    elif fmt == "json":
        data = []
        for row in rows:
            row_dict = dict(row)
            # Convert JSON strings to objects where appropriate for clean JSON output
            for json_col in ["config_json", "metrics_json"]:
                val = row_dict.get(json_col)
                if val:
                    try:
                        row_dict[json_col] = json.loads(val)
                    except json.JSONDecodeError:
                        pass
            data.append(row_dict)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        click.echo(f"Successfully exported {len(rows)} experiments to {output_path} (JSON)")


@click.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["csv", "json"], case_sensitive=False),
    default="csv",
    show_default=True,
    help="The output format (csv or json).",
)
@click.option(
    "--output",
    type=click.Path(writable=True, path_type=str),
    help="Destination file path. Defaults to reports/experiments.{csv|json}",
)
@click.option(
    "--run-id",
    help="Filter exports to a specific run ID.",
)
@click.option(
    "--db-path",
    default=DEFAULT_DB_PATH,
    show_default=True,
    help="Path to the SQLite database.",
)
def main(fmt: str, output: str | None, run_id: str | None, db_path: str):
    """Export experiment history from SQLite to CSV or JSON."""
    asyncio.run(export_data(db_path, fmt.lower(), output, run_id))


if __name__ == "__main__":
    main()

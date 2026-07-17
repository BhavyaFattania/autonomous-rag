#!/usr/bin/env python3
"""CLI script to shrink graphify's graph.html by moving its embedded data to a sidecar file.

graphify's HTML exporter (graphify/exporters/html.py, a third-party package) inlines
RAW_NODES/RAW_EDGES/LEGEND/hyperedges as literal JS arrays directly inside graph.html's
<script> tags, so the whole node/edge/legend payload ships as page text (~1MB) every time
the file is opened. This script extracts those four arrays into a sidecar graph-data.js
next to graph.html and rewrites graph.html to pull them in via <script src="graph-data.js">
instead of inlining them.

A plain <script src> (not fetch()) is used deliberately: graph.html is opened directly via
file://, and fetch()/XHR against a local file is blocked by same-origin/CORS restrictions in
Chrome and Firefox, whereas a same-directory <script src> tag is not — so this keeps
double-click-to-view working with no local HTTP server required.

Does not touch the installed graphify package or change its regeneration behavior. Re-run
this after any `graphify --update` to re-split the freshly regenerated monolithic graph.html.
"""

import json
import sys
from pathlib import Path

import click

DEFAULT_HTML_PATH = "graphify-out/index.html"
DEFAULT_DATA_FILENAME = "graph-data.js"

MARKERS = ["RAW_NODES", "RAW_EDGES", "LEGEND", "hyperedges"]


def _extract_json_value(text: str, start: int) -> tuple[object, int]:
    """Parse one JSON array/object starting at `start`, honoring string/escape state.

    Returns (parsed_value, index_just_past_the_closing_bracket). A naive search for a
    literal "];" terminator can land inside a string value instead of the real array end
    (graphify escapes "</" as "<\\/" inside strings, and titles can contain "];" verbatim).
    """
    depth = 0
    in_string = False
    escape = False
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    return json.loads(text[start:end]), end
        i += 1
    raise ValueError(f"Unterminated JSON value starting at offset {start}")


def _find_assignment(text: str, name: str, search_from: int = 0) -> tuple[int, int, object]:
    """Locate `const {name} = <value>;` and return (stmt_start, stmt_end, value).

    stmt_start/stmt_end span the whole statement, including the trailing semicolon and
    the newline immediately after it (if present), so callers can delete it cleanly.
    """
    marker = f"const {name} = "
    idx = text.find(marker, search_from)
    if idx == -1:
        raise ValueError(f"Could not find `{marker}` — index.html format may have changed")
    value_start = idx + len(marker)
    value, value_end = _extract_json_value(text, value_start)
    end = value_end
    if end < len(text) and text[end] == ";":
        end += 1
    if end < len(text) and text[end] == "\n":
        end += 1
    return idx, end, value


def split_graph_html(html_text: str, data_filename: str) -> tuple[str, dict]:
    """Return (patched_html, extracted_data) with all four arrays pulled out into JSON."""
    extracted = {}
    spans = []
    search_from = 0
    for name in MARKERS:
        stmt_start, stmt_end, value = _find_assignment(html_text, name, search_from)
        extracted[name] = value
        spans.append((stmt_start, stmt_end))
        search_from = stmt_end

    # Delete the four assignment statements, working back-to-front so earlier offsets
    # stay valid while later ones are removed.
    patched = html_text
    for start, end in sorted(spans, reverse=True):
        patched = patched[:start] + patched[end:]

    # Insert the sidecar <script src> right before the first <script> tag that used to
    # hold the data — later script tags in the same document share that global scope.
    first_stmt_start = min(s for s, _ in spans)
    script_tag_start = patched.rfind("<script>", 0, first_stmt_start)
    if script_tag_start == -1:
        raise ValueError("Could not locate the <script> tag preceding the extracted data")
    injection = f'<script src="{data_filename}"></script>\n'
    patched = patched[:script_tag_start] + injection + patched[script_tag_start:]

    return patched, extracted


@click.command()
@click.option(
    "--html-path",
    default=DEFAULT_HTML_PATH,
    show_default=True,
    type=click.Path(exists=False, path_type=str),
    help="Path to the graphify-generated index.html to split (rewritten in place).",
)
@click.option(
    "--data-filename",
    default=DEFAULT_DATA_FILENAME,
    show_default=True,
    help="Filename for the sidecar JS data file, written next to --html-path.",
)
def main(html_path: str, data_filename: str):
    """Shrink graph.html by moving its embedded node/edge/legend data to a sidecar .js file."""
    html_file = Path(html_path)
    if not html_file.exists():
        click.echo(f"Error: {html_path} not found", err=True)
        sys.exit(1)

    original_size = html_file.stat().st_size
    html_text = html_file.read_text(encoding="utf-8")

    if 'src="' + data_filename + '"' in html_text:
        click.echo(f"{html_path} already references {data_filename} — nothing to do.")
        return

    try:
        patched_html, extracted = split_graph_html(html_text, data_filename)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    data_js = "".join(
        f"const {name} = {json.dumps(extracted[name], separators=(',', ':'))};\n"
        for name in MARKERS
    )

    data_path = html_file.parent / data_filename
    data_path.write_text(data_js, encoding="utf-8")
    html_file.write_text(patched_html, encoding="utf-8")

    new_html_size = len(patched_html.encode("utf-8"))
    data_size = data_path.stat().st_size
    click.echo(
        f"{html_path}: {original_size:,} bytes -> {new_html_size:,} bytes\n"
        f"{data_path}: {data_size:,} bytes (new)"
    )


if __name__ == "__main__":
    main()

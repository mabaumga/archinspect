#!/usr/bin/env python3
"""
Extract Git repositories from HTML files in testdata directory.
Each HTML file contains multiple files separated by --- markers with FILEPATH headers.
"""
import os
import re
from pathlib import Path


def extract_repo_name(filename):
    """Extract repository name from filename like '2025-08-25_arvendatenkurier-main.md.html'"""
    # Remove date prefix and extension
    name = re.sub(r'^\d{4}-\d{2}-\d{2}_', '', filename)
    name = re.sub(r'\.md\.html$', '', name)
    # Remove branch suffix like -main, -develop, -dev
    name = re.sub(r'-(main|develop|dev)$', '', name)
    return name


def parse_html_file(filepath):
    """Parse HTML file and extract all files with their paths and contents"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    files = []
    # Split by --- markers
    sections = content.split('\n---\n')

    for section in sections:
        if not section.strip():
            continue

        # Look for FILEPATH marker
        filepath_match = re.search(r'# FILEPATH (.+)', section)
        if not filepath_match:
            continue

        file_path = filepath_match.group(1).strip()

        # Extract content after the FILEPATH line and language marker
        lines = section.split('\n')
        filepath_line_idx = None
        for i, line in enumerate(lines):
            if '# FILEPATH' in line:
                filepath_line_idx = i
                break

        if filepath_line_idx is None:
            continue

        # Skip the FILEPATH line and the next line (language marker like 'java')
        content_start = filepath_line_idx + 2
        file_content = '\n'.join(lines[content_start:])

        # Clean up the path - remove temp_extracted prefix if present
        file_path = re.sub(r'^temp_extracted_[^/]+/', '', file_path)
        # Also remove the repo name prefix if it's duplicated
        file_path = re.sub(r'^[^/]+-main/', '', file_path)
        # Remove any absolute Windows or Linux paths
        file_path = re.sub(r'^/mnt/c/[^/]+/', '', file_path)
        file_path = re.sub(r'^[A-Z]:[/\\]', '', file_path)
        file_path = re.sub(r'^/', '', file_path)
        # Remove common project path prefixes
        file_path = re.sub(r'^.*?/repos2?/[^/]+/[^/]+/', '', file_path)

        files.append({
            'path': file_path,
            'content': file_content
        })

    return files


def write_files_to_repo(files, repo_path):
    """Write extracted files to repository directory"""
    repo_path = Path(repo_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    for file_info in files:
        file_path = repo_path / file_info['path']

        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_info['content'])

        print(f"  Wrote: {file_path}")


def main():
    testdata_dir = Path('testdata')
    repos_dir = testdata_dir / 'repos'

    # Find all HTML files
    html_files = list(testdata_dir.glob('*.html'))

    if not html_files:
        print("No HTML files found in testdata directory")
        return

    print(f"Found {len(html_files)} HTML files")

    for html_file in html_files:
        print(f"\nProcessing: {html_file.name}")

        # Extract repo name
        repo_name = extract_repo_name(html_file.name)
        print(f"  Repository name: {repo_name}")

        # Parse HTML file
        files = parse_html_file(html_file)
        print(f"  Found {len(files)} files")

        # Write to repo directory
        repo_path = repos_dir / repo_name
        write_files_to_repo(files, repo_path)

        print(f"  ✓ Extracted to: {repo_path}")

    print(f"\n✓ All repositories extracted to {repos_dir}")


if __name__ == '__main__':
    main()

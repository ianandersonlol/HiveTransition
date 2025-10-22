#!/usr/bin/env python3
"""
Script to generate a GitHub issue URL for reporting broken scripts.
Usage: python broken.py <script_filename>
"""

import sys
import os
import urllib.parse
from pathlib import Path


def create_issue_url(script_path):
    """Create a GitHub issue URL with pre-filled content."""
    
    # Read the script content
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()
    except Exception as e:
        print(f"Error reading file '{script_path}': {e}")
        return None
    
    # Get absolute path for clarity
    abs_path = os.path.abspath(script_path)
    
    # Create the issue body
    issue_body = f"""## Script
```bash
{script_content}
```

## What happened? What should have happened?
<!-- Describe what went wrong and what you expected to happen -->

---
**Script path:** `{abs_path}`
**Submitted using:** `broken.py`
"""

    # Create the issue title
    script_name = Path(script_path).name
    issue_title = f"[BUG] Script issue: {script_name}"
    
    # GitHub issue parameters
    params = {
        'title': issue_title,
        'body': issue_body,
        'labels': 'bug',
        'assignees': 'ianandersonlol'
    }
    
    # Encode parameters for URL
    encoded_params = urllib.parse.urlencode(params)
    
    # GitHub new issue URL
    base_url = "https://github.com/ianandersonlol/HiveTransition/issues/new"
    full_url = f"{base_url}?{encoded_params}"
    
    return full_url


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python broken.py <script_filename>")
        print("\nThis script generates a GitHub issue URL for reporting broken scripts.")
        print("The URL will be pre-filled with:")
        print("  - The script content")
        print("  - The script path")
        print("  - Auto-assignment to ianandersonlol")
        print("  - Bug label")
        print("\nExample: python broken.py my_broken_script.sh")
        sys.exit(1)
    
    script_filename = sys.argv[1]
    
    if not os.path.exists(script_filename):
        print(f"Error: File '{script_filename}' not found.")
        sys.exit(1)
    
    # Generate the URL
    url = create_issue_url(script_filename)
    
    if url:
        print("GitHub issue URL generated successfully!")
        print("\nCopy and paste this URL into your browser:")
        print("-" * 80)
        print(url)
        print("-" * 80)
        print("\nNote: The URL might be very long due to the script content.")
        print("If the URL is too long for your browser, you can:")
        print("1. Go to: https://github.com/ianandersonlol/HiveTransition/issues/new")
        print("2. Manually fill in the issue with the script content")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
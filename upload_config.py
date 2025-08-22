#!/usr/bin/env python3
"""
Upload config.py directly to GitHub using API
"""
import requests
import base64
import json

def upload_config_to_github():
    """Upload config.py file to GitHub repository"""
    
    # Read the config.py file
    with open('config.py', 'r') as f:
        content = f.read()
    
    # Encode content
    encoded_content = base64.b64encode(content.encode()).decode()
    
    # GitHub API URL
    url = "https://api.github.com/repos/inventor01/Front4/contents/config.py"
    
    # Prepare payload
    payload = {
        "message": "Add missing config.py for Railway Discord bot fix",
        "content": encoded_content,
        "branch": "main"
    }
    
    # You would need a GitHub token for this to work
    # headers = {"Authorization": "token YOUR_GITHUB_TOKEN"}
    
    print("Config file ready for upload:")
    print(f"Content size: {len(content)} characters")
    print(f"Encoded size: {len(encoded_content)} characters")
    print("\nTo upload manually:")
    print("1. Go to https://github.com/inventor01/Front4")
    print("2. Click 'Add file' → 'Create new file'")
    print("3. Filename: config.py")
    print("4. Copy the config.py content from your workspace")
    print("5. Commit with message: 'Add config.py for Discord bot fix'")

if __name__ == "__main__":
    upload_config_to_github()
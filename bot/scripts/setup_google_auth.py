#!/usr/bin/env python3
"""
Google Calendar OAuth2 Setup Script

This script helps you obtain the refresh token needed for Google Calendar API access.

Prerequisites:
1. Create a project in Google Cloud Console
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials.json

Usage:
    python scripts/setup_google_auth.py

This will:
1. Open browser for Google OAuth consent
2. Generate refresh token
3. Display credentials to add to .env file
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import os

# Scopes required for calendar access
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]


def get_refresh_token():
    """Run OAuth flow to get refresh token"""

    # Check for credentials file
    credentials_path = 'credentials.json'
    if not os.path.exists(credentials_path):
        print("❌ Error: credentials.json not found!")
        print("\nPlease:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com")
        print("2. Create a new project or select existing")
        print("3. Enable Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download credentials and save as 'credentials.json' in bot/ directory")
        return

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path,
        SCOPES
    )

    print("🔐 Starting Google OAuth flow...")
    print("Your browser will open for authorization.")
    print("Please grant access to Google Calendar.\n")

    # This will open browser and wait for authorization
    creds = flow.run_local_server(port=0)

    # Extract credentials
    client_config = json.loads(open(credentials_path).read())
    client_info = client_config.get('installed') or client_config.get('web')

    client_id = client_info['client_id']
    client_secret = client_info['client_secret']
    refresh_token = creds.refresh_token

    print("\n" + "="*60)
    print("✅ SUCCESS! Google Calendar authenticated.")
    print("="*60)
    print("\nAdd these to your bot/.env file:\n")
    print(f"GOOGLE_CLIENT_ID={client_id}")
    print(f"GOOGLE_CLIENT_SECRET={client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
    print("\n" + "="*60)
    print("\n⚠️  IMPORTANT: Keep these credentials secret!")
    print("Do NOT commit them to version control.\n")

    # Save to a local file for reference
    with open('.google_credentials', 'w') as f:
        f.write(f"GOOGLE_CLIENT_ID={client_id}\n")
        f.write(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
        f.write(f"GOOGLE_REFRESH_TOKEN={refresh_token}\n")

    print("✅ Credentials also saved to .google_credentials")
    print("   (This file is in .gitignore)\n")


if __name__ == '__main__':
    get_refresh_token()

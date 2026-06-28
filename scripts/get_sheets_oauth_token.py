#!/usr/bin/env python3
"""
One-time helper to mint a Google Sheets OAuth refresh token.

The settings spreadsheet lives in a Workspace whose sharing policy blocks the
Cloud Run service account, so the Worker reads the sheet as an authorized
*user* instead. This script runs the OAuth consent flow locally (in your
browser, as an account that can view the sheet) and writes the resulting
credentials as JSON so they can be stored in Secret Manager.

Prerequisites:
  1. In the GCP Console, create an OAuth 2.0 Client ID of type "Desktop app"
     and download its client-secret JSON.
  2. Set the OAuth consent screen User type to "Internal" so the refresh token
     does not expire under the 7-day "Testing" rule.

Usage:
  uv run python scripts/get_sheets_oauth_token.py <client_secret.json> <output.json>

The output JSON contains: client_id, client_secret, refresh_token.
All human-readable progress is printed to stderr; nothing secret is printed to
stdout.
"""

import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    client_secret_path, output_path = argv[1], argv[2]

    print("Opening browser for Google authorization...", file=sys.stderr)
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    # Force a consent prompt so a refresh_token is always returned.
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    if not creds.refresh_token:
        print(
            "ERROR: No refresh token was returned. Revoke prior grants and "
            "retry, ensuring access_type=offline and prompt=consent.",
            file=sys.stderr,
        )
        return 1

    payload = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    print(f"Wrote OAuth credentials to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

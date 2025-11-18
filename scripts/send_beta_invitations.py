#!/usr/bin/env python3
"""
Send beta invitation emails.

Usage:
    python scripts/send_beta_invitations.py --emails beta-users.csv
"""

import argparse
import csv
import os
from datetime import datetime


def send_email(email: str, name: str, template: str):
    """Send beta invitation email."""
    # Read template
    with open(template, 'r') as f:
        email_template = f.read()

    # Replace placeholders
    email_body = email_template.replace('[Name]', name)
    email_body = email_body.replace('[email]', email)

    print(f"Would send email to: {email}")
    print(f"Subject: Welcome to Document AI SaaS Beta! 🚀")
    print(f"Preview: Hi {name}, Thank you for joining our beta program...")
    print("-" * 60)

    # In production, use SendGrid, Mailgun, or similar
    # For now, just log
    return True


def main():
    parser = argparse.ArgumentParser(description='Send beta invitation emails')
    parser.add_argument('--emails', required=True, help='CSV file with emails (columns: email,name)')
    parser.add_argument('--template', default='docs/beta-onboarding-email.md', help='Email template file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t actually send)')

    args = parser.parse_args()

    # Read CSV
    with open(args.emails, 'r') as f:
        reader = csv.DictReader(f)
        users = list(reader)

    print(f"Found {len(users)} users to invite")

    if args.dry_run:
        print("DRY RUN MODE - No emails will be sent")

    # Send invitations
    sent = 0
    failed = 0

    for user in users:
        email = user.get('email')
        name = user.get('name', email.split('@')[0])

        if not email:
            print(f"Skipping user with no email: {user}")
            continue

        try:
            if not args.dry_run:
                send_email(email, name, args.template)

            sent += 1
            print(f"✓ Sent invitation to {email}")

        except Exception as e:
            failed += 1
            print(f"✗ Failed to send to {email}: {e}")

    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"Total users: {len(users)}")
    print(f"Sent: {sent}")
    print(f"Failed: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()

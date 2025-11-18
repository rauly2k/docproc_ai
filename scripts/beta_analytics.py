#!/usr/bin/env python3
"""
Generate beta analytics report.

Usage:
    python scripts/beta_analytics.py
"""

from sqlalchemy import func, create_engine, case
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.shared.models import Tenant, Document, User
from backend.shared.config import get_settings

settings = get_settings()


def generate_beta_report():
    """Generate comprehensive beta usage report."""

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Date range
    beta_start = datetime.now() - timedelta(days=14)  # Last 14 days
    beta_end = datetime.now()

    print("=" * 60)
    print("BETA ANALYTICS REPORT")
    print(f"Period: {beta_start.date()} to {beta_end.date()}")
    print("=" * 60)

    # 1. User Signup and Activation
    total_signups = db.query(func.count(Tenant.id)).filter(
        Tenant.created_at >= beta_start,
        Tenant.created_at <= beta_end
    ).scalar()

    active_users = db.query(func.count(func.distinct(Document.tenant_id))).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).scalar()

    print(f"\n📊 USER METRICS")
    print(f"Total Signups: {total_signups}")
    print(f"Active Users (uploaded ≥1 doc): {active_users}")
    if total_signups > 0:
        print(f"Activation Rate: {active_users/total_signups*100:.1f}%")

    # 2. Document Processing
    doc_stats = db.query(
        Document.document_type,
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).group_by(Document.document_type).all()

    print(f"\n📄 DOCUMENTS PROCESSED")
    total_docs = 0
    for doc_type, count in doc_stats:
        print(f"{doc_type or 'unknown'}: {count}")
        total_docs += count
    print(f"TOTAL: {total_docs}")

    # 3. Processing Status
    status_stats = db.query(
        Document.status,
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).group_by(Document.status).all()

    print(f"\n📈 PROCESSING STATUS")
    for status, count in status_stats:
        print(f"{status}: {count}")

    # 4. Daily Active Users
    dau = db.query(
        func.date(Document.created_at).label('date'),
        func.count(func.distinct(Document.tenant_id)).label('users')
    ).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).group_by(func.date(Document.created_at)).all()

    print(f"\n📅 DAILY ACTIVE USERS")
    for date, users in sorted(dau, key=lambda x: x[0]):
        print(f"{date}: {users} users")

    # 5. Average Documents per User
    if active_users > 0:
        avg_docs = total_docs / active_users
        print(f"\n📊 AVERAGE DOCUMENTS PER USER: {avg_docs:.1f}")

    db.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        generate_beta_report()
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()

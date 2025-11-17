#!/usr/bin/env python3
"""
Generate beta analytics report (Phase 7.6).

Usage:
    python scripts/beta_analytics.py
    python scripts/beta_analytics.py --output=report.html
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from shared.config import get_settings
from shared.models import (
    Tenant, Document, ProcessingJob, InvoiceData,
    DocumentSummary, ChatMessage, ChatSession
)

settings = get_settings()


def generate_beta_report(beta_start_date: datetime, beta_end_date: datetime):
    """Generate comprehensive beta usage report."""

    # Connect to database
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("=" * 70)
    print("BETA ANALYTICS REPORT")
    print(f"Period: {beta_start_date.date()} to {beta_end_date.date()}")
    print("=" * 70)

    # 1. User Signup and Activation
    total_signups = db.query(func.count(Tenant.id)).filter(
        Tenant.created_at >= beta_start_date,
        Tenant.created_at <= beta_end_date
    ).scalar() or 0

    active_users = db.query(func.count(func.distinct(Document.tenant_id))).filter(
        Document.created_at >= beta_start_date,
        Document.created_at <= beta_end_date
    ).scalar() or 0

    activation_rate = (active_users / total_signups * 100) if total_signups > 0 else 0

    print(f"\n📊 USER METRICS")
    print(f"Total Signups: {total_signups}")
    print(f"Active Users (uploaded ≥1 doc): {active_users}")
    print(f"Activation Rate: {activation_rate:.1f}%")

    # 2. Document Processing
    doc_stats = db.query(
        Document.document_type,
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= beta_start_date,
        Document.created_at <= beta_end_date
    ).group_by(Document.document_type).all()

    total_docs = sum(count for _, count in doc_stats)

    print(f"\n📄 DOCUMENTS PROCESSED")
    print(f"Total Documents: {total_docs}")
    for doc_type, count in doc_stats:
        percentage = (count / total_docs * 100) if total_docs > 0 else 0
        print(f"  {doc_type}: {count} ({percentage:.1f}%)")

    # 3. Feature Usage
    feature_usage = db.query(
        ProcessingJob.job_type,
        func.count(ProcessingJob.id).label('count'),
        func.avg(ProcessingJob.processing_time_ms).label('avg_duration_ms')
    ).filter(
        ProcessingJob.created_at >= beta_start_date,
        ProcessingJob.created_at <= beta_end_date,
        ProcessingJob.status == 'completed'
    ).group_by(ProcessingJob.job_type).all()

    print(f"\n🎯 FEATURE USAGE")
    for job_type, count, avg_duration in feature_usage:
        avg_seconds = (avg_duration / 1000) if avg_duration else 0
        print(f"  {job_type}: {count} jobs (avg {avg_seconds:.1f}s)")

    # 4. Error Analysis
    error_stats = db.query(
        ProcessingJob.job_type,
        func.count(ProcessingJob.id).label('total'),
        func.sum(func.cast(ProcessingJob.status == 'failed', func.INTEGER)).label('failed')
    ).filter(
        ProcessingJob.created_at >= beta_start_date,
        ProcessingJob.created_at <= beta_end_date
    ).group_by(ProcessingJob.job_type).all()

    print(f"\n⚠️  ERROR RATES")
    for job_type, total, failed in error_stats:
        failed = failed or 0
        rate = (failed / total * 100) if total > 0 else 0
        status = "✅" if rate < 5 else "⚠️" if rate < 10 else "❌"
        print(f"  {status} {job_type}: {failed}/{total} ({rate:.1f}%)")

    # 5. Chat Usage
    chat_stats = db.query(
        func.count(ChatMessage.id).label('total_messages'),
        func.count(func.distinct(ChatMessage.session_id)).label('sessions')
    ).filter(
        ChatMessage.created_at >= beta_start_date,
        ChatMessage.created_at <= beta_end_date
    ).first()

    chat_users = db.query(func.count(func.distinct(ChatSession.tenant_id))).filter(
        ChatSession.created_at >= beta_start_date,
        ChatSession.created_at <= beta_end_date
    ).scalar() or 0

    print(f"\n💬 CHAT METRICS")
    print(f"  Total Messages: {chat_stats.total_messages or 0}")
    print(f"  Chat Sessions: {chat_stats.sessions or 0}")
    print(f"  Users Using Chat: {chat_users}")
    if chat_stats.sessions and chat_stats.sessions > 0:
        avg_messages = (chat_stats.total_messages or 0) / chat_stats.sessions
        print(f"  Avg Messages/Session: {avg_messages:.1f}")

    # 6. Validated Invoices (Human-in-the-loop)
    validated_invoices = db.query(func.count(InvoiceData.id)).filter(
        InvoiceData.created_at >= beta_start_date,
        InvoiceData.created_at <= beta_end_date,
        InvoiceData.is_validated == True
    ).scalar() or 0

    total_invoices = db.query(func.count(InvoiceData.id)).filter(
        InvoiceData.created_at >= beta_start_date,
        InvoiceData.created_at <= beta_end_date
    ).scalar() or 0

    validation_rate = (validated_invoices / total_invoices * 100) if total_invoices > 0 else 0

    print(f"\n✅ INVOICE VALIDATION")
    print(f"  Total Invoices: {total_invoices}")
    print(f"  Validated: {validated_invoices} ({validation_rate:.1f}%)")

    # 7. Daily Active Users
    dau = db.query(
        func.date(Document.created_at).label('date'),
        func.count(func.distinct(Document.tenant_id)).label('users')
    ).filter(
        Document.created_at >= beta_start_date,
        Document.created_at <= beta_end_date
    ).group_by(func.date(Document.created_at)).order_by('date').all()

    print(f"\n📈 DAILY ACTIVE USERS")
    for date, users in dau:
        print(f"  {date}: {users} users")

    # 8. Power Users (top 10 by document count)
    power_users = db.query(
        Tenant.email,
        Tenant.name,
        func.count(Document.id).label('doc_count')
    ).join(Document, Document.tenant_id == Tenant.id).filter(
        Document.created_at >= beta_start_date,
        Document.created_at <= beta_end_date
    ).group_by(Tenant.id, Tenant.email, Tenant.name).order_by(func.count(Document.id).desc()).limit(10).all()

    print(f"\n⭐ TOP 10 USERS (by documents)")
    for email, name, doc_count in power_users:
        print(f"  {email} ({name}): {doc_count} docs")

    # 9. Feature Adoption
    print(f"\n🔥 FEATURE ADOPTION")
    features = [
        ('Invoice Processing', db.query(func.count(InvoiceData.id)).filter(
            InvoiceData.created_at >= beta_start_date,
            InvoiceData.created_at <= beta_end_date
        ).scalar() or 0),
        ('OCR', db.query(func.count(ProcessingJob.id)).filter(
            ProcessingJob.job_type == 'ocr',
            ProcessingJob.created_at >= beta_start_date,
            ProcessingJob.created_at <= beta_end_date
        ).scalar() or 0),
        ('Summarization', db.query(func.count(DocumentSummary.id)).filter(
            DocumentSummary.created_at >= beta_start_date,
            DocumentSummary.created_at <= beta_end_date
        ).scalar() or 0),
        ('Chat/RAG', chat_users),
    ]

    for feature_name, count in features:
        adoption = (count / active_users * 100) if active_users > 0 else 0
        bar = "█" * int(adoption / 5)
        print(f"  {feature_name:20s}: {count:3d} users ({adoption:5.1f}%) {bar}")

    # 10. Summary Metrics
    print(f"\n📋 SUMMARY")
    print(f"  • Activation Rate: {activation_rate:.1f}% {'✅' if activation_rate >= 80 else '⚠️'}")
    print(f"  • Avg Documents/User: {total_docs/active_users if active_users > 0 else 0:.1f}")
    print(f"  • Most Popular Feature: {max(features, key=lambda x: x[1])[0] if features else 'N/A'}")

    # Success indicators
    print(f"\n🎯 SUCCESS INDICATORS")
    print(f"  {'✅' if activation_rate >= 80 else '❌'} Activation Rate ≥80%: {activation_rate:.1f}%")
    print(f"  {'✅' if active_users >= 8 else '❌'} Active Users ≥8: {active_users}")

    avg_error_rate = sum(failed or 0 for _, _, failed in error_stats) / sum(total for _, total, _ in error_stats) * 100 if error_stats else 0
    print(f"  {'✅' if avg_error_rate < 5 else '❌'} Error Rate <5%: {avg_error_rate:.1f}%")

    db.close()

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Generate beta analytics report')
    parser.add_argument('--start-date', type=str, help='Beta start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Beta end date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, help='Output file path')

    args = parser.parse_args()

    # Default to last 14 days if not specified
    if args.start_date:
        beta_start = datetime.strptime(args.start_date, '%Y-%m-%d')
    else:
        beta_start = datetime.now() - timedelta(days=14)

    if args.end_date:
        beta_end = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        beta_end = datetime.now()

    generate_beta_report(beta_start, beta_end)


if __name__ == "__main__":
    main()

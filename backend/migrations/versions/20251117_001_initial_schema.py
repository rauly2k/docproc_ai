"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-11-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('subdomain', sa.String(100), unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('settings', JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE'))
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('firebase_uid', sa.String(255), unique=True, nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(50), server_default=sa.text("'user'")),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE'))
    )
    op.create_index('idx_tenant_email', 'users', ['tenant_id', 'email'], unique=True)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500)),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size_bytes', sa.BigInteger()),
        sa.Column('document_type', sa.String(50)),
        sa.Column('gcs_path', sa.Text(), nullable=False),
        sa.Column('gcs_processed_path', sa.Text()),
        sa.Column('status', sa.String(50), server_default=sa.text("'uploaded'")),
        sa.Column('processing_started_at', sa.DateTime()),
        sa.Column('processing_completed_at', sa.DateTime()),
        sa.Column('error_message', sa.Text()),
        sa.Column('ocr_completed', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('invoice_parsed', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('summarized', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('rag_indexed', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_tenant_documents', 'documents', ['tenant_id', 'created_at'])
    op.create_index('idx_user_documents', 'documents', ['user_id', 'created_at'])
    op.create_index('idx_document_status', 'documents', ['status'])

    # Create invoice_data table
    op.create_table(
        'invoice_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vendor_name', sa.String(500)),
        sa.Column('vendor_address', sa.Text()),
        sa.Column('vendor_tax_id', sa.String(100)),
        sa.Column('invoice_number', sa.String(100)),
        sa.Column('invoice_date', sa.Date()),
        sa.Column('due_date', sa.Date()),
        sa.Column('subtotal', sa.DECIMAL(15, 2)),
        sa.Column('tax_amount', sa.DECIMAL(15, 2)),
        sa.Column('total_amount', sa.DECIMAL(15, 2)),
        sa.Column('currency', sa.String(3), server_default=sa.text("'EUR'")),
        sa.Column('line_items', JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column('raw_extraction', JSONB),
        sa.Column('is_validated', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('validated_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('validated_at', sa.DateTime()),
        sa.Column('validation_notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_tenant_invoices', 'invoice_data', ['tenant_id', 'invoice_date'])
    op.create_index('idx_invoice_validation', 'invoice_data', ['is_validated'])

    # Create document_summaries table
    op.create_table(
        'document_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(100)),
        sa.Column('word_count', sa.Integer()),
        sa.Column('key_points', JSONB),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )

    # Create ocr_results table
    op.create_table(
        'ocr_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.DECIMAL(5, 4)),
        sa.Column('page_count', sa.Integer()),
        sa.Column('ocr_method', sa.String(50)),
        sa.Column('layout_data', JSONB),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )

    # Create document_chunks table (for RAG)
    op.create_table(
        'document_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer()),
        sa.Column('embedding', Vector(768)),
        sa.Column('metadata', JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_tenant_chunks', 'document_chunks', ['tenant_id'])
    op.create_index('idx_document_chunks', 'document_chunks', ['document_id', 'chunk_index'])
    # Create HNSW index for vector similarity search
    op.execute('CREATE INDEX idx_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops)')

    # Create document_filling_results table
    op.create_table(
        'document_filling_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_document_type', sa.String(50)),
        sa.Column('extracted_fields', JSONB, nullable=False),
        sa.Column('filled_pdf_gcs_path', sa.Text()),
        sa.Column('template_used', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('ip_address', INET),
        sa.Column('user_agent', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_audit_tenant', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('document_filling_results')
    op.drop_table('document_chunks')
    op.drop_table('ocr_results')
    op.drop_table('document_summaries')
    op.drop_table('invoice_data')
    op.drop_table('documents')
    op.drop_table('users')
    op.drop_table('tenants')

    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

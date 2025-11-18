"""Add performance indexes

Revision ID: 006
Revises: 005
Create Date: 2025-11-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for common queries."""

    # Documents table indexes
    op.create_index(
        'idx_documents_tenant_created',
        'documents',
        ['tenant_id', 'created_at'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_documents_tenant_status',
        'documents',
        ['tenant_id', 'status'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_documents_tenant_type',
        'documents',
        ['tenant_id', 'document_type'],
        postgresql_using='btree'
    )

    # Processing jobs indexes (if table exists)
    try:
        op.create_index(
            'idx_jobs_tenant_created',
            'processing_jobs',
            ['tenant_id', 'created_at'],
            postgresql_using='btree'
        )

        op.create_index(
            'idx_jobs_document_status',
            'processing_jobs',
            ['document_id', 'status'],
            postgresql_using='btree'
        )
    except Exception:
        # Table might not exist yet
        pass

    # Document chunks indexes for RAG
    op.create_index(
        'idx_chunks_tenant_document',
        'document_chunks',
        ['tenant_id', 'document_id'],
        postgresql_using='btree'
    )

    # IMPORTANT: pgvector HNSW index for fast similarity search
    # Note: This requires pgvector extension to be installed
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # Chat messages indexes (if table exists)
    try:
        op.create_index(
            'idx_messages_session_created',
            'chat_messages',
            ['session_id', 'created_at'],
            postgresql_using='btree'
        )
    except Exception:
        pass

    # Audit logs indexes (for compliance queries)
    try:
        op.create_index(
            'idx_audit_tenant_timestamp',
            'audit_logs',
            ['tenant_id', 'timestamp'],
            postgresql_using='btree'
        )

        op.create_index(
            'idx_audit_user_action',
            'audit_logs',
            ['user_id', 'action'],
            postgresql_using='btree'
        )
    except Exception:
        pass


def downgrade():
    """Remove performance indexes."""
    op.drop_index('idx_documents_tenant_created', 'documents')
    op.drop_index('idx_documents_tenant_status', 'documents')
    op.drop_index('idx_documents_tenant_type', 'documents')

    try:
        op.drop_index('idx_jobs_tenant_created', 'processing_jobs')
        op.drop_index('idx_jobs_document_status', 'processing_jobs')
    except Exception:
        pass

    op.drop_index('idx_chunks_tenant_document', 'document_chunks')
    op.execute('DROP INDEX IF EXISTS idx_chunks_embedding_hnsw')

    try:
        op.drop_index('idx_messages_session_created', 'chat_messages')
        op.drop_index('idx_audit_tenant_timestamp', 'audit_logs')
        op.drop_index('idx_audit_user_action', 'audit_logs')
    except Exception:
        pass

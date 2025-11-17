"""Add performance indexes (Phase 7.3)

Revision ID: 002
Revises: 001
Create Date: 2025-11-17

"""
from alembic import op

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Create performance indexes."""

    # Documents table indexes for common queries
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

    # Processing jobs indexes
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

    # Document chunks indexes for RAG
    op.create_index(
        'idx_chunks_tenant_document',
        'document_chunks',
        ['tenant_id', 'document_id'],
        postgresql_using='btree'
    )

    # IMPORTANT: pgvector HNSW index for fast similarity search
    # This enables efficient vector similarity queries for RAG
    op.execute("""
        CREATE INDEX idx_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # Chat messages indexes
    op.create_index(
        'idx_messages_session_created',
        'chat_messages',
        ['session_id', 'created_at'],
        postgresql_using='btree'
    )

    # Audit logs indexes (for compliance queries)
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


def downgrade():
    """Drop performance indexes."""
    op.drop_index('idx_documents_tenant_created')
    op.drop_index('idx_documents_tenant_status')
    op.drop_index('idx_documents_tenant_type')
    op.drop_index('idx_jobs_tenant_created')
    op.drop_index('idx_jobs_document_status')
    op.drop_index('idx_chunks_tenant_document')
    op.drop_index('idx_chunks_embedding_hnsw')
    op.drop_index('idx_messages_session_created')
    op.drop_index('idx_audit_tenant_timestamp')
    op.drop_index('idx_audit_user_action')

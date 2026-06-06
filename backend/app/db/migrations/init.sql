-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Companies
CREATE TABLE companies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email       TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sessions (refresh token store)
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    refresh_token   TEXT NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Knowledge documents (metadata)
CREATE TABLE knowledge_documents (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    doc_type    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    s3_key      TEXT,
    chunk_count INT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Document chunks (vector store)
CREATE TABLE document_chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    namespace   TEXT NOT NULL,
    chunk_index INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Strategies
CREATE TABLE strategies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id),
    session_id  UUID NOT NULL,
    status      TEXT NOT NULL DEFAULT 'generating',
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Content assets
CREATE TABLE content_assets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    strategy_id     UUID REFERENCES strategies(id) ON DELETE SET NULL,
    content_type    TEXT NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    validation_status TEXT NOT NULL DEFAULT 'pending',
    brand_alignment_score FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Company memory (persistent context across sessions)
CREATE TABLE company_memory (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(company_id, key)
);

-- HNSW index for fast cosine similarity search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX ON document_chunks (company_id, namespace);

-- Row-Level Security
ALTER TABLE companies           ENABLE ROW LEVEL SECURITY;
ALTER TABLE users               ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies          ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_assets      ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_memory      ENABLE ROW LEVEL SECURITY;

-- RLS policies (reads current_setting set by tenant middleware)
CREATE POLICY tenant_isolation ON companies
    USING (id = current_setting('app.current_company_id', TRUE)::UUID);

CREATE POLICY tenant_isolation ON users
    USING (company_id = current_setting('app.current_company_id', TRUE)::UUID);

CREATE POLICY tenant_isolation ON knowledge_documents
    USING (company_id = current_setting('app.current_company_id', TRUE)::UUID);

CREATE POLICY tenant_isolation ON document_chunks
    USING (company_id = current_setting('app.current_company_id', TRUE)::UUID);

CREATE POLICY tenant_isolation ON strategies
    USING (company_id = current_setting('app.current_company_id', TRUE)::UUID);

CREATE POLICY tenant_isolation ON content_assets
    USING (company_id = current_setting('app.current_company_id', TRUE)::UUID);

CREATE POLICY tenant_isolation ON company_memory
    USING (company_id = current_setting('app.current_company_id', TRUE)::UUID);

-- Superuser bypass for migrations and internal services
CREATE POLICY superuser_bypass ON companies TO postgres USING (TRUE);
CREATE POLICY superuser_bypass ON users TO postgres USING (TRUE);
CREATE POLICY superuser_bypass ON knowledge_documents TO postgres USING (TRUE);
CREATE POLICY superuser_bypass ON document_chunks TO postgres USING (TRUE);
CREATE POLICY superuser_bypass ON strategies TO postgres USING (TRUE);
CREATE POLICY superuser_bypass ON content_assets TO postgres USING (TRUE);
CREATE POLICY superuser_bypass ON company_memory TO postgres USING (TRUE);

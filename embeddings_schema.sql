-- Embeddings table schema for GitLab ChatBot using pgvector
-- Run this SQL in your Supabase SQL editor to add embeddings support

-- Enable the pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table with pgvector
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES page_content(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1536), -- Google Gemini gemini-embedding-001 with 1536 dimensions
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_embeddings_content_id ON embeddings(content_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata ON embeddings USING GIN(metadata);

-- Create vector similarity index for embeddings using pgvector
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Enable Row Level Security (RLS) for better security
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;

-- Create policy for anon access (public access for embeddings)
CREATE POLICY "Allow anon access" ON embeddings
    FOR ALL USING (true);

-- Grant necessary permissions to anon role
GRANT ALL ON embeddings TO anon;

-- Grant sequence permissions to anon role
GRANT USAGE, SELECT ON SEQUENCE embeddings_id_seq TO anon;

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION search_similar_embeddings(
    query_embedding VECTOR(1536),
    match_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id INTEGER,
    content_id INTEGER,
    chunk_index INTEGER,
    total_chunks INTEGER,
    text TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    similarity FLOAT
)
LANGUAGE SQL
AS $$
    SELECT 
        e.id,
        e.content_id,
        e.chunk_index,
        e.total_chunks,
        e.text,
        e.metadata,
        e.created_at,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM embeddings e
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_limit;
$$;

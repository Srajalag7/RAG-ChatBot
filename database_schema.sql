-- Supabase Database Schema for GitLab ChatBot
-- Run this SQL in your Supabase SQL editor to create the required tables

-- Create sites table
CREATE TABLE IF NOT EXISTS sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    base_urls JSONB NOT NULL,
    max_depth INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create scraped_urls table
CREATE TABLE IF NOT EXISTS scraped_urls (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0,
    title TEXT,
    status_code INTEGER,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create page_content table
CREATE TABLE IF NOT EXISTS page_content (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES scraped_urls(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_length INTEGER NOT NULL,
    title TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create scraping_sessions table
CREATE TABLE IF NOT EXISTS scraping_sessions (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    total_urls INTEGER DEFAULT 0,
    total_content_pages INTEGER DEFAULT 0,
    max_depth INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'in_progress'
);

-- Create chats table
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_query TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    conversation_order INTEGER NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb, -- List of source URLs used in the bot response
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_scraped_urls_site_id ON scraped_urls(site_id);
CREATE INDEX IF NOT EXISTS idx_scraped_urls_url ON scraped_urls(url);
CREATE INDEX IF NOT EXISTS idx_page_content_url_id ON page_content(url_id);
CREATE INDEX IF NOT EXISTS idx_scraping_sessions_site_id ON scraping_sessions(site_id);
CREATE INDEX IF NOT EXISTS idx_scraping_sessions_status ON scraping_sessions(status);
CREATE INDEX IF NOT EXISTS idx_conversations_chat_id ON conversations(chat_id);
CREATE INDEX IF NOT EXISTS idx_conversations_order ON conversations(chat_id, conversation_order);
CREATE INDEX IF NOT EXISTS idx_conversations_sources ON conversations USING GIN (sources);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for sites table
CREATE TRIGGER update_sites_updated_at 
    BEFORE UPDATE ON sites 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for chats table
CREATE TRIGGER update_chats_updated_at 
    BEFORE UPDATE ON chats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for better security
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_urls ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policies for anon access (public access for scraping)
CREATE POLICY "Allow anon access" ON sites
    FOR ALL USING (true);

CREATE POLICY "Allow anon access" ON scraped_urls
    FOR ALL USING (true);

CREATE POLICY "Allow anon access" ON page_content
    FOR ALL USING (true);

CREATE POLICY "Allow anon access" ON scraping_sessions
    FOR ALL USING (true);

CREATE POLICY "Allow anon access" ON chats
    FOR ALL USING (true);

CREATE POLICY "Allow anon access" ON conversations
    FOR ALL USING (true);

-- Grant necessary permissions to anon role
GRANT ALL ON sites TO anon;
GRANT ALL ON scraped_urls TO anon;
GRANT ALL ON page_content TO anon;
GRANT ALL ON scraping_sessions TO anon;
GRANT ALL ON chats TO anon;
GRANT ALL ON conversations TO anon;

-- Grant sequence permissions to anon role
GRANT USAGE, SELECT ON SEQUENCE sites_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE scraped_urls_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE page_content_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE scraping_sessions_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE chats_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE conversations_id_seq TO anon;

-- Tharun AI Portfolio — Supabase pgvector setup
-- Run in Supabase Dashboard → SQL Editor → New Query

-- Enable pgvector
create extension if not exists vector;

-- Knowledge base chunks table
create table if not exists knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  embedding vector(768),
  source_file text,
  chunk_index integer,
  metadata jsonb default '{}',
  created_at timestamp with time zone default now()
);

-- Fast similarity search index
create index if not exists knowledge_chunks_embedding_idx
on knowledge_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Similarity search function
create or replace function match_knowledge(
  query_embedding vector(768),
  match_threshold float default 0.75,
  match_count int default 5
)
returns table (
  id uuid,
  content text,
  source_file text,
  similarity float
)
language sql stable
as $$
  select
    id,
    content,
    source_file,
    1 - (embedding <=> query_embedding) as similarity
  from knowledge_chunks
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

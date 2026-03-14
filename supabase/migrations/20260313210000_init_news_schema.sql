create table if not exists public.articles (
  id bigserial primary key,
  slug text not null unique,
  title text not null,
  deck text not null,
  generated_at text not null,
  generated_date text not null,
  status text not null,
  article_path text not null,
  article_url text,
  article_html text not null,
  audio_path text,
  audio_url text,
  payload_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.subscriptions (
  id bigserial primary key,
  email text not null unique,
  active integer not null default 1,
  created_at timestamptz not null default now()
);

create index if not exists idx_articles_generated_at on public.articles (generated_at desc);
create index if not exists idx_subscriptions_active on public.subscriptions (active);

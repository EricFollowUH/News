insert into storage.buckets (id, name, public)
values ('daily-news-assets', 'daily-news-assets', true)
on conflict (id) do nothing;

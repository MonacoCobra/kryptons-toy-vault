-- Cached real cover art URLs (Comic Vine / publisher). Never AI-generated.
create table if not exists comic_covers (
  comic_id      text primary key,
  series        text not null,
  issue         text not null,
  publisher     text not null,
  source        text not null default 'comicvine',
  source_id     text,
  cover_url     text not null,
  thumb_url     text,
  fetched_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists comic_covers_series_issue_idx on comic_covers (series, issue);

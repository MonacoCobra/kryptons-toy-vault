-- Permanent comic archive (static keys + promoted weekly releases)
create table if not exists comic_catalog (
  id            text primary key,
  series        text not null,
  issue         text not null,
  publisher     text not null,
  cover_date    text not null default '',
  street_date   text,
  writers       jsonb not null default '[]',
  artists       jsonb not null default '[]',
  description   text not null default '',
  msrp          double precision not null default 4.99,
  format        text not null default 'single',
  variant       text,
  upc           text,
  demand        double precision not null default 1,
  key_issue     boolean not null default false,
  palette       jsonb not null default '["#1e3a8a","#e30613","#f8fafc"]',
  cover         text,
  source_week   text,
  promoted_at   timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists comic_catalog_publisher_idx on comic_catalog (publisher);
create index if not exists comic_catalog_series_idx on comic_catalog (series);
create index if not exists comic_catalog_street_date_idx on comic_catalog (street_date);

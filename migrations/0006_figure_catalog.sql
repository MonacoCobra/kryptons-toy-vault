-- Live figure SKU overlay (AF rows keyed by SKU; merge on top of baked oneshot without republish)
create table if not exists figure_catalog (
  id            text primary key,
  name          text not null,
  subtitle      text not null default '',
  line          text not null,
  company       text not null,
  kind          text not null default 'figure',
  release_date  text not null,
  msrp          double precision not null default 24.99,
  scale         text not null default '6"',
  demand        double precision not null default 1,
  tags          jsonb not null default '[]',
  sku           text not null,
  exclusive     text,
  image_url     text,
  source        text,
  promoted_at   timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create unique index if not exists figure_catalog_sku_uidx on figure_catalog (lower(sku));
create index if not exists figure_catalog_company_idx on figure_catalog (company);
create index if not exists figure_catalog_line_idx on figure_catalog (line);
create index if not exists figure_catalog_release_date_idx on figure_catalog (release_date);

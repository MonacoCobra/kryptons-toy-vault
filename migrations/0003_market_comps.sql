create table if not exists market_comps (
  item_key   text primary key,
  kind       text not null,
  query      text not null,
  fetched_at timestamptz not null default now(),
  comps      jsonb not null default '[]',
  estimate   double precision not null default 0,
  status     text not null default 'ok',
  error      text
);

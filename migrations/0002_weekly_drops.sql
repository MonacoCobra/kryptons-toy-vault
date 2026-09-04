create table if not exists weekly_drops (
  week       text primary key,
  fetched_at timestamptz not null default now(),
  comics     jsonb not null default '[]',
  figures    jsonb not null default '[]',
  status     text not null default 'ok',
  error      text
);

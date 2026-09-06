-- UPC/ISBN identity on cached covers (LOCG-first). Never invent codes.
alter table comic_covers add column if not exists upc text;
create index if not exists comic_covers_upc_idx on comic_covers (upc) where upc is not null;

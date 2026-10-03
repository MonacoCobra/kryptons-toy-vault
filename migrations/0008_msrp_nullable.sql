-- MSRP / cover price is unknown (null) when no real price is known.
-- Drops the old invented defaults (24.99 figures, 4.99 comics). Existing rows
-- are left as-is: a stored 24.99 / 4.99 can't be told apart from a real price.
alter table figure_catalog alter column msrp drop default;
alter table figure_catalog alter column msrp drop not null;
alter table comic_catalog alter column msrp drop default;
alter table comic_catalog alter column msrp drop not null;

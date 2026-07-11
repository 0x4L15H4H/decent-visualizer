-- Existing shot data is intentionally discarded before the initial release.
drop table if exists shots;

create table shots (
  id text primary key,
  timestamp timestamptz not null,
  duration double precision not null,
  measurements bytea not null,
  workflow jsonb not null default '{}'::jsonb,
  annotations jsonb,
  created_at timestamptz not null default now()
);

grant all on shots to service_role;

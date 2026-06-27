create extension if not exists pg_trgm;

create table canonical_entities (
  id uuid primary key default gen_random_uuid(),
  kind text not null,
  name text not null,
  country_code text,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index canonical_entities_kind_lower_name_idx
on canonical_entities (kind, lower(name));

create index canonical_entities_kind_idx
on canonical_entities (kind);

create index canonical_entities_name_trgm_idx
on canonical_entities using gin (name gin_trgm_ops);

create table entity_aliases (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references canonical_entities(id) on delete cascade,
  alias text not null,
  source text not null,
  created_at timestamptz not null default now()
);

create unique index entity_aliases_entity_lower_alias_idx
on entity_aliases (entity_id, lower(alias));

create index entity_aliases_entity_id_idx
on entity_aliases (entity_id);

create index entity_aliases_lower_alias_idx
on entity_aliases (lower(alias));

create index entity_aliases_alias_trgm_idx
on entity_aliases using gin (alias gin_trgm_ops);

insert into canonical_entities (kind, name)
values
  ('process', 'Washed'),
  ('process', 'Natural'),
  ('process', 'Honey'),
  ('process', 'Anaerobic'),
  ('process', 'Anaerobic Natural'),
  ('process', 'Anaerobic Washed'),
  ('process', 'Carbonic Maceration'),
  ('process', 'Decaf')
on conflict do nothing;

insert into entity_aliases (entity_id, alias, source)
select id, alias, 'system'
from canonical_entities
cross join lateral (
  values
    (case when name = 'Washed' then 'Fully washed' end),
    (case when name = 'Washed' then 'Wet process' end),
    (case when name = 'Natural' then 'Dry process' end),
    (case when name = 'Honey' then 'Pulped natural' end),
    (case when name = 'Carbonic Maceration' then 'CM' end)
) as aliases(alias)
where kind = 'process' and alias is not null
on conflict do nothing;

grant all on canonical_entities to service_role;
grant all on entity_aliases to service_role;

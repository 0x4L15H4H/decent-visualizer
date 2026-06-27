alter table beans
  add column roaster_id uuid references canonical_entities(id),
  add column producer_id uuid references canonical_entities(id),
  add column farm_id uuid references canonical_entities(id),
  add column country_code text,
  add column variety_id uuid references canonical_entities(id),
  add column process_id uuid references canonical_entities(id);

insert into canonical_entities (kind, name)
select distinct 'roaster', btrim(roaster)
from beans
where nullif(btrim(roaster), '') is not null
on conflict do nothing;

insert into canonical_entities (kind, name)
select distinct 'producer', btrim(producer)
from beans
where nullif(btrim(producer), '') is not null
on conflict do nothing;

insert into canonical_entities (kind, name)
select distinct 'farm', btrim(farm)
from beans
where nullif(btrim(farm), '') is not null
on conflict do nothing;

insert into canonical_entities (kind, name)
select distinct 'variety', btrim(variety)
from beans
where nullif(btrim(variety), '') is not null
on conflict do nothing;

insert into canonical_entities (kind, name)
select distinct 'process', btrim(process)
from beans
where nullif(btrim(process), '') is not null
on conflict do nothing;

update beans
set roaster_id = canonical_entities.id
from canonical_entities
where canonical_entities.kind = 'roaster'
  and lower(canonical_entities.name) = lower(btrim(beans.roaster));

update beans
set producer_id = canonical_entities.id
from canonical_entities
where canonical_entities.kind = 'producer'
  and lower(canonical_entities.name) = lower(btrim(beans.producer));

update beans
set farm_id = canonical_entities.id
from canonical_entities
where canonical_entities.kind = 'farm'
  and lower(canonical_entities.name) = lower(btrim(beans.farm));

update beans
set variety_id = canonical_entities.id
from canonical_entities
where canonical_entities.kind = 'variety'
  and lower(canonical_entities.name) = lower(btrim(beans.variety));

update beans
set process_id = canonical_entities.id
from canonical_entities
where canonical_entities.kind = 'process'
  and lower(canonical_entities.name) = lower(btrim(beans.process));

with countries(code, name) as (
  values
    ('BO', 'Bolivia'), ('BR', 'Brazil'), ('BI', 'Burundi'), ('CM', 'Cameroon'),
    ('CN', 'China'), ('CO', 'Colombia'), ('CD', 'Democratic Republic of the Congo'),
    ('CR', 'Costa Rica'), ('CU', 'Cuba'), ('DO', 'Dominican Republic'),
    ('EC', 'Ecuador'), ('SV', 'El Salvador'), ('ET', 'Ethiopia'), ('GT', 'Guatemala'),
    ('HN', 'Honduras'), ('IN', 'India'), ('ID', 'Indonesia'), ('JM', 'Jamaica'),
    ('KE', 'Kenya'), ('LA', 'Laos'), ('MW', 'Malawi'), ('MX', 'Mexico'),
    ('MM', 'Myanmar'), ('NI', 'Nicaragua'), ('PA', 'Panama'),
    ('PG', 'Papua New Guinea'), ('PE', 'Peru'), ('PH', 'Philippines'),
    ('RW', 'Rwanda'), ('TZ', 'Tanzania'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'),
    ('UG', 'Uganda'), ('US', 'United States'), ('VE', 'Venezuela'), ('VN', 'Vietnam'),
    ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe')
)
update beans
set country_code = countries.code
from countries
where lower(replace(countries.name, '-', ' ')) = lower(replace(btrim(beans.country), '-', ' '))
   or countries.code = upper(btrim(beans.country));

update beans
set country_code = case lower(btrim(country))
  when 'columbia' then 'CO'
  when 'drc' then 'CD'
  when 'dr congo' then 'CD'
  when 'congo' then 'CD'
  when 'png' then 'PG'
  when 'usa' then 'US'
  when 'united states of america' then 'US'
end
where country_code is null and country is not null;

do $$
begin
  if exists (
    select 1 from beans
    where nullif(btrim(country), '') is not null and country_code is null
  ) then
    raise exception 'Cannot migrate unrecognized bean country values to country codes';
  end if;
end
$$;

alter table beans
  alter column roaster_id set not null,
  add constraint beans_country_code_format_check
    check (country_code is null or country_code ~ '^[A-Z]{2}$');

create index beans_roaster_id_idx on beans (roaster_id);
create index beans_producer_id_idx on beans (producer_id);
create index beans_farm_id_idx on beans (farm_id);
create index beans_country_code_idx on beans (country_code);
create index beans_variety_id_idx on beans (variety_id);
create index beans_process_id_idx on beans (process_id);

alter table beans
  drop column roaster,
  drop column producer,
  drop column farm,
  drop column country,
  drop column variety,
  drop column process;

create table bean_search_documents (
  bean_id uuid primary key references beans(id) on delete cascade,
  document tsvector not null,
  sortable_name text not null,
  sortable_roaster text not null,
  sortable_country text,
  sortable_variety text,
  sortable_process text,
  sortable_notes text,
  created_at timestamptz not null
);

create index bean_search_documents_document_idx
on bean_search_documents using gin (document);

create index bean_search_documents_created_at_idx
on bean_search_documents (created_at);

create or replace function bean_country_name(country_code text)
returns text
language sql
immutable
as $$
  select case country_code
    when 'BO' then 'Bolivia'
    when 'BR' then 'Brazil'
    when 'BI' then 'Burundi'
    when 'CM' then 'Cameroon'
    when 'CN' then 'China'
    when 'CO' then 'Colombia'
    when 'CD' then 'Democratic Republic of the Congo'
    when 'CR' then 'Costa Rica'
    when 'CU' then 'Cuba'
    when 'DO' then 'Dominican Republic'
    when 'EC' then 'Ecuador'
    when 'SV' then 'El Salvador'
    when 'ET' then 'Ethiopia'
    when 'GT' then 'Guatemala'
    when 'HN' then 'Honduras'
    when 'IN' then 'India'
    when 'ID' then 'Indonesia'
    when 'JM' then 'Jamaica'
    when 'KE' then 'Kenya'
    when 'LA' then 'Laos'
    when 'MW' then 'Malawi'
    when 'MX' then 'Mexico'
    when 'MM' then 'Myanmar'
    when 'NI' then 'Nicaragua'
    when 'PA' then 'Panama'
    when 'PG' then 'Papua New Guinea'
    when 'PE' then 'Peru'
    when 'PH' then 'Philippines'
    when 'RW' then 'Rwanda'
    when 'TZ' then 'Tanzania'
    when 'TH' then 'Thailand'
    when 'TL' then 'Timor-Leste'
    when 'UG' then 'Uganda'
    when 'US' then 'United States'
    when 'VE' then 'Venezuela'
    when 'VN' then 'Vietnam'
    when 'YE' then 'Yemen'
    when 'ZM' then 'Zambia'
    when 'ZW' then 'Zimbabwe'
  end
$$;

create or replace function refresh_bean_search_document(target_bean_id uuid)
returns void
language sql
security definer
set search_path = public
as $$
  insert into bean_search_documents (
    bean_id,
    document,
    sortable_name,
    sortable_roaster,
    sortable_country,
    sortable_variety,
    sortable_process,
    sortable_notes,
    created_at
  )
  select
    beans.id,
    setweight(to_tsvector('simple', coalesce(beans.name, '')), 'A') ||
      setweight(to_tsvector('simple', coalesce(roaster.name, '')), 'A') ||
      setweight(to_tsvector('simple', concat_ws(
        ' ',
        producer.name,
        farm.name,
        bean_country_name(beans.country_code),
        variety.name,
        process.name
      )), 'B') ||
      setweight(to_tsvector('simple', concat_ws(
        ' ',
        beans.id::text,
        roaster.id::text,
        producer.id::text,
        farm.id::text,
        beans.country_code,
        variety.id::text,
        process.id::text,
        beans.roast_level,
        beans.roast_date::text,
        beans.notes,
        beans.created_at::text
      )), 'C'),
    beans.name,
    roaster.name,
    bean_country_name(beans.country_code),
    variety.name,
    process.name,
    beans.notes,
    beans.created_at
  from beans
  join canonical_entities as roaster on roaster.id = beans.roaster_id
  left join canonical_entities as producer on producer.id = beans.producer_id
  left join canonical_entities as farm on farm.id = beans.farm_id
  left join canonical_entities as variety on variety.id = beans.variety_id
  left join canonical_entities as process on process.id = beans.process_id
  where beans.id = target_bean_id
  on conflict (bean_id) do update set
    document = excluded.document,
    sortable_name = excluded.sortable_name,
    sortable_roaster = excluded.sortable_roaster,
    sortable_country = excluded.sortable_country,
    sortable_variety = excluded.sortable_variety,
    sortable_process = excluded.sortable_process,
    sortable_notes = excluded.sortable_notes,
    created_at = excluded.created_at;
$$;

create or replace function refresh_bean_search_document_trigger()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  perform refresh_bean_search_document(new.id);
  return new;
end;
$$;

create trigger refresh_bean_search_document_after_bean_change
after insert or update on beans
for each row
execute function refresh_bean_search_document_trigger();

create or replace function refresh_bean_search_documents_for_entity_trigger()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  affected_bean_id uuid;
begin
  for affected_bean_id in
    select id
    from beans
    where roaster_id = new.id
       or producer_id = new.id
       or farm_id = new.id
       or variety_id = new.id
       or process_id = new.id
  loop
    perform refresh_bean_search_document(affected_bean_id);
  end loop;

  return new;
end;
$$;

create trigger refresh_bean_search_documents_after_entity_change
after update of name on canonical_entities
for each row
execute function refresh_bean_search_documents_for_entity_trigger();

create or replace function search_bean_ids(
  p_query text default null,
  p_offset integer default 0,
  p_limit integer default 20,
  p_sort_by text default 'created_at',
  p_desc boolean default true
)
returns table(id uuid, total_count bigint)
language sql
stable
security definer
set search_path = public
as $$
  with query as (
    select case
      when nullif(btrim(p_query), '') is null then null
      else websearch_to_tsquery('simple', p_query)
    end as value
  ),
  matches as (
    select
      docs.bean_id as id,
      docs.sortable_name,
      docs.sortable_roaster,
      docs.sortable_country,
      docs.sortable_variety,
      docs.sortable_process,
      docs.sortable_notes,
      docs.created_at,
      case
        when query.value is null then 0
        else ts_rank_cd(docs.document, query.value)
      end as rank
    from bean_search_documents as docs
    cross join query
    where query.value is null or docs.document @@ query.value
  ),
  totals as (
    select count(*) as total_count
    from matches
  ),
  page as (
    select
      matches.id,
      matches.sortable_name,
      matches.sortable_roaster,
      matches.sortable_country,
      matches.sortable_variety,
      matches.sortable_process,
      matches.sortable_notes,
      matches.created_at,
      matches.rank
    from matches
    order by
      case when p_sort_by = 'relevance' and p_desc then matches.rank end desc nulls last,
      case when p_sort_by = 'relevance' and not p_desc then matches.rank end asc nulls last,
      case when p_sort_by = 'name' and p_desc then lower(matches.sortable_name) end desc nulls last,
      case when p_sort_by = 'name' and not p_desc then lower(matches.sortable_name) end asc nulls last,
      case when p_sort_by = 'roaster' and p_desc then lower(matches.sortable_roaster) end desc nulls last,
      case when p_sort_by = 'roaster' and not p_desc then lower(matches.sortable_roaster) end asc nulls last,
      case when p_sort_by = 'country' and p_desc then lower(matches.sortable_country) end desc nulls last,
      case when p_sort_by = 'country' and not p_desc then lower(matches.sortable_country) end asc nulls last,
      case when p_sort_by = 'variety' and p_desc then lower(matches.sortable_variety) end desc nulls last,
      case when p_sort_by = 'variety' and not p_desc then lower(matches.sortable_variety) end asc nulls last,
      case when p_sort_by = 'process' and p_desc then lower(matches.sortable_process) end desc nulls last,
      case when p_sort_by = 'process' and not p_desc then lower(matches.sortable_process) end asc nulls last,
      case when p_sort_by = 'notes' and p_desc then lower(matches.sortable_notes) end desc nulls last,
      case when p_sort_by = 'notes' and not p_desc then lower(matches.sortable_notes) end asc nulls last,
      case when (p_sort_by not in ('relevance', 'name', 'roaster', 'country', 'variety', 'process', 'notes') or p_sort_by = 'created_at') and p_desc then matches.created_at end desc nulls last,
      case when (p_sort_by not in ('relevance', 'name', 'roaster', 'country', 'variety', 'process', 'notes') or p_sort_by = 'created_at') and not p_desc then matches.created_at end asc nulls last,
      matches.id
    offset greatest(p_offset, 0)
    limit least(greatest(p_limit, 1), 100)
  )
  select result.id, result.total_count
  from (
    select
      page.id,
      totals.total_count,
      page.sortable_name,
      page.sortable_roaster,
      page.sortable_country,
      page.sortable_variety,
      page.sortable_process,
      page.sortable_notes,
      page.created_at,
      page.rank
    from page
    cross join totals
    union all
    select
      null::uuid,
      totals.total_count,
      null::text,
      null::text,
      null::text,
      null::text,
      null::text,
      null::text,
      null::timestamptz,
      null::real
    from totals
    where totals.total_count > 0
      and not exists (select 1 from page)
  ) as result
  order by
    case when p_sort_by = 'relevance' and p_desc then result.rank end desc nulls last,
    case when p_sort_by = 'relevance' and not p_desc then result.rank end asc nulls last,
    case when p_sort_by = 'name' and p_desc then lower(result.sortable_name) end desc nulls last,
    case when p_sort_by = 'name' and not p_desc then lower(result.sortable_name) end asc nulls last,
    case when p_sort_by = 'roaster' and p_desc then lower(result.sortable_roaster) end desc nulls last,
    case when p_sort_by = 'roaster' and not p_desc then lower(result.sortable_roaster) end asc nulls last,
    case when p_sort_by = 'country' and p_desc then lower(result.sortable_country) end desc nulls last,
    case when p_sort_by = 'country' and not p_desc then lower(result.sortable_country) end asc nulls last,
    case when p_sort_by = 'variety' and p_desc then lower(result.sortable_variety) end desc nulls last,
    case when p_sort_by = 'variety' and not p_desc then lower(result.sortable_variety) end asc nulls last,
    case when p_sort_by = 'process' and p_desc then lower(result.sortable_process) end desc nulls last,
    case when p_sort_by = 'process' and not p_desc then lower(result.sortable_process) end asc nulls last,
    case when p_sort_by = 'notes' and p_desc then lower(result.sortable_notes) end desc nulls last,
    case when p_sort_by = 'notes' and not p_desc then lower(result.sortable_notes) end asc nulls last,
    case when (p_sort_by not in ('relevance', 'name', 'roaster', 'country', 'variety', 'process', 'notes') or p_sort_by = 'created_at') and p_desc then result.created_at end desc nulls last,
    case when (p_sort_by not in ('relevance', 'name', 'roaster', 'country', 'variety', 'process', 'notes') or p_sort_by = 'created_at') and not p_desc then result.created_at end asc nulls last,
    result.id;
$$;

insert into bean_search_documents (
  bean_id,
  document,
  sortable_name,
  sortable_roaster,
  sortable_country,
  sortable_variety,
  sortable_process,
  sortable_notes,
  created_at
)
select
  beans.id,
  setweight(to_tsvector('simple', coalesce(beans.name, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(roaster.name, '')), 'A') ||
    setweight(to_tsvector('simple', concat_ws(
      ' ',
      producer.name,
      farm.name,
      bean_country_name(beans.country_code),
      variety.name,
      process.name
    )), 'B') ||
    setweight(to_tsvector('simple', concat_ws(
      ' ',
      beans.id::text,
      roaster.id::text,
      producer.id::text,
      farm.id::text,
      beans.country_code,
      variety.id::text,
      process.id::text,
      beans.roast_level,
      beans.roast_date::text,
      beans.notes,
      beans.created_at::text
    )), 'C'),
  beans.name,
  roaster.name,
  bean_country_name(beans.country_code),
  variety.name,
  process.name,
  beans.notes,
  beans.created_at
from beans
join canonical_entities as roaster on roaster.id = beans.roaster_id
left join canonical_entities as producer on producer.id = beans.producer_id
left join canonical_entities as farm on farm.id = beans.farm_id
left join canonical_entities as variety on variety.id = beans.variety_id
left join canonical_entities as process on process.id = beans.process_id;

grant select on bean_search_documents to service_role;
grant execute on function search_bean_ids(text, integer, integer, text, boolean) to service_role;

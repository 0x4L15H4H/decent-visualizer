create table if not exists beans (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    roaster text not null,
    farmer text,
    origin text,
    variety text,
    process text,
    roast_level text,
    roast_date timestamptz,
    notes text,
    created_at timestamptz not null default now()
);

create table if not exists shots (
    id text primary key,
    timestamp timestamptz not null,
    duration double precision not null,
    measurements jsonb not null default '[]'::jsonb,
    workflow jsonb not null default '{}'::jsonb,
    annotations jsonb,
    created_at timestamptz not null default now()
);

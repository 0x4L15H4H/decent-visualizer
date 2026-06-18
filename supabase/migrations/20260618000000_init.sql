create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  display_name text,
  created_at timestamptz not null default now()
);

create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '30 days'
);

create index sessions_user_id_idx on sessions(user_id);
create index sessions_expires_at_idx on sessions(expires_at);

create table settings (
  key text primary key,
  value jsonb not null
);

insert into settings (key, value) values ('signups_enabled', 'true');

create table beans (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  roaster text not null,
  producer text,
  farm text,
  country text,
  variety text,
  process text,
  roast_level text,
  roast_date timestamptz,
  notes text,
  created_at timestamptz not null default now()
);

grant all on users to service_role;
grant all on sessions to service_role;
grant all on settings to service_role;
grant all on beans to service_role;

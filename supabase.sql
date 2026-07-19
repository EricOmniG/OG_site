-- ============================================================
-- PROJECT SPROUT — signup backend (copy-paste into Supabase)
-- Supabase Dashboard -> SQL Editor -> New query -> paste -> Run
-- ============================================================

-- 1. The signups table
create table if not exists public.signups (
  id         uuid primary key default gen_random_uuid(),
  email      text not null unique,
  created_at timestamptz not null default now(),
  source     text default 'landing'
);

-- 2. Row-Level Security: the whole safety model.
--    * anon (the public key in index.html) may INSERT only.
--    * nobody anonymous can SELECT/UPDATE/DELETE — the list is private.
--    * authenticated users (you, logged into admin.html) may SELECT.
alter table public.signups enable row level security;

create policy "public can sign up"
  on public.signups for insert
  to anon
  with check (true);

create policy "admins can read the list"
  on public.signups for select
  to authenticated
  using (true);

-- 3. Weekly stats view (feeds admin.html and weekly_report.py)
create or replace view public.weekly_signups as
  select date_trunc('week', created_at)::date as week_start,
         count(*)::int as signups
  from public.signups
  group by 1
  order by 1 desc;

-- Views don't inherit RLS by default; lock it to authenticated too:
revoke all on public.weekly_signups from anon;
grant select on public.weekly_signups to authenticated;

-- 4. OPTIONAL basic rate-limit hardening: cap dupes & garbage
--    (Supabase also rate-limits at the API layer; unique(email) above
--     already blocks repeat inserts of the same address.)

-- ============================================================
-- AFTER RUNNING THIS, create your admin login:
-- Dashboard -> Authentication -> Users -> Add user
--   email:    you@yourdomain
--   password: (long + random)
-- That login is what admin.html uses. No service keys anywhere.
-- ============================================================

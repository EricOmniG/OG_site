# Security notes — Sprout site kit

## Key model (the part that matters)
| Key | Lives where | Can do |
|---|---|---|
| anon public key | index.html, admin.html (public) | INSERT a signup. Nothing else. |
| admin login (email+password) | your head | upgrades a session to `authenticated` -> can SELECT the list |
| service_role key | env var on YOUR machine only | bypasses RLS entirely — never in any web file, never committed |

Row-Level Security (in supabase.sql) is what enforces this: `anon` has an
INSERT-only policy; SELECT requires `authenticated`. Even with the page's
source fully public on GitHub, the waitlist itself is unreadable.

## Hardening applied in these files
- admin.html: `noindex,nofollow` meta + should be in robots.txt Disallow
- All rendered emails/sources HTML-escaped in admin (stored-XSS defense —
  someone could sign up with a script tag as their "email" otherwise)
- Duplicate emails rejected by a UNIQUE constraint (and handled gracefully
  in the form: "already on the list")
- No secrets in any shipped file: the two pasted values are public-safe by design

## Do / Don't
- DO rotate the admin password if you ever share a screen with admin.html open
- DO keep the service key only in your shell env / a local .env in .gitignore
- DON'T create a SELECT policy for `anon` — that would publish your list
- DON'T put the service key in weekly_report.py itself; keep it in the env
- If you ever suspect the admin password leaked: Supabase -> Auth -> reset it;
  nothing else needs rotating (the anon key was never a secret)

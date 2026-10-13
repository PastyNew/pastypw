# Security policy

## What this program does

PastyNew Password Generator is completely offline:

- passwords are created with `secrets` (the operating system CSPRNG);
- the application never opens a network connection;
- there is no telemetry, no update check and no analytics;
- the only files it writes are
  - `~/.config/pastypw/settings.json` — interface settings,
  - `~/.local/share/pastypw/history.json` — the local password history.

## History is not encrypted

The history file contains generated passwords **in plain text** so that it
stays readable for backup and export. If that is not acceptable for your
threat model:

- clear the history with the bin icon in the history card;
- use the eye button only when nobody is watching your screen;
- better: do not store history at all - export the batch to a file on an
  encrypted partition and wipe the history afterwards;
- on a shared machine log out or clear the history after use.

## Reporting a vulnerability

Please do **not** open a public issue for a security problem. Write to
`pastypew@gmail.com` with a description and, if possible, a reproduction
step. You can expect an answer within a few days.

## Scope

This is a desktop utility. Issues like "a weak password was generated because
the user unchecked all character classes" are by design, not vulnerabilities.
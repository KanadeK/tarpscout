# Security policy

## Supported version

Security fixes are provided for the latest tagged release. v0.1.0 is a local
offline application: it opens a user-selected JSON file and writes artifacts to
a user-selected directory; it does not authenticate, listen on a port, or make
network requests.

## Reporting a vulnerability

Use GitHub Security Advisories' **Report a vulnerability** entry when it is
available. If the entry is absent, open a public issue containing no sensitive
details and ask the maintainer to establish a private channel. Include the
affected version, platform, minimal reproduction, impact, and whether crafted
JSON or an output path is required only in that private channel.

Expected non-security behavior:

- invalid JSON/schema returns exit `2` with a field path;
- valid no-solution input returns exit `1` and a diagnostic report;
- HTML and SVG text derived from input is escaped;
- identifiers containing control characters are rejected and formula-shaped
  CSV text is emitted as text rather than an executable spreadsheet formula;
- output names derive only from the validated ASCII scenario name.

TarpScout's explicit safety disclaimer is not a vulnerability workaround. A
wrong constraint result, path escape, script injection, or unexpected network
access should be reported.

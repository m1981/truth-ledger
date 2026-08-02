"""truthlib -- the truth CLI as a package of concern modules (ADR-044).

Deliberately empty: scripts/truth (the thin entry) re-exports every
module's namespace and stays the one loading surface for consumers and
for SourceFileLoader-based suites.  Importing truthlib itself pulls in
nothing, so module import order stays explicit at the entry.
"""

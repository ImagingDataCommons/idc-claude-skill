# Syncing this skill into a registry

Third-party skill registries vendor this skill into their own repositories. Every rule below
exists because a registry had to patch the vendored copy at least once; upstream now holds it
in CI so a sync stays a file copy instead of a copy plus a patch that has to be re-applied
every release.

If your registry needs an edit that is not covered here, please
[open an issue](https://github.com/ImagingDataCommons/imaging-data-commons-skill/issues/new/choose)
rather than carrying the patch — the fix belongs upstream.

## Take the release attachment

Every release carries `imaging-data-commons-<version>.zip`, and that attachment *is* the
bundle — nothing in it is optional:

```bash
gh release download vX.Y.Z -R ImagingDataCommons/imaging-data-commons-skill -p '*.zip'
```

```
SKILL.md          the always-loaded file
references/       topical guides, loaded on demand
scripts/          check_version.py, the startup version check
```

Vendor `scripts/` along with the other two. It is the skill's first step — `python
scripts/check_version.py` reports whether `idc-index` is installed and current enough, prints
the install command for the interpreter that ran it, and exits non-zero so the agent stops
rather than querying a stale index. Registries that require a test suite for any skill
shipping `scripts/` should see *Tests* below.

Copying from a checkout works too, but then getting the path list right is on you, and `main`
can sit between releases. `README.md`, `USAGE.md`, `CHANGELOG.md`, `tests/`, and `.github/`
are repository infrastructure and are deliberately absent from the zip: `USAGE.md` documents
loading the skill from this repository, which is not how a registry's users will get it.

## What upstream guarantees

| Guarantee | Held by |
|---|---|
| `SKILL.md` is at most 500 lines | `tests/test_structure.py::TestLineBudget` |
| `metadata` frontmatter entries are indented exactly two spaces | `TestFrontmatter::test_metadata_scalars_are_indented_two_spaces` |
| `metadata.version` is `MAJOR.MINOR.PATCH` | `TestFrontmatter::test_version_is_semver` |
| Frontmatter uses only Agent Skills top-level keys (`name`, `description`, `license`, `metadata`) | Agent Skills spec |
| No hardcoded `pip` / `uv` / `conda` / `poetry` install command in `SKILL.md` or `references/` | `TestInstallCommands` |
| Every `references/` and `scripts/` path the docs name resolves, and no guide is unreachable | `TestReferenceLinks` |
| The bundled script never shells out to an installer, never calls `eval` / `exec` / `os.system`, and never overrides PEP 668 | `tests/test_check_version.py::TestNeverInstalls` |
| The bundled script imports without network access, `idc-index`, or any third-party package | `tests/test_check_version.py` |
| No tests, fixtures, or bytecode inside the three vendored paths | the release zip is built from those paths alone |

Two-space indentation and the absence of installer commands are the two that broke a
registry's conformance gate in practice, so they are pinned rather than left to style.

For a security triage: `check_version.py` is standard library only, takes no arguments, and
its only network access is two public JSON endpoints — the PyPI project page for `idc-index`
and this repository's GitHub releases API — read with `urllib` to print update notices, both
best-effort and skipped when unreachable. It reads no environment variables and no
credentials.

## Version numbering

Registries that maintain their own skill version should set `metadata.version` to theirs and
record ours alongside it:

```yaml
metadata:
  version: "1.5"                 # the registry's numbering
  source-skill-version: 1.8.1    # the upstream release this copy came from
```

`scripts/check_version.py` pins `SKILL_VERSION` to the upstream release and compares it
against this repository's GitHub releases to notify users when a newer skill is available. A
test asserting that the script and the frontmatter agree must therefore read
`source-skill-version`, not `version`, in a renumbered copy.

## Tests

Registries that require a test suite for a skill shipping `scripts/` should copy
`tests/test_check_version.py` out of this repository. It is written to be vendored: offline,
standard library plus pytest, no `idc-index` install, and it runs with nothing else present.
Only the two path constants at the top change — plus the frontmatter assertion above, if you
renumber.

Do not vendor `tests/test_snippets.py`, `test_rest_api.py`, `test_mcp_server.py`, or
`test_bq_snippets.py`. They need `idc-index`, live IDC endpoints, and (for BigQuery) GCP
credentials, and they already run here on every pull request.

## One sync, step by step

1. Download the release attachment and unpack it.
2. **Replace the whole skill directory**, rather than merging file by file. Guides do get
   removed: content moves between them when `SKILL.md` is reduced, and a stale guide left
   behind means the same material in two places.
3. Re-copy `tests/test_check_version.py` and adjust its path constants.
4. Renumber the frontmatter if your registry does that, keeping `source-skill-version`.
5. Run your validators, then check `CHANGELOG.md` for the `idc-index` pin and IDC data
   version this release was tested against — both also appear in the frontmatter.
6. **Say what was removed** in the sync pull request. A deletion is the one part of a
   wholesale copy that is not self-explanatory.

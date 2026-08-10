"""
Structure contract for the skill bundle.

SKILL.md is loaded into context on every invocation, so its size is a budget, not a
preference. Detail belongs in references/, which the agent loads on demand.

These tests need no network and no idc-index install — they are pure file checks, so they
run everywhere the rest of the suite might skip.
"""

import os
import re

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SKILL_MD = os.path.join(_ROOT, "SKILL.md")
_REFERENCES = os.path.join(_ROOT, "references")

# Downstream skill registries impose a hard cap on SKILL.md. Hold the budget here so a
# vendored copy never has to be re-split by hand after a sync.
LINE_BUDGET = 500


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class TestLineBudget:
    def test_skill_md_within_budget(self):
        lines = _read(_SKILL_MD).splitlines()
        assert len(lines) <= LINE_BUDGET, (
            f"SKILL.md is {len(lines)} lines, over the {LINE_BUDGET}-line budget. "
            "Move detail into an existing references/ guide and leave a pointer — "
            "do not create a catch-all overflow file."
        )


class TestReferenceLinks:
    """Every guide SKILL.md points at must exist, and every guide must be reachable."""

    def _named_guides(self):
        skill = _read(_SKILL_MD)
        return set(re.findall(r"`?(?:references/)?([a-z0-9_]+_guide\.md|sql_patterns\.md|use_cases\.md|licensing_and_citation\.md)`?", skill))

    def test_named_guides_exist(self):
        missing = [g for g in self._named_guides() if not os.path.exists(os.path.join(_REFERENCES, g))]
        assert not missing, f"SKILL.md points at guides that do not exist: {sorted(missing)}"

    def test_no_orphan_guides(self):
        on_disk = {f for f in os.listdir(_REFERENCES) if f.endswith(".md")}
        orphans = on_disk - self._named_guides()
        assert not orphans, (
            f"references/ contains guides SKILL.md never names: {sorted(orphans)}. "
            "An unreferenced guide is never loaded."
        )


class TestAlwaysLoadedGuidance:
    """
    Content that must stay in SKILL.md rather than move to a reference file.

    The common thread: each one corrects something a model will otherwise get confidently
    wrong from its own priors. A reference file only helps when the agent already knows it
    needs to look — these are the cases where it does not.
    """

    def test_download_argument_order_is_inline(self):
        skill = _read(_SKILL_MD)
        assert "opposite order" in skill, (
            "SKILL.md must state that download_from_selection and download_dicom_series take "
            "their first two arguments in opposite order"
        )
        # Both signatures spelled out, so the agent can check rather than recall.
        assert re.search(r"`download_from_selection`\s*\|\s*`downloadDir`", skill)
        assert re.search(r"`download_dicom_series`\s*\|\s*`seriesInstanceUID`", skill)

    def test_download_from_selection_dataframe_warning_is_inline(self):
        skill = _read(_SKILL_MD)
        assert "NOT a DataFrame" in skill, (
            "SKILL.md must warn that download_from_selection takes filter kwargs, not a DataFrame"
        )

    def test_explore_values_before_filtering_is_inline(self):
        skill = _read(_SKILL_MD)
        assert "most common cause of an" in skill and "empty result set" in skill, (
            "SKILL.md must tell the agent to enumerate filter values before filtering on them"
        )

    def test_license_and_citation_obligation_is_inline(self):
        skill = _read(_SKILL_MD)
        assert "citations_from_selection" in skill
        assert "license_short_name" in skill
        assert "CC BY-NC" in skill, (
            "SKILL.md must name the non-commercial license class inline — a user asking about "
            "commercial use gets a wrong answer if this only lives in a reference file"
        )

    def test_access_path_routing_gate_is_inline(self):
        # Without this, the agent falls back to its prior that idc-index is the one entry point
        # and pays a ~77 MB install to answer a metadata question. The gate only works if it is
        # read before the first query, so it cannot move to a reference file.
        skill = _read(_SKILL_MD)
        assert "Choose the access path first" in skill, (
            "SKILL.md must open with the access-path routing gate"
        )
        assert "do not install anything" in skill, (
            "SKILL.md must tell the agent not to install idc-index for read-only metadata"
        )

    def test_prior_versions_index_warning_is_inline(self):
        skill = _read(_SKILL_MD)
        assert "prior_versions_index" in skill
        assert "series_init_idc_version" in skill, (
            "SKILL.md must route 'what's new in vX' to series_init_idc_version rather than "
            "prior_versions_index"
        )


class TestFrontmatter:
    def test_version_is_semver(self):
        skill = _read(_SKILL_MD)
        match = re.search(r"^\s+version:\s*(\S+)\s*$", skill, re.MULTILINE)
        assert match, "SKILL.md frontmatter has no version"
        assert re.fullmatch(r"\d+\.\d+\.\d+", match.group(1)), (
            f"version {match.group(1)!r} is not MAJOR.MINOR.PATCH"
        )

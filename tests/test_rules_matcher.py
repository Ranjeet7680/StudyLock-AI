"""
StudyLock AI - Unit Tests: Block Rules Precedence & Canonical Matching
Ref: StudyLock AI Architecture Specification Section 6
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from packages.schemas.enums import TargetType, RuleAction
from packages.schemas.rules import RuleMatcher, BlockRuleDefinition


def test_domain_normalization():
    assert RuleMatcher.normalize_domain("https://www.youtube.com/watch?v=123") == "youtube.com"
    assert RuleMatcher.normalize_domain("http://youtu.be/xyz") == "youtu.be"
    assert RuleMatcher.normalize_domain("www.instagram.com") == "instagram.com"
    assert RuleMatcher.normalize_domain("m.instagram.com") == "m.instagram.com"


def test_youtube_canonical_matching():
    rule = BlockRuleDefinition(
        id="r-yt",
        user_id="u1",
        target_type=TargetType.DOMAIN,
        target_value="youtube.com",
        action=RuleAction.BLOCK,
        enabled=True
    )
    # Direct match
    assert RuleMatcher.matches_target(rule, "https://youtube.com") is True
    # Subdomain match
    assert RuleMatcher.matches_target(rule, "https://m.youtube.com/watch?v=1") is True
    # youtu.be shortlink canonicalization (Spec Section 6.4)
    assert RuleMatcher.matches_target(rule, "https://youtu.be/abc") is True
    # Unrelated site
    assert RuleMatcher.matches_target(rule, "https://wikipedia.org") is False


def test_rule_precedence_allow_overrides_block():
    # Category or broad block for youtube.com
    block_rule = BlockRuleDefinition(
        id="r-block",
        user_id="u1",
        target_type=TargetType.DOMAIN,
        target_value="youtube.com",
        action=RuleAction.BLOCK,
        enabled=True
    )
    # Specific allow rule for educational channel URL pattern
    allow_rule = BlockRuleDefinition(
        id="r-allow",
        user_id="u1",
        target_type=TargetType.URL_PATTERN,
        target_value="*youtube.com/c/3blue1brown*",
        action=RuleAction.ALLOW,
        enabled=True
    )

    # Candidate 1: 3Blue1Brown educational video -> allowed by higher specificity URL_PATTERN
    cand1 = "https://www.youtube.com/c/3blue1brown/videos"
    res1 = RuleMatcher.evaluate([block_rule, allow_rule], cand1)
    assert res1["action"] == RuleAction.ALLOW
    assert res1["matched_rule_id"] == "r-allow"

    # Candidate 2: Random entertainment video -> blocked by domain rule
    cand2 = "https://www.youtube.com/watch?v=random_entertainment"
    res2 = RuleMatcher.evaluate([block_rule, allow_rule], cand2)
    assert res2["action"] == RuleAction.BLOCK
    assert res2["matched_rule_id"] == "r-block"


def test_app_package_matching():
    rule = BlockRuleDefinition(
        id="r-app",
        user_id="u1",
        target_type=TargetType.APP_PACKAGE,
        target_value="discord.exe",
        action=RuleAction.BLOCK,
        enabled=True
    )
    assert RuleMatcher.matches_target(rule, "discord.exe") is True
    assert RuleMatcher.matches_target(rule, "Discord.EXE") is True
    assert RuleMatcher.matches_target(rule, "notepad.exe") is False

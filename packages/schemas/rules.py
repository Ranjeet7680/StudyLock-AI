"""
StudyLock AI - Block Rules, Precedence Engine & Domain Matcher
Ref: StudyLock AI Architecture Specification Section 6
"""
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from .enums import TargetType, RuleAction, RuleScope


class BlockRuleDefinition(BaseModel):
    id: str
    user_id: str
    device_id: Optional[str] = None
    target_type: TargetType
    target_value: str
    action: RuleAction = RuleAction.BLOCK
    scope: RuleScope = RuleScope.DEVICE
    enabled: bool = True
    revision: int = 1


class RuleMatcher:
    """
    Evaluates block/allow rules with deterministic precedence.
    Precedence order (highest to lowest):
    1. ALLOW rules with exact URL_PATTERN match
    2. BLOCK rules with exact URL_PATTERN match
    3. ALLOW rules with exact DOMAIN / APP_PACKAGE match
    4. BLOCK rules with exact DOMAIN / APP_PACKAGE match
    5. CATEGORY rules
    """

    @staticmethod
    def normalize_domain(domain_or_url: str) -> str:
        """
        Normalizes input to canonical lowercased domain.
        Strips scheme, port, leading 'www.', and trailing path.
        Handles youtube.com, youtu.be, instagram.com canonicalization.
        """
        raw = domain_or_url.strip().lower()
        if not raw.startswith(("http://", "https://")):
            # Prepend https for urlparse to parse correctly if given plain hostname
            parsed = urlparse("https://" + raw)
        else:
            parsed = urlparse(raw)

        hostname = parsed.hostname or raw
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname

    @classmethod
    def matches_target(cls, rule: BlockRuleDefinition, candidate: str) -> bool:
        """
        Checks if candidate URL, domain or package matches the rule.
        """
        if not rule.enabled:
            return False

        if rule.target_type == TargetType.APP_PACKAGE:
            # Package names e.g. com.google.android.youtube or process name e.g. discord.exe
            return rule.target_value.strip().lower() == candidate.strip().lower()

        elif rule.target_type == TargetType.DOMAIN:
            rule_domain = cls.normalize_domain(rule.target_value)
            candidate_domain = cls.normalize_domain(candidate)

            # Direct match or subdomain match (e.g., m.youtube.com matches youtube.com)
            if candidate_domain == rule_domain:
                return True
            if candidate_domain.endswith("." + rule_domain):
                return True

            # Special YouTube short-link canonicalization
            if rule_domain == "youtube.com" and candidate_domain in {"youtu.be", "m.youtube.com"}:
                return True
            if rule_domain == "instagram.com" and candidate_domain in {"m.instagram.com", "ig.me"}:
                return True

            return False

        elif rule.target_type == TargetType.URL_PATTERN:
            # Regex or wildcard matching
            pattern = rule.target_value
            try:
                # Convert glob wildcard to regex if not already regex
                if "*" in pattern and not pattern.startswith("^"):
                    regex_str = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
                else:
                    regex_str = pattern
                return bool(re.search(regex_str, candidate, re.IGNORECASE))
            except re.error:
                return False

        elif rule.target_type == TargetType.SUPPORTED_CATEGORY:
            # Category match (e.g. social_media, gaming, streaming)
            return False

        return False

    @classmethod
    def evaluate(cls, rules: List[BlockRuleDefinition], candidate: str) -> Dict[str, Any]:
        """
        Evaluates active rules against a candidate (app package or URL/domain).
        Returns decision: action (BLOCK, ALLOW, or NONE) and matched rule ID.
        """
        matched_allow = []
        matched_block = []

        for rule in rules:
            if not rule.enabled:
                continue
            if cls.matches_target(rule, candidate):
                if rule.action == RuleAction.ALLOW:
                    matched_allow.append(rule)
                elif rule.action == RuleAction.BLOCK:
                    matched_block.append(rule)

        # Precedence: URL_PATTERN > DOMAIN / APP_PACKAGE > CATEGORY
        # And ALLOW overrides BLOCK at same specificity
        type_precedence = {
            TargetType.URL_PATTERN: 3,
            TargetType.DOMAIN: 2,
            TargetType.APP_PACKAGE: 2,
            TargetType.SUPPORTED_CATEGORY: 1
        }

        if matched_allow or matched_block:
            highest_allow = max(matched_allow, key=lambda r: type_precedence.get(r.target_type, 0), default=None)
            highest_block = max(matched_block, key=lambda r: type_precedence.get(r.target_type, 0), default=None)

            score_allow = type_precedence.get(highest_allow.target_type, 0) if highest_allow else -1
            score_block = type_precedence.get(highest_block.target_type, 0) if highest_block else -1

            if score_allow >= score_block:
                return {
                    "action": RuleAction.ALLOW,
                    "matched_rule_id": highest_allow.id,
                    "target_type": highest_allow.target_type,
                    "reason": f"Allowed by explicit rule for {highest_allow.target_value}"
                }
            else:
                return {
                    "action": RuleAction.BLOCK,
                    "matched_rule_id": highest_block.id,
                    "target_type": highest_block.target_type,
                    "reason": f"Blocked by rule for {highest_block.target_value}"
                }

        return {
            "action": None,
            "matched_rule_id": None,
            "target_type": None,
            "reason": "No active rule matched"
        }

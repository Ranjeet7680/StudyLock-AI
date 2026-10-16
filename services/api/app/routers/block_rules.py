"""
StudyLock AI - Block Rules & Testing Router
Ref: StudyLock AI Architecture Specification Section 6 & Section 13.2
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.models import BlockRule, User
from ..schemas.schemas import (
    BlockRuleCreate,
    BlockRuleUpdate,
    BlockRuleResponse,
    TestRuleRequest,
    TestRuleResponse
)
from ..core.auth import get_current_user
from ..core.errors import NotFoundException, ForbiddenException

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from packages.schemas.rules import RuleMatcher, BlockRuleDefinition
from packages.schemas.enums import TargetType, RuleAction, RuleScope

router = APIRouter(prefix="/block-rules", tags=["Block Rules"])


@router.get("", response_model=List[BlockRuleResponse])
def list_block_rules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(BlockRule).filter(BlockRule.user_id == current_user.id).all()


@router.post("", response_model=BlockRuleResponse, status_code=status.HTTP_201_CREATED)
def create_block_rule(
    payload: BlockRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = BlockRule(
        user_id=current_user.id,
        device_id=payload.device_id,
        target_type=payload.target_type,
        target_value=payload.target_value.strip(),
        action=payload.action,
        enabled=payload.enabled,
        revision=1
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=BlockRuleResponse)
def update_block_rule(
    rule_id: str,
    payload: BlockRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(BlockRule).filter(BlockRule.id == rule_id).first()
    if not rule:
        raise NotFoundException("Block rule not found")
    if rule.user_id != current_user.id:
        raise ForbiddenException()

    if payload.target_value is not None:
        rule.target_value = payload.target_value.strip()
    if payload.action is not None:
        rule.action = payload.action
    if payload.enabled is not None:
        rule.enabled = payload.enabled

    rule.revision += 1
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(BlockRule).filter(BlockRule.id == rule_id).first()
    if not rule:
        raise NotFoundException("Block rule not found")
    if rule.user_id != current_user.id:
        raise ForbiddenException()

    db.delete(rule)
    db.commit()
    return None


@router.post("/test", response_model=TestRuleResponse)
def test_block_rule(
    payload: TestRuleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tests what action is taken for a candidate website URL or app package
    according to active rule precedence (Spec Section 6.3).
    """
    rules = db.query(BlockRule).filter(BlockRule.user_id == current_user.id, BlockRule.enabled.is_(True)).all()
    domain_rules = []
    for r in rules:
        try:
            t_type = TargetType(r.target_type)
            r_action = RuleAction(r.action)
            domain_rules.append(
                BlockRuleDefinition(
                    id=r.id,
                    user_id=r.user_id,
                    target_type=t_type,
                    target_value=r.target_value,
                    action=r_action,
                    enabled=r.enabled,
                    revision=r.revision
                )
            )
        except Exception:
            continue

    result = RuleMatcher.evaluate(domain_rules, payload.candidate)
    return TestRuleResponse(
        action=result["action"].value if result["action"] else None,
        matched_rule_id=result["matched_rule_id"],
        reason=result["reason"]
    )

from __future__ import annotations

import json
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import or_

from .auth import get_current_user
from .database import SessionLocal
from .models.question_bank import QuestionBank, QuestionBankMember, QuestionBankVersion, QuestionItem
from .models.user import User
from .third_party.jianying import build_hint_board

router = APIRouter(prefix="/api/new-quiz", tags=["new-quiz"])


class BankInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    visibility: Literal["private", "public", "unlisted"] = "private"


class QuestionInput(BaseModel):
    question_type: Literal["single_choice", "text", "jianying", "multi_hint",
                           "streaming_text"] = "single_choice"
    prompt: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list, max_length=8)
    correct_option_index: int = 0
    accepted_answers: list[str] = Field(default_factory=list, max_length=20)
    explanation: str = ""
    default_score: int = Field(default=10, ge=0, le=10000)
    hints: list[str] = Field(default_factory=list, max_length=6)
    hint_interval_seconds: int = Field(default=20, ge=1, le=300)
    character_interval_ms: int = Field(default=120, ge=20, le=5000)
    answer_time_after_reveal_seconds: int = Field(default=10, ge=0, le=300)


class MemberInput(BaseModel):
    user_id: int
    role: Literal["viewer", "editor"]


def permission(db, bank: QuestionBank, user_id: int) -> str | None:
    if bank.owner_id == user_id:
        return "owner"
    member = db.query(QuestionBankMember).filter_by(bank_id=bank.id, user_id=user_id).first()
    return member.role if member else None


def require_bank(db, bank_id: int) -> QuestionBank:
    bank = db.query(QuestionBank).filter_by(id=bank_id).first()
    if not bank:
        raise HTTPException(404, "题库不存在")
    return bank


def require_editor(db, bank: QuestionBank, user_id: int) -> str:
    role = permission(db, bank, user_id)
    if role not in {"owner", "editor"}:
        raise HTTPException(403, "没有编辑该题库的权限")
    return role


def bank_view(db, bank: QuestionBank, user_id: int, include_questions=False):
    role = permission(db, bank, user_id)
    result = {"id": bank.id, "title": bank.title, "description": bank.description,
              "visibility": bank.visibility, "status": bank.status,
              "current_version": bank.current_version, "owner_id": bank.owner_id,
              "role": role, "can_edit": role in {"owner", "editor"}}
    if include_questions:
        questions = db.query(QuestionItem).filter_by(bank_id=bank.id).order_by(QuestionItem.position, QuestionItem.id).all()
        result["questions"] = [question_item_view(item) for item in questions]
    return result


def question_item_view(item: QuestionItem) -> dict:
    answer = json.loads(item.correct_answer_json)
    result = {"id": item.id, "type": item.question_type, "prompt": item.prompt,
              "explanation": item.explanation, "default_score": item.default_score}
    content = json.loads(item.content_json or "{}")
    if item.question_type == "single_choice":
        result.update(options=json.loads(item.options_json), correct_option_id=answer["option_id"])
    else:
        result["accepted_answers"] = answer["accepted_answers"]
    result["content"] = content
    return result


def question_payload(data: QuestionInput) -> tuple[str, str, str]:
    if data.question_type == "single_choice":
        if len(data.options) < 2 or any(not value.strip() for value in data.options):
            raise HTTPException(422, "单选题至少需要两个非空选项")
        if not 0 <= data.correct_option_index < len(data.options):
            raise HTTPException(422, "正确选项索引无效")
        options = [{"id": chr(65 + index), "text": text.strip()} for index, text in enumerate(data.options)]
        answer = {"option_id": options[data.correct_option_index]["id"]}
        return (json.dumps(options, ensure_ascii=False),
                json.dumps(answer, ensure_ascii=False), "{}")
    answers = [value.strip() for value in data.accepted_answers if value.strip()]
    if not answers:
        raise HTTPException(422, "问答题至少需要一个非空答案")
    content = {}
    if data.question_type == "multi_hint":
        hints = [value.strip() for value in data.hints]
        if len(hints) != 6 or any(not value for value in hints):
            raise HTTPException(422, "多提示题必须填写六个提示")
        content = {"hints": hints, "hint_interval_seconds": data.hint_interval_seconds}
    elif data.question_type == "streaming_text":
        content = {"character_interval_ms": data.character_interval_ms,
                   "answer_time_after_reveal_seconds": data.answer_time_after_reveal_seconds}
    return ("[]", json.dumps({"accepted_answers": answers}, ensure_ascii=False),
            json.dumps(content, ensure_ascii=False))


@router.get("/banks")
async def list_banks(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        member_ids = db.query(QuestionBankMember.bank_id).filter_by(user_id=user.id)
        banks = db.query(QuestionBank).filter(or_(QuestionBank.owner_id == user.id,
            QuestionBank.visibility == "public", QuestionBank.id.in_(member_ids))).order_by(QuestionBank.updated_at.desc()).all()
        return {"banks": [bank_view(db, bank, user.id) for bank in banks]}
    finally:
        db.close()


@router.get("/banks/available")
async def available_banks(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        member_ids = db.query(QuestionBankMember.bank_id).filter_by(user_id=user.id)
        banks = db.query(QuestionBank).filter(QuestionBank.status == "published",
            or_(QuestionBank.owner_id == user.id, QuestionBank.visibility == "public",
                QuestionBank.id.in_(member_ids))).all()
        return {"banks": [bank_view(db, bank, user.id) for bank in banks]}
    finally:
        db.close()


@router.post("/banks", status_code=status.HTTP_201_CREATED)
async def create_bank(data: BankInput, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = QuestionBank(owner_id=user.id, **data.dict())
        db.add(bank); db.commit(); db.refresh(bank)
        return bank_view(db, bank, user.id, True)
    finally:
        db.close()


@router.get("/banks/{bank_id}")
async def get_bank(bank_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id)
        role = permission(db, bank, user.id)
        if not role and bank.visibility != "public":
            raise HTTPException(403, "没有查看该题库的权限")
        return bank_view(db, bank, user.id, role in {"owner", "editor"})
    finally:
        db.close()


@router.put("/banks/{bank_id}")
async def update_bank(bank_id: int, data: BankInput, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id); require_editor(db, bank, user.id)
        for key, value in data.dict().items(): setattr(bank, key, value)
        bank.status = "draft"; db.commit(); db.refresh(bank)
        return bank_view(db, bank, user.id, True)
    finally:
        db.close()


@router.delete("/banks/{bank_id}")
async def delete_bank(bank_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id)
        if bank.owner_id != user.id:
            raise HTTPException(403, "只有题库所有者可以删除题库")
        db.delete(bank); db.commit()
        return {"success": True}
    finally:
        db.close()


@router.post("/banks/{bank_id}/questions", status_code=status.HTTP_201_CREATED)
async def add_question(bank_id: int, data: QuestionInput, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id); require_editor(db, bank, user.id)
        options_json, answer_json, content_json = question_payload(data)
        position = db.query(QuestionItem).filter_by(bank_id=bank_id).count()
        item = QuestionItem(bank_id=bank_id, question_type=data.question_type,
            prompt=data.prompt, options_json=options_json, correct_answer_json=answer_json,
            content_json=content_json, explanation=data.explanation,
            default_score=data.default_score, position=position)
        db.add(item); bank.status = "draft"; db.commit(); db.refresh(item)
        return {"id": item.id}
    finally:
        db.close()


@router.delete("/banks/{bank_id}/questions/{question_id}")
async def delete_question(bank_id: int, question_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id); require_editor(db, bank, user.id)
        item = db.query(QuestionItem).filter_by(id=question_id, bank_id=bank_id).first()
        if not item: raise HTTPException(404, "题目不存在")
        db.delete(item); bank.status = "draft"; db.commit()
        return {"success": True}
    finally:
        db.close()


@router.put("/banks/{bank_id}/questions/{question_id}")
async def update_question(bank_id: int, question_id: int, data: QuestionInput,
                          user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id); require_editor(db, bank, user.id)
        item = db.query(QuestionItem).filter_by(id=question_id, bank_id=bank_id).first()
        if not item: raise HTTPException(404, "题目不存在")
        options_json, answer_json, content_json = question_payload(data)
        item.question_type = data.question_type
        item.prompt = data.prompt
        item.options_json = options_json
        item.correct_answer_json = answer_json
        item.content_json = content_json
        item.explanation = data.explanation
        item.default_score = data.default_score
        bank.status = "draft"; db.commit()
        return {"success": True}
    finally:
        db.close()


@router.post("/banks/{bank_id}/publish")
async def publish_bank(bank_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id); require_editor(db, bank, user.id)
        items = db.query(QuestionItem).filter_by(bank_id=bank_id).order_by(QuestionItem.position, QuestionItem.id).all()
        if not items: raise HTTPException(409, "题库至少需要一道题才能发布")
        questions = []
        for item in items:
            view = question_item_view(item)
            view["id"] = str(item.id)
            if item.question_type == "jianying":
                answer = view["accepted_answers"][0]
                view["hint_board"] = build_hint_board(answer, secrets.randbits(31))
            questions.append(view)
        version = bank.current_version + 1
        snapshot = {"bank_id": bank.id, "version": version, "title": bank.title, "questions": questions}
        db.add(QuestionBankVersion(bank_id=bank.id, version=version, title=bank.title,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False), published_by=user.id))
        bank.current_version = version; bank.status = "published"; db.commit()
        return {"bank_id": bank.id, "version": version, "question_count": len(questions)}
    finally:
        db.close()


@router.put("/banks/{bank_id}/members")
async def set_member(bank_id: int, data: MemberInput, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        bank = require_bank(db, bank_id)
        if bank.owner_id != user.id: raise HTTPException(403, "只有题库所有者可以管理协作者")
        member = db.query(QuestionBankMember).filter_by(bank_id=bank_id, user_id=data.user_id).first()
        if member: member.role = data.role
        else: db.add(QuestionBankMember(bank_id=bank_id, user_id=data.user_id, role=data.role))
        db.commit(); return {"success": True}
    finally:
        db.close()

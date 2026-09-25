from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from . import Base


class QuestionBank(Base):
    __tablename__ = "new_quiz_question_banks"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False, default="")
    visibility = Column(String(20), nullable=False, default="private")
    status = Column(String(20), nullable=False, default="draft")
    current_version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuestionBankMember(Base):
    __tablename__ = "new_quiz_question_bank_members"
    __table_args__ = (UniqueConstraint("bank_id", "user_id", name="uq_new_quiz_bank_member"),)

    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, ForeignKey("new_quiz_question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")


class QuestionItem(Base):
    __tablename__ = "new_quiz_questions"

    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, ForeignKey("new_quiz_question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type = Column(String(30), nullable=False, default="single_choice")
    prompt = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    correct_answer_json = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False, default="")
    default_score = Column(Integer, nullable=False, default=10)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuestionBankVersion(Base):
    __tablename__ = "new_quiz_question_bank_versions"
    __table_args__ = (UniqueConstraint("bank_id", "version", name="uq_new_quiz_bank_version"),)

    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, ForeignKey("new_quiz_question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    title = Column(String(120), nullable=False)
    snapshot_json = Column(Text, nullable=False)
    published_by = Column(Integer, nullable=False)
    published_at = Column(DateTime, nullable=False, default=datetime.utcnow)

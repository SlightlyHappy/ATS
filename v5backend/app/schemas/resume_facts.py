from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class Identity(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

class ExperienceItem(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[str] = None

class Skills(BaseModel):
    hard: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)

class Culture(BaseModel):
    leadership: Optional[str] = None
    teamwork: Optional[str] = None
    communication: Optional[str] = None
    values: Optional[str] = None

class ResumeFactsModel(BaseModel):
    identity: Identity = Field(default_factory=Identity)
    summary_short: Optional[str] = None
    summary_detailed: Optional[str] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    culture: Culture = Field(default_factory=Culture)
    domain: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None

class FactsWithScores(BaseModel):
    facts: ResumeFactsModel
    scores: dict = Field(default_factory=dict)

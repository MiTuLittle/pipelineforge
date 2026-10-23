from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
    git_url: AnyHttpUrl

    @field_validator("git_url")
    @classmethod
    def require_repository_path(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if not value.path or value.path == "/":
            raise ValueError("git_url must include a repository path")
        return value


class ProjectRead(BaseModel):
    id: int
    name: str
    git_url: str
    created_at: str


class RunCreate(BaseModel):
    git_ref: str = Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9._/-]+$")


class RunRead(BaseModel):
    id: int
    project_id: int
    git_ref: str
    status: Literal["pending", "running", "succeeded", "failed"]
    detail: str | None
    created_at: str
    updated_at: str


class RunTransition(BaseModel):
    status: Literal["running", "succeeded", "failed"]
    detail: str | None = Field(default=None, max_length=2000)

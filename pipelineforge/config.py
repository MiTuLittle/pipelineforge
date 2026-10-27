import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("PIPELINEFORGE_DB_PATH", "./pipelineforge.db"))


settings = Settings()

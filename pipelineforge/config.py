from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("PIPELINEFORGE_DB_PATH", "./pipelineforge.db"))


settings = Settings()

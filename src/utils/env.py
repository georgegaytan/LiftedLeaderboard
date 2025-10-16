import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def _find_project_root(start: Optional[Path] = None) -> Path:
    start = start or Path(__file__).resolve()
    current = start if start.is_dir() else start.parent
    markers = {'pyproject.toml', 'requirements.txt', '.git'}
    while True:
        if any((current / m).exists() for m in markers):
            return current
        if current.parent == current:
            return start if start.is_dir() else start.parent
        current = current.parent


def _resolve_env_filename() -> str:
    env_file = os.getenv('ENV_FILE')
    if env_file:
        return env_file

    env = (os.getenv('ENV') or os.getenv('PYTHON_ENV') or 'local').lower()
    if env in {'prod', 'production'}:
        return '.env.prod'
    return '.env.local'


def load_env(override: bool = False) -> Path:
    root = _find_project_root()
    target = _resolve_env_filename()

    env_path = Path(target)
    if not env_path.is_absolute():
        env_path = root / target

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=override)
    else:
        fallback = root / '.env'
        if fallback.exists():
            load_dotenv(dotenv_path=fallback, override=override)

    return env_path

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class FileStorage:
    def __init__(self, data_root: Path = None):
        self.data_root = data_root or Path("data")
        self.data_root.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: int) -> Path:
        user_dir = self.data_root / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_user_files(self, user_id: int) -> tuple[Path, Path]:
        user_dir = self._get_user_dir(user_id)
        return (user_dir / "articules.txt", user_dir / "results.json")
    
    def load_articules_for(self, user_id: int) -> List[str]:
        articules_file, _ = self._get_user_files(user_id)
        if not articules_file.exists():
            return []
        try:
            return [line.strip() for line in articules_file.read_text("utf-8").splitlines() if line.strip()]
        except Exception as e:
            logger.error(f"Error loading articules for user {user_id}: {e}")
            return []
    
    def save_articules_for(self, user_id: int, articules: List[str]) -> None:
        articules_file, _ = self._get_user_files(user_id)
        try:
            articules_file.write_text("\n".join(articules) + "\n", encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving articules for user {user_id}: {e}")
    
    def load_results_for(self, user_id: int) -> List[Dict]:
        _, results_file = self._get_user_files(user_id)
        if not results_file.exists():
            return []
        try:
            return json.loads(results_file.read_text("utf-8"))
        except Exception as e:
            logger.error(f"Error loading products for user {user_id}: {e}")
            return []
    
    def save_results_for(self, user_id: int, data: List[Dict]) -> None:
        _, results_file = self._get_user_files(user_id)
        try:
            results_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving products for user {user_id}: {e}")

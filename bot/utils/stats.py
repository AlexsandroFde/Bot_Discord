import json
import os
import threading

# Estatísticas de reprodução persistidas em disco, sobrevivendo a reinícios.
_DATA_DIR   = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
_STATS_FILE = os.path.join(_DATA_DIR, 'play_counts.json')

_lock:   threading.Lock   = threading.Lock()
_counts: dict[str, int]   = {}


def _load() -> None:
    global _counts
    try:
        with open(_STATS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        _counts = {str(k): int(v) for k, v in data.items()}
    except Exception:
        _counts = {}


def _save() -> None:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_counts, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def record_play(name: str) -> None:
    """Incrementa o contador de reprodução de um áudio e persiste em disco."""
    with _lock:
        _counts[name] = _counts.get(name, 0) + 1
        _save()


def top_plays(limit: int = 10) -> list[tuple[str, int]]:
    """Retorna os áudios mais tocados, do mais para o menos reproduzido."""
    with _lock:
        return sorted(_counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]


def play_count(name: str) -> int:
    return _counts.get(name, 0)


_load()

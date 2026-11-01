from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source_path(root, relative):
    root = Path(root)
    original = root/relative
    if original.exists():
        return original
    for folder in ('src','scripts'):
        candidate = root/folder/relative
        if candidate.exists():
            return candidate
    if root.resolve()!=ROOT:
        return source_path(ROOT,relative)
    raise FileNotFoundError(relative)

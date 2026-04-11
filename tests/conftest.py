"""pytest configuration"""

import sys
from pathlib import Path

import pytest

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 配置 pytest
pytest_plugins = []
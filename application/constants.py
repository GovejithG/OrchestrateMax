import os

WORKSPACE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
)
os.makedirs(WORKSPACE_DIR, exist_ok=True)

import os

from backend.config import REPO_ROOT, resolve_repo_path


def test_relative_path_resolved_against_repo_root_not_cwd():
    assert resolve_repo_path("ai_reference/x.ckpt") == os.path.join(REPO_ROOT, "ai_reference", "x.ckpt")


def test_absolute_and_empty_paths_unchanged():
    assert resolve_repo_path("/tmp/model.ckpt") == "/tmp/model.ckpt"
    assert resolve_repo_path("") == ""

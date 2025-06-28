import os
import tempfile
import pytest
import sys

# Permet d'importer depuis le dossier clients/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clients')))
from github_client import GitHubClient

@pytest.fixture
def github():
    return GitHubClient()

def test_upload_read_delete_file(github):
    # 1. Créer un fichier temporaire
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as tmp:
        tmp.write("# Titre de test\n\nContenu temporaire pour GitHub")
        tmp_path = tmp.name
        tmp_filename = os.path.basename(tmp_path)

    remote_path = f"MH/{tmp_filename}"

    try:
        # 2. Upload sur GitHub
        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()
        github.upload_file(remote_path, content, "Test upload")

        # 3. Lire le fichier depuis GitHub
        remote_content = github.get_file(remote_path)
        assert "# Titre de test" in remote_content

        # 4. Vérifier qu’il est listé
        files = github.list_files("MH")
        assert any(remote_path.endswith(os.path.basename(f)) for f in files)

        # 5. Supprimer le fichier depuis GitHub
        github.delete_file(remote_path, "Test suppression")

        # 6. Vérifier qu’il est bien supprimé
        with pytest.raises(Exception):
            github.get_file(remote_path)

    finally:
        # 7. Supprimer le fichier local
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

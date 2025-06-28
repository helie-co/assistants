import json
import pytest
from clients.github_client import GitHubClient
from services.backlog_builder_from_emails import BacklogBuilderFromEmails
from data.action import Action

@pytest.mark.integration
def test_build_backlog_file_from_multiple_sources():
    github = GitHubClient()
    source_dirs = ["MH/emails", "MH/transcriptions"]
    backlog_path = "MH/backlog.json"

    builder = BacklogBuilderFromEmails(
        github=github,
        source_dirs=source_dirs,
        backlog_path=backlog_path
    )

    builder.build_backlog_file()

    # Vérification que le fichier a bien été créé sur GitHub
    content = github.get_file(backlog_path)
    assert content, "❌ Le fichier backlog.json n'a pas été créé ou est vide"

    actions_data = json.loads(content)
    actions = [Action(**a) for a in actions_data]

    assert isinstance(actions, list), "❌ Le contenu du backlog n'est pas une liste"
    assert all(isinstance(a, Action) for a in actions), "❌ Tous les éléments ne sont pas des instances d'Action"
    assert len(actions) > 0, "⚠️ Aucune action détectée dans le backlog"

    for action in actions:
        assert action.source, "❌ Le champ 'source' est manquant ou vide"
        assert isinstance(action.source, str), "❌ Le champ 'source' doit être une chaîne de caractères"
        assert any(action.source.startswith(d) for d in source_dirs), f"❌ Le champ 'source' ne provient pas d'un répertoire autorisé : {action.source}"

    print(f"[TEST ✅] {len(actions)} action(s) détectée(s) avec champ source dans backlog GitHub.")

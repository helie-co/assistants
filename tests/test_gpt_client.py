import os
import pytest
import requests
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clients')))
from gpt_client import GPTClient  # adapte le nom du fichier/module si nécessaire

# On utilise requests-mock pour éviter les appels réels à l'API
def test_complete_success(requests_mock):
    mock_url = "https://api.openai.com/v1/chat/completions"
    expected_output = "Voici une réponse simulée."

    # Mock de la réponse JSON de l'API OpenAI
    mock_response = {
        "choices": [{
            "message": {
                "content": expected_output
            }
        }]
    }

    requests_mock.post(mock_url, json=mock_response, status_code=200)

    client = GPTClient(api_key="fake_api_key", model="gpt-4o")
    result = client.complete(prompt="Bonjour", system_prompt="Tu es un assistant.")
    
    assert result == expected_output

def test_complete_timeout(requests_mock):
    mock_url = "https://api.openai.com/v1/chat/completions"

    def timeout_callback(request, context):
        raise requests.exceptions.Timeout()

    requests_mock.post(mock_url, text=timeout_callback)

    client = GPTClient(api_key="fake_api_key", model="gpt-4o")

    with pytest.raises(RuntimeError, match="La requête GPT a expiré."):
        client.complete(prompt="Hello")

def test_complete_http_error(requests_mock):
    mock_url = "https://api.openai.com/v1/chat/completions"

    requests_mock.post(mock_url, status_code=500, text="Erreur interne")

    client = GPTClient(api_key="fake_api_key", model="gpt-4o")

    with pytest.raises(RuntimeError, match="Erreur HTTP GPT"):
        client.complete(prompt="Test erreur")

def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Veuillez définir OPENAI_API_KEY"):
        GPTClient()

import os
import requests
import urllib3
import streamlit as st
from dotenv import load_dotenv

class GPTClient:
    def __init__(self, api_key: str = None, model: str = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]
        if not self.api_key:
            raise ValueError("Veuillez définir OPENAI_API_KEY dans le fichier .env")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.url = "https://api.openai.com/v1/chat/completions"
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def complete(
        self,
        prompt: str,
        system_prompt: str = "Tu es un assistant professionnel.",
        temperature: float = 0.3,
        max_tokens: int = 512,
        timeout: float = 15.0  # Ajout d’un timeout explicite
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            with requests.Session() as session:
                response = session.post(
                    self.url,
                    headers=headers,
                    json=data,
                    timeout=timeout,
                    verify=False
                )
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content'].strip()

        except requests.exceptions.Timeout:
            raise RuntimeError("La requête GPT a expiré.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur HTTP GPT : {e}")

    def summarize_email(self, body: str) -> str:
        """
        Utilise GPT pour générer un résumé concis et professionnel du corps de l'email.
        """
        if not body.strip():
            return ""

        prompt = (
            "Voici le corps d’un email professionnel. Résume-le en une ou deux phrases claires et précises, "
            "en conservant les informations clés. Ignore les formules de politesse ou les signatures :\n\n"
            f"{body.strip()}"
        )

        try:
            return self.complete(
                prompt=prompt,
                system_prompt="Tu es un assistant qui génère des résumés d’emails professionnels en français.",
                temperature=0.4,
                max_tokens=200
            )
        except Exception as e:
            print(f"[GPT] Échec du résumé : {e}")
            return ""

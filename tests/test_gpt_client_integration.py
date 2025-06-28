import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clients')))
from clients.gpt_client import GPTClient

class TestGPTClientIntegration(unittest.TestCase):
    def setUp(self):
        self.client = GPTClient()

    def test_complete_simple_prompt(self):
        prompt = "Peux-tu résumer cet email ? Bonjour, je vous propose une réunion demain à 14h pour discuter du budget."
        system = "Tu es un assistant professionnel spécialisé en gestion de projet."
        try:
            result = self.client.complete(prompt=prompt, system_prompt=system)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 10)
            print("\n✅ Résumé reçu :", result)
        except Exception as e:
            self.fail(f"Erreur pendant l’appel à GPT : {e}")

if __name__ == "__main__":
    unittest.main()

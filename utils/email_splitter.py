import re
import yaml
from pathlib import Path
from datetime import datetime
from data.email_message import EmailMessage


class EmailSplitter:
    """
    Découpe un fichier markdown contenant un ou plusieurs emails (y compris avec transferts et historiques)
    en plusieurs objets EmailMessage distincts.
    """

    def split_markdown_file(self, path: Path) -> list[EmailMessage]:
        """
        Lit un fichier .md avec un header YAML et un corps contenant possiblement des emails transférés,
        et retourne une liste d'objets EmailMessage (le message principal + chaque forward séparément).
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        parts = raw.split("---")
        if len(parts) < 3:
            raise ValueError(f"Fichier {path} invalide : header YAML manquant")

        header_str, body = parts[1], "---".join(parts[2:])
        metadata = yaml.safe_load(header_str)

        # Conversion date
        raw_date = metadata.get("date", "")
        try:
            date = datetime.fromisoformat(raw_date)
        except Exception:
            try:
                date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
            except Exception:
                date = datetime.now()

        messages = self._split_body_into_messages(body.strip())
        email_messages = []

        for i, msg_body in enumerate(messages):
            email_messages.append(EmailMessage(
                id=f"{metadata.get('id')}_{i+1}" if i > 0 else metadata.get("id"),
                subject=metadata.get("subject", ""),
                date=date,
                sender=metadata.get("author", "expediteur@inconnu"),
                recipients=metadata.get("recipients", []),
                source=metadata.get("source", "inbox"),
                body=msg_body.strip()
            ))

        return email_messages

    def _split_body_into_messages(self, full_text: str) -> list[str]:
        """
        Utilise des motifs communs de forward/reply pour découper le corps en messages indépendants.
        """

        # Ajoute un séparateur fictif au tout début pour inclure le message principal
        fake_header = "\n===DÉBUT===\n"
        text = fake_header + full_text

        separators = re.compile(r"""
            (^Début\s+du\s+message\s+transféré\s?:)|  # "Début du message transféré :"
            (^[-]{5,}.*message.*[-]{5,})|             # ----- Message transféré -----
            (^De\s?:.*\nDate\s?:.*\n(?:À|Cc)\s?:.*\nObjet\s?:.*)  # En-tête standard
        """, re.MULTILINE | re.IGNORECASE | re.VERBOSE)

        indices = [m.start() for m in separators.finditer(text)]
        if not indices:
            return [full_text.strip()]

        indices.append(len(text))
        messages = []

        for i in range(len(indices) - 1):
            chunk = text[indices[i]:indices[i + 1]].strip()
            # On enlève le faux header pour le premier message
            if chunk.startswith("===DÉBUT==="):
                chunk = chunk.replace("===DÉBUT===", "").strip()
            messages.append(chunk)

        return messages

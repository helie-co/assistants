from dataclasses import dataclass

@dataclass
class Action:
    sujet: str
    demandeur: str
    date: str
    porteur: str
    statut: str
    tag: str
    source: str = ""  # chemin du fichier .md dans le repo

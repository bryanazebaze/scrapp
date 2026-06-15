from abc import ABC, abstractmethod
from typing import List
from core.models import Annonce

class BaseScraper(ABC):
    def __init__(self):
        self.platform_name = "Base"

    @abstractmethod
    def scrape(self) -> List[Annonce]:
        """
        Méthode principale à implémenter par chaque scraper spécifique.
        Doit retourner une liste d'objets Annonce (SQLAlchemy models)
        prêts à être insérés en base de données.
        """
        pass

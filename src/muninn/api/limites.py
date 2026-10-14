"""Limite de débit globale des appels au LLM : borne le coût d'une route publique.

La limite est globale et non par client : la console appelle l'API côté serveur, si bien que
tous ses visiteurs partagent la même adresse. Le compteur vit en mémoire, ce qui suffit avec une
réplique au plus par application (infra/azure/03-applications.sh) ; avec N répliques, la limite
effective serait multipliée par N.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable


class LimiteurDebit:
    """Fenêtres glissantes : au plus `maximum` appels par période de `duree_s` secondes."""

    def __init__(
        self,
        fenetres: list[tuple[float, int]],
        horloge: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fenetres = fenetres
        self._horloge = horloge
        self._appels: deque[float] = deque()
        self._verrou = threading.Lock()
        self._plus_longue = max(duree for duree, _ in fenetres)

    def reserver(self) -> int | None:
        """Enregistre un appel s'il est permis ; sinon rend l'attente en secondes, arrondie."""
        with self._verrou:
            maintenant = self._horloge()
            while self._appels and maintenant - self._appels[0] >= self._plus_longue:
                self._appels.popleft()
            attente = 0.0
            for duree, maximum in self._fenetres:
                if maximum <= 0:  # limite nulle : appels coupés
                    attente = max(attente, duree)
                    continue
                recents = [t for t in self._appels if maintenant - t < duree]
                if len(recents) >= maximum:
                    attente = max(attente, recents[len(recents) - maximum] + duree - maintenant)
            if attente > 0:
                return max(1, math.ceil(attente))
            self._appels.append(maintenant)
            return None

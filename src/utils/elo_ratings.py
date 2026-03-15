import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Tuple

from bots.registry import list_bot_ids

DEFAULT_ELO = 1200.0
DEFAULT_K_FACTOR = 32.0
DEFAULT_TIERS = (200, 500, 800)


@dataclass
class EloUpdate:
    tier: int
    agent_a: str
    agent_b: str
    old_a: float
    old_b: float
    new_a: float
    new_b: float


class EloRatings:
    def __init__(
        self,
        file_path: str = "data/elo_ratings.json",
        tiers: Iterable[int] = DEFAULT_TIERS,
        default_rating: float = DEFAULT_ELO,
        k_factor: float = DEFAULT_K_FACTOR,
    ):
        self.file_path = Path(file_path)
        self.tiers = tuple(sorted(int(t) for t in tiers))
        self.default_rating = float(default_rating)
        self.k_factor = float(k_factor)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load_or_init()

    @staticmethod
    def _expected_score(rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

    def _empty_tier(self) -> Dict:
        return {"agents": {}, "games_played": 0, "updated_at": None}

    def _load_or_init(self) -> Dict:
        if self.file_path.exists():
            with open(self.file_path) as f:
                data = json.load(f)
        else:
            data = {
                "version": 1,
                "default_rating": self.default_rating,
                "k_factor": self.k_factor,
                "tiers": {},
            }

        tiers = data.setdefault("tiers", {})
        for tier in self.tiers:
            tiers.setdefault(str(tier), self._empty_tier())

        for tier_key, tier_data in tiers.items():
            agents = tier_data.setdefault("agents", {})
            for bot_id in list_bot_ids():
                agents.setdefault(bot_id, self.default_rating)
            tier_data.setdefault("games_played", 0)
            tier_data.setdefault("updated_at", None)

        self._atomic_save(data)
        return data

    def _atomic_save(self, data: Dict) -> None:
        temp_path = self.file_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        temp_path.replace(self.file_path)

    def _tier_bucket(self, tier: int) -> Dict:
        tier_key = str(int(tier))
        tiers = self._data["tiers"]
        if tier_key not in tiers:
            raise ValueError(f"Unsupported Elo tier '{tier}'. Expected one of: {', '.join(map(str, self.tiers))}")
        return tiers[tier_key]

    def get_rating(self, tier: int, agent_id: str) -> float:
        bucket = self._tier_bucket(tier)
        return float(bucket["agents"].setdefault(agent_id, self.default_rating))

    def update_result(self, tier: int, agent_a: str, agent_b: str, score_a: float) -> EloUpdate:
        if score_a not in (0.0, 0.5, 1.0):
            raise ValueError("score_a must be 0.0 (loss), 0.5 (draw), or 1.0 (win)")

        bucket = self._tier_bucket(tier)
        agents = bucket["agents"]
        old_a = float(agents.setdefault(agent_a, self.default_rating))
        old_b = float(agents.setdefault(agent_b, self.default_rating))

        exp_a = self._expected_score(old_a, old_b)
        exp_b = self._expected_score(old_b, old_a)
        score_b = 1.0 - score_a

        new_a = old_a + self.k_factor * (score_a - exp_a)
        new_b = old_b + self.k_factor * (score_b - exp_b)

        agents[agent_a] = new_a
        agents[agent_b] = new_b
        bucket["games_played"] = int(bucket.get("games_played", 0)) + 1
        bucket["updated_at"] = datetime.now().isoformat()

        self._atomic_save(self._data)
        return EloUpdate(
            tier=int(tier),
            agent_a=agent_a,
            agent_b=agent_b,
            old_a=old_a,
            old_b=old_b,
            new_a=new_a,
            new_b=new_b,
        )

    def leaderboard(self, tier: int) -> Tuple[Tuple[str, float], ...]:
        bucket = self._tier_bucket(tier)
        pairs = sorted(bucket["agents"].items(), key=lambda item: item[1], reverse=True)
        return tuple((agent, float(rating)) for agent, rating in pairs)

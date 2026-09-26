import json

from pydantic import BaseModel, Field

from app.config import BASE_DIR

RULES_PATH = BASE_DIR / "data" / "rules.json"


class Rules(BaseModel):
    max_breaks_per_hour: int = Field(4, ge=1)
    min_gap_seconds: float = Field(300.0, ge=0)
    max_ad_load_percent: float = Field(10.0, gt=0, le=100)
    ad_duration_seconds: float = Field(15.0, gt=0)
    edge_buffer_seconds: float = Field(90.0, ge=0)  # no break this close to start/end
    min_where_score: float = Field(60.0, ge=0, le=100)


def load_rules() -> Rules:
    if RULES_PATH.exists():
        return Rules(**json.loads(RULES_PATH.read_text(encoding="utf-8")))
    return Rules()


def save_rules(rules: Rules) -> Rules:
    RULES_PATH.write_text(rules.model_dump_json(indent=2), encoding="utf-8")
    return rules

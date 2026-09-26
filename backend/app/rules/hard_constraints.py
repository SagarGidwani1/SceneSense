import re
from typing import List, Tuple


def _norm(s: str) -> str:
    return re.sub(r"[\s_\-/]+", " ", s.lower()).strip()


def _words(s: str) -> set:
    return set(_norm(s).split())


def check_negative_context_violation(scene_contexts: List[str], negative_contexts: List[str]) -> Tuple[bool, List[str]]:
    """
    Deterministic lexical hard block. A negative context matches a scene tag when all of its
    words appear in the tag ("funeral" ~ "funeral_mourning", "medical emergency" ~
    "emergency medical ward"). Semantic matches (e.g. "death" vs "mourning")
    come from the AI layer in brand_matcher; this layer can only add blocks, never remove them.
    """
    tags = [_words(t) for t in scene_contexts if t.strip()]
    matched = []
    for neg in negative_contexts:
        nw = _words(neg)
        if nw and any(nw <= tw for tw in tags):
            matched.append(neg)
    return bool(matched), matched

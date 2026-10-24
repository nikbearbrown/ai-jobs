"""Conclusions of ours about a posting, each stamped with the rule that made it (schema: 'inferred').

seniority-v1 is deliberately crude and returns None when the title does not say.
title-ngram-v1 looks for the longest title from data/titles/titles.json inside the posting title.
"""
import json
import re
from functools import lru_cache

from .paths import TITLES

SENIORITY_RULE = "seniority-v1"
TITLE_RULE = "title-ngram-v1"

_RULES = [
    ("intern", re.compile(r"\b(intern|internship|co-?op|apprentice|working student|summer analyst)\b", re.I)),
    ("exec", re.compile(r"\b(chief|c[etfdp]o|svp|evp|vice president|vp\b|president|general manager)\b", re.I)),
    ("director", re.compile(r"\b(director|head of|managing director)\b", re.I)),
    ("entry", re.compile(r"\b(junior|jr\.?|entry[- ]level|new grad(uate)?|graduate|early career|trainee|(?<!senior )associate (?!director|vice|general|partner|principal)|campus|university grad)\b|(?<![a-z])i$|\blevel 1\b", re.I)),
    ("staff", re.compile(r"\b(staff|principal|distinguished)\b", re.I)),
    ("senior", re.compile(r"\b(senior|sr\.?|iii|iv|lead|level [3-9])\b", re.I)),
    ("manager", re.compile(r"\b(engineering manager|manager of|manager, engineering|(software|data science|ml|machine learning|research|security|infrastructure) manager)\b", re.I)),
    ("mid", re.compile(r"\b(ii|level 2)\b", re.I)),
]


def seniority(title):
    for name, rx in _RULES:
        if rx.search(title or ""):
            return name
    return None


@lru_cache(maxsize=1)
def _title_index():
    doc = json.loads(TITLES.read_text())
    idx, longest = {}, 1
    for f in doc["families"]:
        for t in f["titles"]:
            k = _tok(t)
            if k and k not in idx:
                idx[k] = f["key"]
                longest = max(longest, len(k.split()))
    return idx, longest


def _tok(s):
    return " ".join(re.findall(r"[a-z0-9+#.]+", (s or "").lower().replace("&", " and ")))


def title_family(title):
    idx, longest = _title_index()
    toks = _tok(title).split()
    best = (0, None)
    for n in range(min(longest, len(toks)), 0, -1):
        for i in range(0, len(toks) - n + 1):
            fam = idx.get(" ".join(toks[i:i + n]))
            if fam:
                return fam
    return None

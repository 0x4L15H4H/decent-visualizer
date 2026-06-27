import unicodedata
from difflib import SequenceMatcher

from pydantic import BaseModel


class CountryCandidate(BaseModel):
    code: str
    name: str
    score: float


_COUNTRIES = {
    "BO": "Bolivia",
    "BR": "Brazil",
    "BI": "Burundi",
    "CM": "Cameroon",
    "CN": "China",
    "CO": "Colombia",
    "CD": "Democratic Republic of the Congo",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "DO": "Dominican Republic",
    "EC": "Ecuador",
    "SV": "El Salvador",
    "ET": "Ethiopia",
    "GT": "Guatemala",
    "HN": "Honduras",
    "IN": "India",
    "ID": "Indonesia",
    "JM": "Jamaica",
    "KE": "Kenya",
    "LA": "Laos",
    "MW": "Malawi",
    "MX": "Mexico",
    "MM": "Myanmar",
    "NI": "Nicaragua",
    "PA": "Panama",
    "PG": "Papua New Guinea",
    "PE": "Peru",
    "PH": "Philippines",
    "RW": "Rwanda",
    "TZ": "Tanzania",
    "TH": "Thailand",
    "TL": "Timor-Leste",
    "UG": "Uganda",
    "US": "United States",
    "VE": "Venezuela",
    "VN": "Vietnam",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}

_ALIASES = {
    "columbia": "CO",
    "drc": "CD",
    "dr congo": "CD",
    "congo": "CD",
    "png": "PG",
    "timor leste": "TL",
    "usa": "US",
    "united states of america": "US",
}


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.lower().replace("-", " ").split())


def country_candidates(value: str, *, limit: int = 8) -> list[CountryCandidate]:
    normalized = _normalize(value)
    if not normalized:
        return []

    if normalized.upper() in _COUNTRIES:
        code = normalized.upper()
        return [CountryCandidate(code=code, name=_COUNTRIES[code], score=1.0)]

    if normalized in _ALIASES:
        code = _ALIASES[normalized]
        return [CountryCandidate(code=code, name=_COUNTRIES[code], score=0.98)]

    candidates: list[CountryCandidate] = []
    for code, name in _COUNTRIES.items():
        normalized_name = _normalize(name)
        score = SequenceMatcher(a=normalized, b=normalized_name).ratio()
        if normalized in normalized_name or normalized_name in normalized:
            score = max(score, 0.9)
        if score >= 0.55:
            candidates.append(CountryCandidate(code=code, name=name, score=round(score, 4)))
    return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)[:limit]


def country_name(code: str | None) -> str | None:
    if code is None:
        return None
    return _COUNTRIES.get(code.upper())

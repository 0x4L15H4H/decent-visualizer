export interface NormalizationCandidate {
  id: string;
  kind: "roaster" | "producer" | "farm" | "variety" | "process";
  canonical_name: string;
  aliases: string[];
  score: number;
  match_reason: string;
}

export type EntityKind = NormalizationCandidate["kind"];

export interface CanonicalEntity {
  id: string;
  kind: EntityKind;
  name: string;
  country_code: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CountryCandidate {
  code: string;
  name: string;
  score: number;
}

export interface NormalizationCandidate {
  id: string;
  kind: "roaster" | "producer" | "farm" | "variety" | "process";
  canonical_name: string;
  aliases: string[];
  score: number;
  match_reason: string;
}

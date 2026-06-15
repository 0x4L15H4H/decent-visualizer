import { readFileSync, appendFileSync, writeFileSync } from "fs";
import { resolve } from "path";

function flatten(obj, prefix = "") {
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    const flat = prefix ? `${prefix}_${key}` : key;
    if (typeof value === "object" && value !== null && !Array.isArray(value)) {
      Object.assign(result, flatten(value, flat));
    } else {
      result[flat] = value;
    }
  }
  return result;
}

function parseDeclaredVars(variablesTf) {
  const pattern = /^variable\s+"([^"]+)"/gm;
  const vars = new Set();
  let match;
  while ((match = pattern.exec(variablesTf)) !== null) {
    vars.add(match[1]);
  }
  return vars;
}

const config = JSON.parse(readFileSync(resolve("config/infra.json"), "utf-8"));
const flat = flatten(config);

const lines = Object.entries(flat).map(([k, v]) => `${k}=${v}`);
appendFileSync(process.env.GITHUB_ENV, lines.join("\n") + "\n");

if (process.env.INPUT_TFVARS === "true") {
  const variablesTf = readFileSync(resolve("infra/variables.tf"), "utf-8");
  const declared = parseDeclaredVars(variablesTf);
  const tfvars = {};
  for (const [key, value] of Object.entries(flat)) {
    if (declared.has(key)) {
      tfvars[key] = value;
    }
  }
  writeFileSync(
    resolve("infra/terraform.tfvars.json"),
    JSON.stringify(tfvars, null, 2) + "\n"
  );
}

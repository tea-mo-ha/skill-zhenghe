const SECTION_NAMES = new Set([
  "chosen_subskills",
  "skill_file_reads",
  "routing_context",
  "plan",
  "execution",
  "validation",
  "telemetry",
]);

function parseSections(output) {
  const sections = new Map();
  let current = null;

  for (const line of output.split("\n")) {
    const stripped = line.trim();
    if (SECTION_NAMES.has(stripped)) {
      current = stripped;
      if (!sections.has(current)) {
        sections.set(current, []);
      }
      continue;
    }

    if (current) {
      sections.get(current).push(line);
    }
  }

  return Object.fromEntries(
    Array.from(sections.entries(), ([name, lines]) => [name, lines.join("\n").trim()]),
  );
}

function extractSkills(block) {
  const skills = [];

  for (const rawLine of block.split("\n")) {
    const line = rawLine.trim();
    if (!line.startsWith("-")) {
      continue;
    }
    if (line.startsWith("- [provenance:")) {
      continue;
    }

    const content = line.slice(1).trim();
    const leadMatch = content.match(/^(?:`([^`]+)`|([A-Za-z0-9:_-]+))(?=\s*[:\-]|\s*$)/);
    if (leadMatch) {
      skills.push(leadMatch[1] ?? leadMatch[2]);
      continue;
    }

    let plain = content;
    if (plain.includes(":")) {
      plain = plain.split(":", 1)[0].trim();
    }
    if (plain) {
      skills.push(plain);
    }
  }

  return skills;
}

function extractFileReads(block) {
  const reads = [];
  for (const rawLine of block.split("\n")) {
    const line = rawLine.trim();
    if (line.startsWith("- ")) {
      reads.push(stripWrappingBackticks(line.slice(2).trim()));
    }
  }
  return reads;
}

function stripWrappingBackticks(value) {
  if (value.startsWith("`") && value.endsWith("`") && value.length >= 2) {
    return value.slice(1, -1);
  }
  return value;
}

export function contractAssert(output, context) {
  const requiredSections = context?.config?.required_sections ?? [
    "chosen_subskills",
    "skill_file_reads",
    "routing_context",
    "plan",
    "execution",
    "validation",
    "telemetry",
  ];
  const sections = parseSections(output);
  const missing = requiredSections.filter((name) => !sections[name]);

  if (missing.length) {
    return {
      pass: false,
      score: 0,
      reason: `Missing required sections: ${missing.join(", ")}`,
    };
  }

  return { pass: true, score: 1, reason: "Required sections are present." };
}

export function expectedSkillSetAssert(output, context) {
  const expected = context?.config?.expected_skills ?? [];
  const exactOrder = Boolean(context?.config?.exact_order);
  const sections = parseSections(output);
  const actual = extractSkills(sections.chosen_subskills ?? "");

  if (exactOrder) {
    const actualPrefix = actual.slice(0, expected.length);
    const matches =
      actualPrefix.length === expected.length &&
      actualPrefix.every((skill, index) => skill === expected[index]);

    if (!matches) {
      return {
        pass: false,
        score: 0,
        reason: `Expected chosen_subskills to start with ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
      };
    }
  } else {
    const missing = expected.filter((skill) => !actual.includes(skill));
    if (missing.length) {
      return {
        pass: false,
        score: 0,
        reason: `Missing expected skills: ${JSON.stringify(missing)}; got ${JSON.stringify(actual)}`,
      };
    }
  }

  return { pass: true, score: 1, reason: "Expected skill set matched." };
}

export function expectedAnySkillAssert(output, context) {
  const expectedAny = context?.config?.expected_any_skills ?? [];
  const sections = parseSections(output);
  const actual = extractSkills(sections.chosen_subskills ?? "");

  if (!expectedAny.some((skill) => actual.includes(skill))) {
    return {
      pass: false,
      score: 0,
      reason: `Expected at least one of ${JSON.stringify(expectedAny)}, got ${JSON.stringify(actual)}`,
    };
  }

  return { pass: true, score: 1, reason: "At least one expected skill was selected." };
}

export function noDisallowedSkillsAssert(output, context) {
  const disallowed = new Set(context?.config?.disallowed_skills ?? []);
  const sections = parseSections(output);
  const actual = extractSkills(sections.chosen_subskills ?? "");
  const found = actual.filter((skill) => disallowed.has(skill));

  if (found.length) {
    return {
      pass: false,
      score: 0,
      reason: `Found disallowed skills in chosen_subskills: ${JSON.stringify(found)}`,
    };
  }

  return { pass: true, score: 1, reason: "No disallowed skills were selected." };
}

export function skillFileReadsCoverSelectedAssert(output, context) {
  const managedSkills = new Set(context?.config?.managed_skills ?? []);
  const sections = parseSections(output);
  const selected = extractSkills(sections.chosen_subskills ?? "");
  const reads = extractFileReads(sections.skill_file_reads ?? "");

  const missing = [];
  for (const skill of selected) {
    if (managedSkills.size && !managedSkills.has(skill)) {
      continue;
    }

    const target = `/${skill}/SKILL.md`;
    const covered = reads.some((path) => path.includes(target) || path.endsWith(`${skill}/SKILL.md`));
    if (!covered) {
      missing.push(skill);
    }
  }

  if (missing.length) {
    return {
      pass: false,
      score: 0,
      reason: `Missing skill_file_reads coverage for selected managed skills: ${JSON.stringify(missing)}; reads=${JSON.stringify(reads)}`,
    };
  }

  return { pass: true, score: 1, reason: "Every selected managed skill has a matching child SKILL.md read." };
}

export function skillFileReadsOnlyChildSkillsAssert(output) {
  const sections = parseSections(output);
  const reads = extractFileReads(sections.skill_file_reads ?? "");
  const invalid = [];

  for (const path of reads) {
    if (!path.endsWith("/SKILL.md")) {
      invalid.push(path);
      continue;
    }
    if (path.includes("/skill-suite-orchestrator/SKILL.md")) {
      invalid.push(path);
    }
  }

  if (invalid.length) {
    return {
      pass: false,
      score: 0,
      reason: `skill_file_reads must list only child SKILL.md files; found invalid entries: ${JSON.stringify(invalid)}`,
    };
  }

  return { pass: true, score: 1, reason: "skill_file_reads only lists child SKILL.md paths." };
}

export function mutuallyExclusiveSkillsAssert(output, context) {
  const groups = context?.config?.mutually_exclusive_groups ?? [];
  const sections = parseSections(output);
  const actual = new Set(extractSkills(sections.chosen_subskills ?? ""));
  const violations = [];

  for (const group of groups) {
    const present = group.filter((skill) => actual.has(skill));
    if (present.length > 1) {
      violations.push(present);
    }
  }

  if (violations.length) {
    return {
      pass: false,
      score: 0,
      reason: `Found mutually exclusive skills together: ${JSON.stringify(violations)}`,
    };
  }

  return { pass: true, score: 1, reason: "No mutually exclusive skill combination was selected." };
}

export function fastPathBypassAssert(output) {
  const sections = parseSections(output);
  const hasRouting = Object.hasOwn(sections, "chosen_subskills") || Object.hasOwn(sections, "routing_context");

  if (hasRouting) {
    return {
      pass: false,
      score: 0,
      reason: "Trivial task should bypass routing entirely, but found chosen_subskills or routing_context sections.",
    };
  }

  if (!output || !output.trim()) {
    return {
      pass: false,
      score: 0,
      reason: "Trivial task should produce a direct answer, but got empty output.",
    };
  }

  return { pass: true, score: 1, reason: "Trivial task was answered directly without routing overhead." };
}

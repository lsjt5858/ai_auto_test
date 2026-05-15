Skill implementations live here.

Recommended layout:

- `skills/<skill_name>/scripts/` for executable scripts
- `skills/<skill_name>/README.md` for quick start
- `skills/<skill_name>/SKILL.md` for detailed capability notes

Runtime configuration still lives in `config/skills/<skill_name>.yaml`.
Test cases live in `data/`.

Core notes:

- The script paths under `skills/` are treated as fixed runtime entrypoints by the framework.
- Do not rename, move, or delete files under `skills/<skill_name>/scripts/` unless you also update the matching `config/skills/<skill_name>.yaml`.
- If a script path changes but the YAML is not updated, automation will fail before business execution starts.
- Add new skills under `skills/`, but keep existing script entry files stable.

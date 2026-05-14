---
name: create-crew
description: Step-by-step workflow for creating an agent team for a new project. Use when onboarding a project, creating a crew, or adapting the base for a new stack.
---

# Create Crew Workflow

## Step 1: Read the Project

```bash
# Structure
find <path> -maxdepth 3 -type f | grep -v .git | grep -v node_modules | sort

# Entry points
cat <path>/README.md
cat <path>/AGENTS.md

# Build system (check in order)
cat <path>/.mise.toml        # mise (preferred)
cat <path>/justfile           # just
cat <path>/Makefile           # make
cat <path>/package.json      # npm
cat <path>/pyproject.toml    # python
cat <path>/Cargo.toml        # rust
cat <path>/cdk.json          # CDK

# Existing agents
find <path>/.kiro -type f 2>/dev/null

# Contribution conventions
find <path> -path "*.github/PULL_REQUEST_TEMPLATE*" -o -path "*.github/ISSUE_TEMPLATE*"
cat <path>/CONTRIBUTING.md 2>/dev/null

# Recent history
git -C <path> log --oneline -10
```

## Step 2: Decide What to Build

- **Crews**: Always start with `general`. Add specialized crews based on primary work type.
- **Language**: Python, TypeScript, Rust, Terraform, mixed?
- **Build commands**: What runs tests? What builds? What lints?
- **Dangerous commands**: What should be denied? (deploy, destroy, start servers)
- **Existing agents**: Coexist or replace?
- **Primary work type**: Feature dev? Bug fixes? Docs? Research? All of the above?

## Step 3: Select Crews

Every project gets `general` as baseline. Add specialized crews based on need:

| Primary work | Add crew |
|-------------|----------|
| Bug fixing focus | bug-fix |
| Infrastructure/deploy | infrastructure |
| Research/investigation | research |
| New to codebase | onboarding |
| Maintenance/cleanup | hygiene |
| Presentations/tutorials | content |
| Writing/editing | writing |

Update fleet.yaml:
```yaml
projects:
  <project>:
    crews: [general, <specialized>]  # general is ALWAYS first
```

NEVER omit general. A research project still needs builder/tester for prototyping.

## Step 4: Create the Example

```bash
mkdir -p examples/<project>/.kiro/skills examples/<project>/.kiro/steering
```

Start from `base/crew.yaml` and adapt:
1. Shell allowlist (add project's build/test/lint commands)
2. Denied commands (deploy, destroy, dev servers)
3. Agent prompts (reference project-specific files, patterns, conventions)
4. Resources (load project's key docs as context)

## Step 5: Write Project Steering

Create `examples/<project>/.kiro/steering/project.md` with:
- What the project is (1-2 sentences)
- Stack (language, framework, tools)
- Code layout (where things live)
- Conventions (style, patterns to follow)
- Key commands (build, test, lint)
- DO NOT list (safety guardrails)

## Step 6: Copy Relevant Skills

From `base/skills/`, copy what applies:
- `git-conventions.md` — always
- `contribution-conventions.md` — if contributing upstream
- `code-review.md` — always
- `aws-architecture.md` — if AWS project
- `testing-patterns.md` — if has tests
- `project-setup.md` — if new/scaffolding project

Add project-specific skills if needed (e.g., `terraform-patterns.md` for infrastructure projects).

## Step 7: Generate and Deploy

```bash
python3 generate.py examples/<project>/.kiro/crew.yaml
cp -r examples/<project>/.kiro <target-path>/.kiro
cp base/feedback.md <target-path>/feedback.md
cd <target-path> && git add .kiro/ feedback.md && git commit -m "feat(agents): deploy SA dev crew"
```

## Step 8: Commit in agent-crews

```bash
cd ~/code/agent-crews
git add examples/<project>/
git commit -m "feat(examples): add <project> crew for <description>"
```

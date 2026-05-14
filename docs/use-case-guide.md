# Use Case Guide

How to use your deployed agents for common development tasks.

## The Basics

1. Start kiro in your project: `cd ~/code/my-project && kiro-cli chat`
2. Pick a lead agent: `/agent general-lead` (or whichever crew fits your work)
3. Describe what you need in plain language
4. The lead delegates to specialists automatically

You talk to the lead. It handles the rest.

## Common Workflows

### "I need to build a feature"

```
/agent general-lead
"Add pagination to the /users API endpoint"
```

The lead will: plan the work → delegate research → delegate implementation → delegate testing → commit.

### "I need to fix a bug"

```
/agent bugfix-lead
"The login form crashes when email contains a plus sign"
```

The lead will: reproduce → diagnose root cause → apply minimal fix → verify regression tests pass.

### "I need to understand this codebase"

```
/agent onboarding-lead
"Map this repo — what's the architecture, what's the build system, where are the tests?"
```

The lead will: scan structure → trace architecture → identify gaps → produce onboarding guide.

### "I need to deploy infrastructure"

```
/agent infrastructure-lead
"Deploy the staging environment with the new RDS instance"
```

The lead will: plan deployment sequence → provision resources → verify health → report status.

### "I need to write docs"

```
/agent research-lead
"Document the authentication flow for new developers"
```

The lead will: research the code → draft documentation → fact-check claims → format and commit.

### "I need to create a presentation"

```
/agent content-lead
"Build a 10-slide deck on our new architecture for the team meeting"
```

The lead will: outline structure → write narrative → fact-check → review accessibility → export.

## Tips

- **Be specific about outcomes.** "Tests pass and PR is ready" is better than "fix the thing."
- **Let the lead plan.** Don't micromanage which agent does what — the lead knows.
- **Switch crews when work type changes.** Bug fixing → features? Switch from bugfix-lead to general-lead.
- **Check @crew-sheet** for the full list of available agents and commands.

## When Things Go Wrong

- **Agent is stuck?** Describe what you see. The lead will re-route.
- **Wrong crew for the job?** Just switch: `/agent <other-lead>`
- **Need more control?** Talk to a worker directly: `/agent builder "do exactly this"`

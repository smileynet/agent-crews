---
name: adversarial-review
description: Protocol for fact-checking and adversarial review of claims. Use when reviewing research output, documentation claims, or architecture decisions that need verification.
---

# Adversarial Review Protocol

## 7-Point Check
1. **Source exists** and is accessible
2. **Accuracy**: Claim accurately represents source content
3. **Context**: No cherry-picking (surrounding context preserved)
4. **Recency**: Source is current (not outdated for this domain)
5. **Authority**: Source is credible for this domain
6. **Consistency**: Claim doesn't contradict other verified facts
7. **Completeness**: No critical omissions that change the conclusion

## Stance
- Assume claims are wrong until verified
- Look for the strongest counter-argument
- Flag confidence level: HIGH (verified), MEDIUM (plausible), LOW (unverified)

## Output Format
For each claim reviewed:
```
[CLAIM]: <the assertion>
[SOURCE]: <where it came from>
[VERDICT]: ✅ CONFIRMED | ⚠️ PARTIALLY TRUE | ❌ INCORRECT | 🔍 UNVERIFIABLE
[CONFIDENCE]: HIGH | MEDIUM | LOW
[NOTE]: <context, caveats, or corrections>
```

# What is MedSkillAudit?

MedSkillAudit is a domain-specific audit framework for medical research agent skills. 

## How does MedSkillAudit Work?

### Veto Gates

To enforce strict quality control, MedSkillAudit is designed with two layers of veto mechanisms. Any failure in these checks may lead to immediate rejection of a skill.

#### Skill ​Veto

* Operational Stability
* Structural Consistency
* Result Determinism
* System Security

#### Research ​Veto

* Scientific Integrity
* Practice Boundaries
* Methodological Ground
* Code Usability

### Core Capability (Static)

Evaluates a skill’s design and contract against key dimensions such as **Functional Suitability, Reliability, Performance & Context, Agent Usability, Human Usability, Security, Agent-Specific and Maintainability.**

### Medical Task (Dynamic)

Assesses actual outputs of a skill with layered criteria.

For skill testing, the AI automatically generates inputs. The number of inputs in specific categories will increase or decrease depending on the complexity of the skill. The following 7 inputs represent the most comprehensive version.

* Canonical
* Variant A
* Edge
* Variant B
* Stress
* Scope Boundary
* Adversarial

**Skill Complexity Classification**

| Label    | Code/Rank | Definition                                |
| ---------- | ----------- | ------------------------------------------- |
| Simple   | S         | Narrow task scope                         |
| Moderate |M         | Moderate branching or multiple task types |
| Complex  | C         | Broad or multi-step specialized skill     |

**Simple (S):** 3 inputs

**Moderate (M):** 5 inputs

**Complex (C):** 7 inputs

### Final Score

Skills passing both veto gates received a final quality score. The MedSkillAudit uses a two-stage scoring system: static evaluation (design quality, accounting for 40%) and dynamic evaluation (runtime performance, accounting for 60%). The final overall score is derived by combining both.

* Static (40%)
* Dynamic (60%)

Final Score = Static Score × 40% + Dynamic Score × 60%


# Testing Skill Profile — Annotation Instrument (v0, pre-calibration)

> Status: **v0 — draft, not frozen.** After the calibration round (30 skills, R1 + R2 + LLM) the
> examples are adjusted once (new P10 categories may be added) and the instrument is frozen as v1.
> This exact text is both the human guideline and the LLM prompt. Its SHA-256 is recorded in
> `results/` whenever a sample is exported or a model is run.

## 1. Task

You will read one agent skill (`SKILL.md`): its name, description and up to 8,000 characters of
content. Answer every item with a single question in mind:

> **Does the text instruct the agent to do this?**

Mentioning, listing, or describing something does **not** count. A table of "test types" with no
instruction to write or run them is NO. An imperative ("write…", "run…", "always…", "never…",
"must…"), a step in a workflow the agent is told to follow, or a template the agent is told to
fill counts as an instruction.

## 2. Domain class (one per skill)

| Class | Use when |
|---|---|
| `onchain` | The testing guidance is about code executed by the chain (contracts, proxies, deploy scripts). |
| `offchain_web3` | The guidance is about off-chain code that reads/writes chain state, signs transactions, manages keys or consumes ABI/events (dApp with wallet, SDK/RPC, indexers, oracles, bots, bridges). |
| `misto` | Substantial guidance for both on-chain and off-chain Web3 code. |
| `web2_incidental` | Blockchain is a peripheral mention; the guidance is about code that does not interact with a chain. |
| `indeterminado` | The text does not allow a decision. |

## 3. Context of each piece of evidence

The context is defined by **what the tested component does**, not by the repository it lives in.

| Context | Definition | Examples |
|---|---|---|
| `onchain` | Code executed by the blockchain | Smart contracts (Solidity, Vyper, Rust/Anchor, Move), proxies, deploy scripts |
| `offchain_web3` | Off-chain code that reads/writes state, signs transactions, manages keys or consumes ABI/events | dApp with wallet, SDK/RPC (ethers, viem), indexers, oracles, bots, bridges |
| `web2` | Code with no chain interaction, even inside a Web3 project | REST API, database, authentication, UI without wallet, generic CI |

Decision rule: (1) Is the code under test executed by the chain? → `onchain`. (2) Otherwise, does it
touch chain state, keys, signatures, ABI or events? → `offchain_web3`. (3) Otherwise → `web2`.

## 4. Layer checklist (Q1–Q9)

Answer `YES` or `NO` for each item. YES criteria paraphrase Vocke, *The Practical Test Pyramid*
(2018); the Web3 adaptation follows the Foundry, Hardhat and Anchor documentation.

| Item | YES when the text instructs… | In blockchain (on / off-chain) | Does not count |
|---|---|---|---|
| **Q1 Unit** | testing an isolated unit, with test doubles for its collaborators | a contract function with mocked dependencies / an SDK function with a stubbed RPC | "run the tests" |
| **Q2 Integration** | testing a real junction with an external part (DB, network, filesystem, another service) | contract ↔ contract on a local chain / backend ↔ RPC node, events | a fork without checking the junction |
| **Q3 Contract** | checking that consumer and provider respect a shared interface (consumer-driven contract tests) | a contract complies with an ABI/ERC; front-end and indexer check ABI and events | testing the smart contract itself (that is Q1/Q2) |
| **Q4 UI** | driving an interface: input → action → resulting state (GUI, REST, CLI) | calls via `cast`; dApp with wallet | XSS, injection (security, not UI testing) |
| **Q5 E2E** | testing the whole deployed system through its external interface | user → front-end → wallet → contract → indexer | the same quote already used for Q2 |
| **Q6 Acceptance** | testing a user scenario / business rule from the user's point of view (given/when/then) | a contract business rule; a dApp user journey | "all tests must pass" |
| **Q7 Exploratory** | explicit manual exploration to find problems not covered by automated tests | a session on testnet / in the dApp | informal wording ("check it works") |
| **Q8 Automation** | running tests with a named runner or in CI | `forge test`, `hardhat test` / `jest`, Playwright, a CI job | "verification commands" without a test runner |
| **Q9 Web3-specific** | fork testing, fuzzing, invariant/property tests, formal verification, gas testing | almost always on-chain | — |

For every YES give: **quote**, **justification**, **context** (§3).

## 5. Practice codebook (P1–P10)

List every testing practice the text **instructs**. Each practice gets a category, a polarity
(`good` / `bad`) fixed by the codebook (not by the annotator's opinion), a quote, a context and a
justification. Sources: Vocke (2018); test smells (Garousi & Küçük, JSS 2018); Foundry Book;
ConsenSys Smart Contract Best Practices; OWASP Smart Contract Top 10.

| Category | Good practice (example) | Bad practice (example) |
|---|---|---|
| **P1 Pyramid balance** | many unit tests, few E2E | only E2E, or only manual testing |
| **P2 Isolation** | mock the oracle and external contracts | a unit test that depends on a public RPC |
| **P3 Assertions** | assert the exact revert error, events, boundaries | only the happy path; a test without assertions |
| **P4 Determinism** | fork pinned to a block number; controlled time (`warp`, `roll`) | fork without a pinned block; unstable testnet |
| **P5 Adversarial** | fuzz/invariant tests, reentrancy, access-control tests | only fixed examples in value-bearing code |
| **P6 Automation & CI** | tests in CI blocking the merge | manual-only execution |
| **P7 Coverage** | coverage used as a signal | a coverage % as the goal |
| **P8 Integrity** | fix the code, not the test | skip, delete or loosen a failing test |
| **P9 Secrets** | local/test accounts; secrets kept out of the repo | a real private key in a test |
| **P10 Other** | emerging in calibration | emerging in calibration |

## 6. Evidence rules (humans and LLM)

1. Every YES and every practice needs a **literal quote of 5–40 words**, copied verbatim and
   contiguous from the text (no ellipses, no paraphrase, no reconstructed tables), plus a
   **one-sentence justification** linking the quote to the criterion or category.
2. Every piece of evidence gets a context: `onchain`, `offchain_web3` or `web2`.
3. Only what is **instructed** counts; polarity follows the codebook.
4. **One quote cannot justify two different items** (layers or practices).
5. When in doubt between YES and NO, answer NO and explain in the notes.

## 7. Output format

**LLM** — a single JSON object:

```json
{
  "domain_class": "onchain | offchain_web3 | misto | web2_incidental | indeterminado",
  "layers": {
    "Q1": {"answer": "YES | NO", "quote": "", "justification": "", "context": "onchain | offchain_web3 | web2 | null"},
    "...": {},
    "Q9": {"answer": "YES | NO", "quote": "", "justification": "", "context": null}
  },
  "practices": [
    {"category": "P1..P10", "polarity": "good | bad", "quote": "", "context": "onchain | offchain_web3 | web2", "justification": ""}
  ]
}
```

**Humans** — the same fields in the per-reviewer CSV sheets (`skills.csv`, `camadas.csv`,
`praticas.csv`); see `annotation/LEIA-ME_ANOTACAO.md`.

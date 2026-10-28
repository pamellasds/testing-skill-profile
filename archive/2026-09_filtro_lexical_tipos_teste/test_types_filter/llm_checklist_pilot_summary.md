# Piloto LLM checklist CTFL — resultados

Pipeline: Prompt A (checklist multi-label) → regras (skills_evidenced só com YES + quote verbatim).

| skill | hint | artifact | conf | verbatim_all_YES | skills_evidenced |
|---|---|---|---|---|---|
| `smart-contract-dev` | unit | test_guidance_skill | high | False | component, functional, performance, white_box, error_guessing, confirmation, contract_testing |
| `pentest-dapps` | integration | test_guidance_skill | high | False | system_integration, functional, non_functional, performance, security, reliability, compatibility, black_box, white_box, experience_based, state_transition_testing, error_guessing, checklist_based_testing, property_invariant_testing, load_testing, stress_testing, contract_testing |
| `flare-fcc` | system_e2e | not_test_related | high | True | — |
| `test-contracts` | fuzz_property | test_guidance_skill | high | True | component, component_integration, system, functional, non_functional, security, reliability, white_box, state_transition_testing, error_guessing, confirmation, regression, property_invariant_testing, contract_testing |
| `blockchain-engineer` | fork | test_guidance_skill | high | True | component, non_functional, security, white_box, state_transition_testing, confirmation, fuzz_testing, property_invariant_testing, fork_testing, contract_testing |
| `blockchain-cryptocurrency-blockchain-ecomunsing-blockchain` | regression | not_test_related | low | True | — |

## Notas

- `verification_ok=False` = algum YES ainda tem quote nao-literal; esses labels **nao** entram em `skills_evidenced` (filtro automatico).
- `flare-fcc` e o skill de regression do pool vieram como `not_test_related` neste piloto (conteudo truncado a 14k chars e/ou skill sem orientacao de teste dominante).
- Overclassification aparente em `pentest-dapps` (muitos labels) — candidato a revisao humana / ajuste de prompt.

### smart-contract-dev
- repo: `youugiuhiuh/web3-demos`
- issues: `['test_type.non_functional', 'test_type.non_functional_aspects.security', 'test_technique.state_transition_testing', 'test_technique.checklist_based_testing']`
- dropped_non_verbatim: `['test_type.non_functional', 'test_technique.state_transition_testing', 'test_technique.checklist_based_testing', 'test_type.non_functional_aspects.security']`
- skills: `{"test_level": ["component"], "test_type": ["functional"], "non_functional_aspects": ["performance"], "test_technique": ["white_box", "error_guessing"], "test_purpose": ["confirmation"], "test_strategy": [], "extensions": ["contract_testing"]}`

### pentest-dapps
- repo: `abelrguezr/hacktricks-skills`
- issues: `['test_level.component', 'test_level.component_integration', 'test_level.system', 'test_technique.exploratory_testing', 'test_purpose.confirmation']`
- dropped_non_verbatim: `['test_level.component', 'test_level.component_integration', 'test_level.system', 'test_technique.exploratory_testing', 'test_purpose.confirmation']`
- skills: `{"test_level": ["system_integration"], "test_type": ["functional", "non_functional"], "non_functional_aspects": ["performance", "security", "reliability", "compatibility"], "test_technique": ["black_box", "white_box", "experience_based", "state_transition_testing", "error_guessing", "checklist_based_testing"], "test_purpose": [], "test_strategy": [], "extensions": ["property_invariant_testing", "load_testing", "stress_testing", "contract_testing"]}`

### flare-fcc
- repo: `flare-foundation/flare-ai-skills`
- issues: `[]`
- dropped_non_verbatim: `[]`
- skills: `{"test_level": [], "test_type": [], "non_functional_aspects": [], "test_technique": [], "test_purpose": [], "test_strategy": [], "extensions": []}`

### test-contracts
- repo: `Lay3rLabs/wavs-aave-guardian`
- issues: `[]`
- dropped_non_verbatim: `[]`
- skills: `{"test_level": ["component", "component_integration", "system"], "test_type": ["functional", "non_functional"], "non_functional_aspects": ["security", "reliability"], "test_technique": ["white_box", "state_transition_testing", "error_guessing"], "test_purpose": ["confirmation", "regression"], "test_strategy": [], "extensions": ["property_invariant_testing", "contract_testing"]}`

### blockchain-engineer
- repo: `Matro81/ModernFlyouts-Enhance`
- issues: `[]`
- dropped_non_verbatim: `[]`
- skills: `{"test_level": ["component"], "test_type": ["non_functional"], "non_functional_aspects": ["security"], "test_technique": ["white_box", "state_transition_testing"], "test_purpose": ["confirmation"], "test_strategy": [], "extensions": ["fuzz_testing", "property_invariant_testing", "fork_testing", "contract_testing"]}`

### blockchain-cryptocurrency-blockchain-ecomunsing-blockchain
- repo: `linkxzhou/build-your-own-x-skills`
- issues: `[]`
- dropped_non_verbatim: `[]`
- skills: `{"test_level": [], "test_type": [], "non_functional_aspects": [], "test_technique": [], "test_purpose": [], "test_strategy": [], "extensions": []}`

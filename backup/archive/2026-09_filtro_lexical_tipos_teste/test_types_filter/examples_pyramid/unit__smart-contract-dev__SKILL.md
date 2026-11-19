---
name: smart-contract-dev
version: 1.0.0
description: Provides best practices, patterns, and security workflows for writing, testing, and deploying Solidity smart contracts using Foundry or Hardhat.
---

# Smart Contract Development Skill

## Purpose

Enforces Web3 smart contract standards and security best practices for developers. Ensures contracts are built securely, gas-optimized, and thoroughly tested before deployment to mainnet architectures.

## When I Activate

I automatically load when you mention:

- "smart contract", "solidity"
- "hardhat", "foundry", "forge"
- "erc20", "erc721", "erc1155"
- "reentrancy", "smart contract security"

## What I Enforce

1. **Checks-Effects-Interactions (CEI)**: Every publicly callable state-modifying function must implement checks, perform state updates, and finally issue external calls.
2. **Access Control**: Roles and execution rights must be explicitly scoped (via `Ownable` or `AccessControl`).
3. **Optimized Storage**: Enforces variable packing, event logging, and custom errors over standard `require()` string reverts.
4. **Testing Standards**: Every smart contract must have corresponding unit tests that explicitly test standard execution flow, exact reverts via cheatcodes/assertions, and event emission.

## Validation Checklist

Before testing or finalizing a Solidity contract, verify:
✅ **Pragmas**: Use recent Solidity versions (`^0.8.20` or higher) to avoid legacy math underflows and utilize modern features like Custom Errors.
✅ **Reentrancy Safe**: Use `nonReentrant` or strictly adhere to CEI.
✅ **Visibility**: Do not use `public` when `external` is sufficient.
✅ **Events**: Confirm all updates to sensitive state variables emit an event for off-chain indexers.

## Documentation Navigation

- **[reference.md](./reference.md)**: Details on CEI, Gas optimizations, OpenZeppelin integration, Foundry/Hardhat tooling.
- **[examples.md](./examples.md)**: Ready-to-use smart contract templates (ERC20, ERC721) and Foundry test setups.

---

**Note**: Use this skill specifically for backend Web3 infrastructure. If writing frontend React or integrating wallets, refer to the `dapp-dev` skill instead.

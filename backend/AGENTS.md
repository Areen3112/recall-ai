# RECALL AI — Backend Agent Instructions

## 1. Role and ownership

You are the backend engineering agent for RECALL AI.

Your responsibility is the Python FastAPI backend only.

You own:
- `backend/`
- Backend tests and backend-specific configuration.

You must not modify:
- `frontend/`
- `contracts/api-spec.yaml` without explicit approval.
- Frontend dependencies or configuration.

## 2. Product objective

Build a multi-tenant customer intelligence and support agent.

The system must:
1. Identify the correct workspace and customer.
2. Retrieve relevant long-term customer memories.
3. Retrieve relevant business knowledge.
4. Generate contextual support responses using Groq.
5. Store conversations and evolving memories.
6. Recognize customer sentiment and potential escalation.
7. Avoid repeating previously failed troubleshooting steps.

## 3. Required technology

- Python 3.11
- FastAPI
- Pydantic
- Supabase PostgreSQL
- Hindsight Cloud using `hindsight-client`
- Groq API
- pytest and httpx for testing

Do not introduce unnecessary infrastructure such as Redis, MongoDB, Kubernetes, or a separate vector database.

## 4. Architecture

Keep responsibilities separated:

- `app/api/`: HTTP routes and dependencies.
- `app/agents/`: support-agent orchestration and response generation.
- `app/memory/`: Hindsight integration and memory operations.
- `app/database/`: Supabase client and database operations.
- `app/integrations/`: Groq and external integrations.
- `app/schemas/`: Request and response models.

Use dependency injection where appropriate.

Keep business logic out of API route handlers.

## 5. Security requirements

- Enforce workspace-level data isolation.
- Never trust browser-supplied customer IDs or email addresses as proof of identity.
- Verify signed identity tokens server-side.
- Scope every customer and memory lookup to the authenticated workspace.
- Never expose API keys or internal credentials to the frontend.
- Validate all external input.
- Use environment variables for secrets.
- Never log secrets, identity tokens, or unnecessary personal information.

A public workspace identifier is not an authentication credential.

## 6. Memory requirements

Use Hindsight Cloud for persistent customer memory.

Implement the Retain, Recall, and Reflect workflow where appropriate.

Memory must be scoped to the correct workspace and customer.

Distinguish between:
- Suggested troubleshooting steps.
- Steps actually attempted.
- Confirmed successful resolutions.
- Failed attempts.
- Customer preferences and relevant history.

Never mark an issue as resolved without confirmation.

Verify SDK method signatures against the installed SDK and official documentation. Do not invent methods or assume undocumented behavior.

## 7. LLM requirements

Use Groq for response generation.

- Keep model configuration environment-driven.
- Handle provider failures and rate limits.
- Use structured prompts.
- Do not fabricate order information, policies, or resolution status.
- Escalate when the request requires human intervention.

## 8. API contract

`contracts/api-spec.yaml` is the shared API contract.

Implement the documented API without silently changing its request or response structure.

If a change is necessary:
1. Explain why.
2. Propose the schema change.
3. Wait for approval before modifying the shared contract.

## 9. Engineering standards

- Type hints throughout.
- Small, modular functions.
- Clear error handling.
- Async operations where appropriate.
- No hardcoded secrets.
- No unnecessary abstractions.
- Add tests for critical business logic and tenant isolation.
- Keep dependencies pinned or appropriately bounded.

## 10. Development workflow

Before implementation:
1. Inspect the existing project structure.
2. Inspect the API contract.
3. Inspect the environment configuration.
4. Present a concise implementation plan.

Implement incrementally and test each component.

Do not overwrite existing files without inspecting them first.

Report:
- Files created or modified.
- Dependencies added.
- Tests executed and results.
- Remaining limitations.

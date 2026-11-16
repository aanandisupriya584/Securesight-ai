# OpenAI AI provider

SecureSight exposes the provider behind `POST /api/ai/analyze`; the API key stays in the backend environment. The common `AIProvider` interface keeps HTTP/provider details outside the route. The current adapter uses OpenAI's Responses API.

## Local configuration

The project `.env` accepts:

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=your-server-side-API-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-6-luna
AI_TIMEOUT_SECONDS=20
AI_MAX_OUTPUT_TOKENS=400
AI_MAX_REQUESTS_PER_HOUR=30
```

Create an API key in the [OpenAI API dashboard](https://platform.openai.com/api-keys) and put it in the ignored `.env` file on the API host. Do not paste it into chat, React environment variables, source control, screenshots, or user prompts. `gpt-6-luna` is the initial cost-focused default; model access and billing depend on the OpenAI API account. See the current [model catalog](https://developers.openai.com/api/docs/models) and [pricing](https://developers.openai.com/api/docs/pricing).

Restart the stack after adding the key:

```sh
docker compose up --build -d
```

Then open the AI Analyst page and ask a question using synthetic or approved, minimized data. If no key is configured, the endpoint returns a clear `503`; it does not fabricate an AI response.

## Guardrails

- 20-second default timeout, capped at 60 seconds; transient network/server errors retry at most twice.
- Maximum 4000-character prompt, configurable output-token ceiling, and per-organization request cap.
- Credential-like values are rejected; email addresses are redacted before sending.
- The agent can call three fixed, read-only tools: incident search, security event search, and asset listing. Every query is scoped to the authenticated organization; the model cannot supply or override the organization ID.
- Tool output is limited to eight records per call, omits asset identifiers, and redacts credential patterns and email addresses before it is sent to OpenAI. The UI identifies the source categories used.
- Tool arguments are validated server-side. The agent has no shell, arbitrary SQL, scanning, write, or response-action tools, and is limited to three tool lookups before a final response without tools.
- The model is instructed to treat workspace records as untrusted data, distinguish evidence from hypotheses, and cite record IDs. Human review is required before any remediation.
- The current request cap is held in process memory for the single-process development service. Replace it with a shared Redis-backed quota before horizontal scaling.

These filters reduce accidental disclosure but cannot guarantee detection of every sensitive value. Send only synthetic or approved, minimized data.

The implementation follows the Responses API function-calling cycle: accept a model function call, run the allowlisted application function, return its output with the call ID, and request a final response. See the [official OpenAI function calling documentation](https://developers.openai.com/api/docs/guides/function-calling).

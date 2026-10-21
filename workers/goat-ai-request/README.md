# Automatic GOAT Gemini requests

This small Cloudflare Worker accepts a selection from the production GOAT page and dispatches the existing, secret-backed GitHub Actions workflow. The Gemini key remains a GitHub Actions secret and is never sent to the browser or this Worker.

The Worker accepts requests only from `https://espierin.github.io`, validates the driver IDs, periods and supplied prompt hash, and only dispatches the workflow on a cache miss. A SQLite Durable Object serializes requests and enforces a maximum of four new comparisons per UTC day, two per originating IP per day, and two attempts per prompt hash. IP addresses are hashed with the Worker secret before the hash is stored. No request body or IP address is logged by the Worker.

## One-time setup

1. Sign in with `npx wrangler login` from this folder.
2. Create a GitHub fine-grained token for `espierin/overtakeitaway` only, with **Actions: Read and write**. The workflow itself continues to use its existing GitHub Actions token and `GEMINI_API_KEY` secret.
3. Add the token as a Worker secret with `npx wrangler secret put GITHUB_ACTIONS_TOKEN`.
4. Add a random salt with `npx wrangler secret put RATE_LIMIT_SALT`.
5. Deploy with `npx wrangler deploy`. The command prints the Worker URL.
6. Put that URL in `assets/goat-ai-config.js` as `window.goatAIConfig.endpoint`, then rebuild and publish the GOAT page.

The daily limits are in `wrangler.toml`; keep them low because every new uncached comparison uses Gemini. The Worker can be deployed on Cloudflare's free Workers plan within its current account limits; account terms and usage limits are set by Cloudflare.

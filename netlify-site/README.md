# Netlify frontend

The root `netlify.toml` sets this folder as Netlify's base directory. This keeps `requirements.txt` out of Netlify's automatic dependency installation: Netlify builds only the static frontend, while the FastAPI backend runs on a separate HTTPS host.

Set `MAMBOT_API_ORIGIN` in the Netlify site's build environment to the backend's bare HTTPS origin, such as `https://api.example.com`. The build fails if this is missing, rather than publishing a chat UI with broken API calls. The generated `/mambot/api/*` rewrite keeps requests same-origin in the browser. Keep the backend running and verify `/mambot/api/health` and an actual chat request through the Netlify domain before making the site public.

The source repository's Python server is not a Netlify Function. Publishing `static/` alone leaves chat and library unavailable. Do not put OpenRouter or MongoDB credentials in the frontend or this build directory.


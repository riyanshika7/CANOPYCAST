# Deploying the backend

Written for whoever runs the deploy. Everything here was checked against a real
container, not read off the docs.

## What the service needs

| Variable | Required | Notes |
|---|---|---|
| `OPENAI_API_KEY` | yes, for chat | Without it the grid and optimizer still work and chat answers 503 |
| `PORT` | set by the platform | Already honoured, do not hardcode 8000 |
| `CANOPYCAST_MAX_CALLS` | no | Default 500 OpenAI calls per process |
| `CANOPYCAST_MAX_TOKENS` | no | Default 2,000,000 |
| `CANOPYCAST_AUTO_INGEST` | no | Default on, set to `0` to disable the boot-time index build |

Nothing else. The grid database seeds itself on first boot.

## Render, Docker, free tier

1. New Web Service, connect the repo, root directory `backend`, runtime Docker.
2. Set `OPENAI_API_KEY`.
3. Deploy.

That is the whole thing. There is no shell step, which matters: the free tier
gives you no shell, so `python -m app.ingest` is not something you can run
against the deployed container. The service builds the index itself on first
boot when the corpus is empty and a key is present.

Measured on a container started with no index and nothing mounted: healthy
immediately, `corpus_ready` false for about 18 seconds, then true, and chat
answered correctly from the corpus straight after. Roughly 800 embedding calls,
once.

Watch the first boot log for `index built with N chunks`. If you see
`index build failed`, the rest of the app is still up and only chat is down.

## Free tier, the parts that will bite

The disk is not persistent. A restart loses the index and the service rebuilds
it on the next boot, which costs another 800 embedding calls. The budget ceiling
caps the damage, but attach a persistent disk at
`/home/appuser/app/chroma_db` if the plan allows one, and the rebuild stops
happening.

Free instances sleep after inactivity and take roughly a minute to wake. Hit the
URL a few minutes before any demo. A judge clicking a sleeping service sees a
timeout, and the frontend cannot tell that apart from a broken backend.

## Verifying a deploy

```bash
BASE=https://your-service.onrender.com
curl -s $BASE/api/health
curl -s "$BASE/api/city-grid?city=Kolkata" | head -c 200
curl -s "$BASE/api/cell-stats?city=Kolkata&lat=22.5726&lon=88.3639"
curl -s -X POST $BASE/api/optimize -H 'content-type: application/json' -d '{"city":"Kolkata","top_n":5}'
curl -s "$BASE/api/recommend-trees?city=Kolkata&cell_id=8_13&n=3"
curl -s -X POST $BASE/api/chat -H 'content-type: application/json' -d '{"message":"Should we plant Gulmohar here?","city":"Kolkata"}'
```

`/api/health` reporting `"corpus_ready": true` and `"chat_ready": true` is the
signal that the last two will work. Until then they answer 503 with the reason
in the body.

## The frontend still points at a laptop

`frontend/src/components/Chatbot.jsx` calls `http://127.0.0.1:8000/api/chat`.
A deployed backend changes nothing until that URL does, and the component falls
back to canned text on any failure, so it will look like it works while
answering from a hardcoded string.

That file belongs to the frontend pair, not this deploy. Flagging it because
deploying the backend and leaving that line alone produces a demo that appears
fine and is not.

## Docker, by hand

```bash
docker build -t canopycast-api .
docker run -p 8000:8000 -e OPENAI_API_KEY=... canopycast-api
```

Add `-v chroma_data:/home/appuser/app/chroma_db` to keep the index across
restarts. That path, not `/app/chroma_db`. Mounting the wrong one fails quietly:
the container starts, reports healthy, and rebuilds the index every boot.

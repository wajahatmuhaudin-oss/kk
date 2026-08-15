# JARVIS — AI Voice Assistant (Claude / ChatGPT)

A hacker-terminal styled voice assistant that talks to **either Claude or
ChatGPT** — real AI, not fixed commands. Works on desktop and mobile
browsers (Chrome/Edge recommended for voice input).

## How it works

```
Your voice/text  →  index.html (browser)  →  app.py (your own backend)  →  Claude or OpenAI API
                                                    ↑
                                     your API key travels only this path
```

Your API key is typed once into the **Settings (⚙)** panel, saved in your
browser's local storage, and sent only to the `app.py` server *you* run.
`app.py` forwards it to Anthropic or OpenAI and relays the reply back. The
key is never written into any file and never shared with a third party.

## 1. Get an API key

Pick one (or both):

- **Claude**: sign up at [console.anthropic.com](https://console.anthropic.com), create an API key under "API Keys". New accounts usually get some free credit.
- **ChatGPT**: sign up at [platform.openai.com](https://platform.openai.com/api-keys), create a key there. You'll need to add billing (a few dollars is enough for a lot of use).

Keep the key private — anyone with it can spend your credits.

## 2. Run the backend

```bash
cd jarvis-ai
pip install -r requirements.txt
python app.py
```

This starts a server at `http://localhost:5000` and also serves the page
itself, so you can just open that URL in your browser.

## 3. Open it and configure

Visit `http://localhost:5000` (desktop) — a Settings panel will pop up
automatically the first time. Paste your Claude and/or OpenAI key, hit
**Save Configuration**. Pick which provider to use from the dropdown at the
top (CLAUDE / CHATGPT) any time.

## 4. Using it on your phone too

`localhost` only works on the same computer. To use JARVIS from your phone:

**Option A — same WiFi network (quick, free):**
1. Find your computer's local IP (e.g. `192.168.1.5`) — on Windows run `ipconfig`, on Mac/Linux run `ifconfig` or `ip addr`.
2. Run the backend with `python app.py` (it already listens on `0.0.0.0`, so this works).
3. On your phone (same WiFi), open `http://192.168.1.5:5000` in Chrome.
4. In Settings, set **Backend URL** to that same address, e.g. `http://192.168.1.5:5000`.

**Option B — access from anywhere (needs free hosting):**
Deploy `app.py` to a free Python host like [Render](https://render.com) or
[Railway](https://railway.app) (Netlify does *not* run Python backends —
it's static-only). Once deployed you'll get a permanent HTTPS URL; open
that on any device and set it as the Backend URL in Settings.

## Voice input notes

- Voice recognition (Web Speech API) needs **Chrome or Edge**, and needs to
  be loaded over **HTTPS** or `localhost` — not a `file://` path.
- **Safari/iOS doesn't support it** — use the text box under the orb
  instead; text works everywhere.
- Voice *output* (text-to-speech) works in all modern browsers.

## Files

```
jarvis-ai/
├── index.html       → UI: hacker terminal look, orb mic control, settings modal
├── app.py            → Flask backend, proxies to Claude/OpenAI using your key
├── requirements.txt   → Python dependencies
└── README.md
```

## Cost

This app itself is free — you only pay your AI provider for what you
actually ask it (typically fractions of a cent per short exchange on
Claude Haiku/GPT-4o-mini class models; this app uses `claude-sonnet-4-6`
and `gpt-4o-mini` by default — edit the model names in `app.py` if you want
a cheaper or more powerful model).

## Security notes

- Never commit your API keys to a public GitHub repo.
- If you deploy the backend publicly, anyone who can reach it and knows
  your key could use your credits — this demo trusts whoever holds the
  browser's saved key. For a shared/public deployment, add your own
  authentication in front of `/api/chat`.

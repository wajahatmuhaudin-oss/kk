"""
JARVIS backend — AI proxy server
=================================
This server does NOT store any API keys. The browser sends the user's own
OpenAI and/or Anthropic key with each request (kept in the browser's
localStorage), and this server simply forwards the request to the right
provider and returns the reply. This keeps keys out of any committed code
and off any third-party server other than the one the user runs themselves.

Run locally:
    pip install flask flask-cors requests
    python app.py

Then open index.html (served by this same app at http://localhost:5000)
and paste your API key(s) into the Settings panel.
"""

import os
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)  # Restrict origins in production if you deploy this publicly.

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are JARVIS, a concise, helpful voice assistant. Keep answers short "
    "and conversational since they will be read aloud by text-to-speech — "
    "prefer 1-3 sentences unless the user asks for detail. No markdown, "
    "no bullet points, no headers, just plain spoken-style text."
)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Expects JSON body:
    {
        "provider": "anthropic" | "openai",
        "api_key": "<user's own key, sent from the browser>",
        "message": "user's spoken/typed message",
        "history": [{"role": "user"|"assistant", "content": "..."}, ...]  (optional)
    }
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Request body must be JSON"}), 400

    provider = payload.get("provider")
    api_key = payload.get("api_key", "").strip()
    message = payload.get("message", "").strip()
    history = payload.get("history", [])

    if provider not in ("anthropic", "openai"):
        return jsonify({"error": "provider must be 'anthropic' or 'openai'"}), 400
    if not api_key:
        return jsonify({"error": "Missing api_key. Add your key in Settings."}), 400
    if not message:
        return jsonify({"error": "Missing message"}), 400

    try:
        if provider == "anthropic":
            reply = _call_anthropic(api_key, message, history)
        else:
            reply = _call_openai(api_key, message, history)
        return jsonify({"reply": reply})
    except AuthError as e:
        return jsonify({"error": str(e)}), 401
    except UpstreamError as e:
        return jsonify({"error": str(e)}), 502


class AuthError(Exception):
    pass


class UpstreamError(Exception):
    pass


def _call_anthropic(api_key, message, history):
    messages = []
    for turn in history[-10:]:  # keep last 10 turns of context
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 400,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        },
        timeout=30,
    )

    if resp.status_code == 401:
        raise AuthError("Invalid Anthropic API key.")
    if resp.status_code != 200:
        raise UpstreamError(f"Anthropic API error ({resp.status_code}): {resp.text[:200]}")

    data = resp.json()
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return "".join(parts).strip() or "I didn't get a text reply from Claude."


def _call_openai(api_key, message, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-10:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    resp = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "max_tokens": 400,
            "messages": messages,
        },
        timeout=30,
    )

    if resp.status_code == 401:
        raise AuthError("Invalid OpenAI API key.")
    if resp.status_code != 200:
        raise UpstreamError(f"OpenAI API error ({resp.status_code}): {resp.text[:200]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        return "I didn't get a text reply from ChatGPT."
    return choices[0].get("message", {}).get("content", "").strip()


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

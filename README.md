# Maneuver — Talk to Founder Voice AI

## How to run locally

### Agent (backend)
cd agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python agent.py dev

### Frontend
cd agent-starter-react
pnpm install
pnpm dev

Open http://localhost:3000

## Environment variables

### agent/.env
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
GROQ_API_KEY=...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...

### agent-starter-react/.env.local
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

## Models used and why
- STT: Deepgram nova-2 — lowest latency, best accuracy for conversational speech
- LLM: Groq llama-3.3-70b-versatile — extremely fast inference, free tier, great instruction following
- TTS: Cartesia — natural voice, low latency, free tier available
- Voice infra: LiveKit — required by assignment, handles WebRTC and data channels

## What I'd build next
- Multi-agent handoff: discovery agent hands off to scheduling agent when user is ready to book
- Follow-up email triggered at end of call with captured lead data
- Admin dashboard showing all past calls and captured leads
- Smarter visual triggers — show case studies when user asks about results
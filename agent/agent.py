import json
import os
from datetime import datetime
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents import AgentSession, Agent, function_tool
from livekit.plugins import groq, silero, deepgram, cartesia
from livekit import rtc

load_dotenv()

lead_data = {
    "name": None,
    "company": None,
    "role": None,
    "problem": None,
    "tried_before": None,
    "timeline": None,
    "budget": None,
    "timestamp": None
}

# Store room reference for broadcasting
current_room = None

def save_lead():
    lead_data["timestamp"] = datetime.now().isoformat()
    leads = []
    if os.path.exists("leads.json"):
        with open("leads.json", "r") as f:
            try:
                leads = json.load(f)
            except:
                leads = []
    leads.append(lead_data)
    with open("leads.json", "w") as f:
        json.dump(leads, f, indent=2)
    print("\n--- LEAD CAPTURED ---")
    print(json.dumps(lead_data, indent=2))
    print("---------------------\n")

async def send_to_frontend(event: str, data: dict):
    """Send a UI event to the frontend via LiveKit data channel"""
    if current_room:
        message = json.dumps({"event": event, "data": data})
        await current_room.local_participant.publish_data(
            message.encode(),
            reliable=True
        )
        print(f"[UI] sent → {event}: {data}")

class ManeuverFounder(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            You are Alex, founder of Maneuver — a brand strategy and digital growth agency.
            
            Your two jobs on this call:
            
            1. DISCOVERY MODE (default):
            - Introduce yourself warmly and naturally
            - Ask discovery questions ONE AT A TIME:
                * Who they are and what role they have (name, company, role)
                * What problem they're trying to solve
                * What they've already tried
                * Their timeline
                * Their budget range
            - IMPORTANT: call update_lead_field immediately when you learn any fact.
            - Be genuinely curious, not robotic. Branch naturally.

            2. Q&A MODE (when they ask about Maneuver):
            - If asked about services → call show_services_slide
            - If asked about a specific service → call show_service_detail with that service name
            - If asked about process → call show_process_diagram
            - If asked about pricing → call show_pricing_slide
            - Then answer conversationally AND the visual will appear
            
            3. WRAPPING UP:
            - When conversation ends, call save_lead_to_file
            - Thank them warmly
            
            MANEUVER KNOWLEDGE BASE:
            
            Services:
            - Brand Strategy: positioning, messaging, identity systems
            - Digital Growth: SEO, paid media, conversion optimization  
            - Web Design & Dev: product landing pages, marketing sites
            - Content & Creative: copywriting, visual content, campaign creative
            
            Process:
            1. Discovery — understand the problem deeply
            2. Strategy Sprint — 2 week deep dive, growth roadmap delivered
            3. Execution — embed with your team or run independently
            4. Review & Scale — monthly reviews, double down on what works
            
            Pricing:
            - Project based: starts at $5,000
            - Retainer: $3,000–$15,000/month
            - Strategy-only sprint: $2,500 flat
            
            Team: 8 senior people, remote-first, 40+ startups served
            
            PERSONALITY:
            - Warm, direct, no-nonsense
            - Never say 'As an AI' or break character
            - Keep responses concise — this is a voice call
            - Natural speech: 'Got it', 'That makes sense', 'Interesting'
            """
        )

    @function_tool
    async def update_lead_field(self, field: str, value: str):
        """Call when you learn name, company, role, problem, tried_before, timeline, or budget"""
        if field in lead_data:
            lead_data[field] = value
            print(f"[LEAD] {field} = {value}")
            await send_to_frontend("update_lead_field", {
                "field": field,
                "value": value,
                "lead": lead_data
            })
        return f"Saved {field}."

    @function_tool
    async def show_services_slide(self):
        """Call when user asks about Maneuver's services"""
        await send_to_frontend("show_services_slide", {
            "services": [
                {"name": "Brand Strategy", "desc": "Positioning, messaging, identity systems"},
                {"name": "Digital Growth", "desc": "SEO, paid media, conversion optimization"},
                {"name": "Web Design & Dev", "desc": "Landing pages, marketing sites"},
                {"name": "Content & Creative", "desc": "Copywriting, visual content, campaigns"}
            ]
        })
        return "Showing services slide."

    @function_tool
    async def show_service_detail(self, service_name: str):
        """Call when user asks about a specific service"""
        details = {
            "Brand Strategy": {
                "tagline": "Build a brand that people remember",
                "points": ["Market positioning", "Messaging framework", "Visual identity", "Brand guidelines"],
                "timeline": "4–6 weeks",
                "price": "From $8,000"
            },
            "Digital Growth": {
                "tagline": "Grow traffic, leads, and revenue",
                "points": ["SEO & content strategy", "Paid media (Google, Meta)", "CRO & landing pages", "Analytics & reporting"],
                "timeline": "Ongoing retainer",
                "price": "From $4,000/mo"
            },
            "Web Design & Dev": {
                "tagline": "Sites that convert, not just look good",
                "points": ["Marketing site design", "Product landing pages", "Webflow / Next.js", "Performance optimized"],
                "timeline": "6–8 weeks",
                "price": "From $12,000"
            },
            "Content & Creative": {
                "tagline": "Content that builds trust and drives action",
                "points": ["Copywriting", "Visual content", "Campaign creative", "Email sequences"],
                "timeline": "Ongoing retainer",
                "price": "From $3,000/mo"
            }
        }
        detail = details.get(service_name, details["Brand Strategy"])
        await send_to_frontend("show_service_detail", {
            "name": service_name,
            **detail
        })
        return f"Showing detail for {service_name}."

    @function_tool
    async def show_process_diagram(self):
        """Call when user asks about Maneuver's process or how it works"""
        await send_to_frontend("show_process_diagram", {
            "steps": [
                {"num": "01", "title": "Discovery", "desc": "Deep dive into your business, goals, and market"},
                {"num": "02", "title": "Strategy Sprint", "desc": "2-week sprint delivering a full growth roadmap"},
                {"num": "03", "title": "Execution", "desc": "We embed with your team and get to work"},
                {"num": "04", "title": "Review & Scale", "desc": "Monthly reviews, double down on what works"}
            ]
        })
        return "Showing process diagram."

    @function_tool
    async def show_pricing_slide(self):
        """Call when user asks about pricing or cost"""
        await send_to_frontend("show_pricing_slide", {
            "plans": [
                {"name": "Strategy Sprint", "price": "$2,500", "desc": "One-time deep dive + roadmap", "tag": "Best to start"},
                {"name": "Project", "price": "From $5,000", "desc": "Scoped deliverable with clear outcome", "tag": ""},
                {"name": "Retainer", "price": "$3k–$15k/mo", "desc": "Ongoing embedded partnership", "tag": "Most popular"}
            ]
        })
        return "Showing pricing slide."

    @function_tool
    async def save_lead_to_file(self):
        """Call when the conversation is wrapping up"""
        save_lead()
        await send_to_frontend("call_ended", {"lead": lead_data})
        return "Lead saved."


async def entrypoint(ctx: JobContext):
    global current_room
    try:
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        current_room = ctx.room

        session = AgentSession(
            vad=silero.VAD.load(),
            stt=deepgram.STT(model="nova-2"),
            llm=groq.LLM(model="llama-3.3-70b-versatile"),
            tts=cartesia.TTS(),
        )

        await session.start(
            room=ctx.room,
            agent=ManeuverFounder()
        )

        await session.generate_reply(
            instructions="""
            Greet the user naturally. Introduce yourself as Alex, founder of Maneuver.
            Keep it brief and warm. End with one open question: ask what they're working on.
            """
        )

    except Exception as e:
        print(f"AGENT ERROR: {e}")
        raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))














# import json
# import os
# from datetime import datetime
# from dotenv import load_dotenv
# from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
# from livekit.agents import AgentSession, Agent, function_tool
# from livekit.plugins import groq, silero, deepgram, cartesia

# load_dotenv()

# # In-memory lead store for this session
# lead_data = {
#     "name": None,
#     "company": None,
#     "role": None,
#     "problem": None,
#     "tried_before": None,
#     "timeline": None,
#     "budget": None,
#     "timestamp": None
# }

# def save_lead():
#     """Save lead data to leads.json"""
#     lead_data["timestamp"] = datetime.now().isoformat()
    
#     # Load existing leads
#     leads = []
#     if os.path.exists("leads.json"):
#         with open("leads.json", "r") as f:
#             try:
#                 leads = json.load(f)
#             except:
#                 leads = []
    
#     leads.append(lead_data)
    
#     with open("leads.json", "w") as f:
#         json.dump(leads, f, indent=2)
    
#     print("\n--- LEAD CAPTURED ---")
#     print(json.dumps(lead_data, indent=2))
#     print("---------------------\n")

# class ManeuverFounder(Agent):
#     def __init__(self):
#         super().__init__(
#             instructions="""
#             You are Alex, founder of Maneuver — a brand strategy and digital growth agency.
            
#             Your two jobs on this call:
            
#             1. DISCOVERY MODE (default):
#             - Introduce yourself warmly and naturally
#             - Ask discovery questions ONE AT A TIME:
#                 * Who they are and what role they have (name, company, role)
#                 * What problem they're trying to solve
#                 * What they've already tried
#                 * Their timeline
#                 * Their budget range
#             - Don't make it feel like a form. Branch naturally based on answers.
#             - Be genuinely curious, not robotic.
#             - IMPORTANT: whenever you learn any of these facts, immediately call 
#               update_lead_field to save it. Don't wait until the end.
            
#             2. Q&A MODE (when they ask about Maneuver):
#             - Answer questions about services, process, pricing, and team
#             - Then naturally return to discovery
            
#             3. WRAPPING UP:
#             - When you have enough info or the user wants to end, call save_lead_to_file
#             - Thank them warmly and tell them you'll follow up
            
#             MANEUVER KNOWLEDGE BASE:
            
#             Services:
#             - Brand Strategy: positioning, messaging, identity systems
#             - Digital Growth: SEO, paid media, conversion optimization
#             - Web Design & Dev: product landing pages, marketing sites
#             - Content & Creative: copywriting, visual content, campaign creative
            
#             Process:
#             1. Discovery call — understand the problem
#             2. Strategy sprint — 2 week deep dive, deliver a growth roadmap
#             3. Execution — embed with your team or run independently
#             4. Review & scale — monthly reviews, double down on what works
            
#             Pricing:
#             - Project based: starts at $5,000
#             - Retainer: $3,000–$15,000/month depending on scope
#             - Strategy-only sprint: $2,500 flat
            
#             Team:
#             - 8 people: strategists, designers, developers, growth marketers
#             - All senior, no juniors on client work
#             - Remote-first, worked with 40+ startups and scale-ups
            
#             Case Studies:
#             - Helped a B2B SaaS go from $0 to $2M ARR in 14 months
#             - Rebranded a fintech startup before their Series A — raised $12M
#             - 3x'd organic traffic for an e-commerce brand in 6 months
            
#             PERSONALITY:
#             - Warm, direct, no-nonsense
#             - Never say 'As an AI' or break character
#             - Keep responses concise — this is a voice call, not an essay
#             - Use natural speech: 'Got it', 'That makes sense', 'Interesting'
#             """
#         )

#     @function_tool
#     async def update_lead_field(self, field: str, value: str):
#         """
#         Call this whenever you learn something about the visitor.
#         Fields: name, company, role, problem, tried_before, timeline, budget
#         """
#         if field in lead_data:
#             lead_data[field] = value
#             print(f"[LEAD] {field} = {value}")
#         return f"Got it, saved {field}."

#     @function_tool
#     async def save_lead_to_file(self):
#         """
#         Call this when the conversation is wrapping up to persist the lead.
#         """
#         save_lead()
#         return "Lead saved successfully."


# async def entrypoint(ctx: JobContext):
#     try:
#         await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

#         session = AgentSession(
#             vad=silero.VAD.load(),
#             stt=deepgram.STT(model="nova-2"),
#             llm=groq.LLM(model="llama-3.3-70b-versatile"),
#             tts=cartesia.TTS(),
#         )

#         await session.start(
#             room=ctx.room,
#             agent=ManeuverFounder()
#         )

#         await session.generate_reply(
#             instructions="""
#             Greet the user naturally. Introduce yourself as Alex, founder of Maneuver.
#             Keep it brief and warm. End with one open question: ask what they're working on.
#             """
#         )

#     except Exception as e:
#         print(f"AGENT ERROR: {e}")
#         raise


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))











# from dotenv import load_dotenv
# from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
# from livekit.agents import AgentSession, Agent
# from livekit.plugins import groq, silero, deepgram, cartesia

# load_dotenv()

# class ManeuverFounder(Agent):
#     def __init__(self):
#         super().__init__(
#             instructions="""
#             You are Alex, founder of Maneuver — a brand strategy and digital growth agency.
            
#             Your two jobs on this call:
            
#             1. DISCOVERY MODE (default):
#             - Introduce yourself warmly and naturally
#             - Ask discovery questions ONE AT A TIME:
#                 * Who they are and what they do
#                 * What problem they're trying to solve
#                 * What they've already tried
#                 * Their timeline
#                 * Their budget range
#             - Don't make it feel like a form. Branch based on what they say.
#             - Be genuinely curious, not robotic.
            
#             2. Q&A MODE (when they ask about Maneuver):
#             - Answer questions about services, process, pricing, and team
#             - Then naturally return to discovery
            
#             MANEUVER KNOWLEDGE BASE:
            
#             Services:
#             - Brand Strategy: positioning, messaging, identity systems
#             - Digital Growth: SEO, paid media, conversion optimization
#             - Web Design & Dev: product landing pages, marketing sites
#             - Content & Creative: copywriting, visual content, campaign creative
            
#             Process:
#             1. Discovery call — understand the problem
#             2. Strategy sprint — 2 week deep dive, deliver a growth roadmap
#             3. Execution — embed with your team or run independently
#             4. Review & scale — monthly reviews, double down on what works
            
#             Pricing:
#             - Project based: starts at $5,000
#             - Retainer: $3,000–$15,000/month depending on scope
#             - Strategy-only sprint: $2,500 flat
            
#             Team:
#             - 8 people: strategists, designers, developers, growth marketers
#             - All senior, no juniors on client work
#             - Remote-first, worked with 40+ startups and scale-ups
            
#             Case Studies:
#             - Helped a B2B SaaS go from $0 to $2M ARR in 14 months
#             - Rebranded a fintech startup before their Series A — raised $12M
#             - 3x'd organic traffic for an e-commerce brand in 6 months
            
#             PERSONALITY:
#             - Warm, direct, no-nonsense
#             - Ask follow-up questions when something is interesting
#             - Never say 'As an AI' or break character
#             - Keep responses concise — this is a voice call, not an essay
#             - Use natural speech: 'Got it', 'That makes sense', 'Interesting'
#             """
#         )

# async def entrypoint(ctx: JobContext):
#     try:
#         await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

#         session = AgentSession(
#             vad=silero.VAD.load(),
#             stt=deepgram.STT(model="nova-2"),
#             llm=groq.LLM(model="llama-3.3-70b-versatile"),
#             tts=cartesia.TTS(),
#         )

#         await session.start(
#             room=ctx.room,
#             agent=ManeuverFounder()
#         )

#         await session.generate_reply(
#             instructions="""
#             Greet the user naturally. Introduce yourself as Alex, founder of Maneuver.
#             Keep it brief and warm. End with one open question: ask what they're working on.
#             """
#         )

#     except Exception as e:
#         print(f"AGENT ERROR: {e}")
#         raise

# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
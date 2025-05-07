import os
import json
import time
import base64
from io import BytesIO
from typing import Dict, Any
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from gtts import gTTS

# Load environment variables
load_dotenv()

# Load GROQ_API_KEY from environment securely
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not set in environment variables")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)
# List of supported models with priority order for automatic switching
SUPPORTED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-guard-3-8b",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it"
]

# Start with the first model in the list
current_model_index = 0

MODEL = SUPPORTED_MODELS[current_model_index]  # Using Llama 3.3 70B for best tool use support

# Bot data for simulating responses
conversion_rates = {
    "beans": {
        "diamonds": 2,
        "usd": 0.05
    },
    "diamonds": {
        "beans": 0.5,
        "usd": 0.025
    },
    "usd": {
        "beans": 20,
        "diamonds": 40
    }
}

tiers = [
    {"name": "Rookie", "beans": 0, "hours": 0},
    {"name": "Explorer", "beans": 5000, "hours": 60},
    {"name": "Rising Star", "beans": 15000, "hours": 80},
    {"name": "Talent", "beans": 30000, "hours": 100},
    {"name": "Professional", "beans": 60000, "hours": 120},
    {"name": "Elite", "beans": 100000, "hours": 150},
    {"name": "Champion", "beans": 200000, "hours": 180}
]

events = [
    {"name": "Summer Bash", "type": "Contest", "entry_fee": 500, "participants": "12/20", "duration": "5 days", "prize": "10,000 beans"},
    {"name": "Talent Showcase", "type": "Exhibition", "entry_fee": 0, "participants": "8/15", "duration": "3 days", "prize": "Promotion opportunity"},
    {"name": "Team Challenge", "type": "Competition", "entry_fee": 1000, "participants": "24/30", "duration": "7 days", "prize": "25,000 beans + sponsorship"}
]

growth_strategies = {
    "default": "Focus on consistency, engaging with viewers, collaborating with other streamers, and cross-platform promotion.",
    "instagram": "Post daily stories, weekly carousel posts, and use relevant hashtags. Promote your Bigo Live schedule.",
    "tiktok": "Create 3-5 short clips daily from your streams. Use trending sounds and participate in challenges.",
    "youtube": "Upload weekly highlight videos and monthly best-of compilations. Optimize titles and thumbnails.",
    "twitter": "Tweet updates before going live, share screenshots, and engage with your community frequently."
}

def get_events() -> str:
    """Get current events from Bigo Live by scraping with requests and BeautifulSoup"""
    url = "https://www.onbigo.live/events"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        event_elements = soup.select('.event-list .event-item')
        events = []
        for event in event_elements:
            name = event.select_one('.event-name').get_text(strip=True) if event.select_one('.event-name') else ''
            rebate = event.select_one('.event-rebate').get_text(strip=True) if event.select_one('.event-rebate') else ''
            entry_fee = event.select_one('.event-entry-fee').get_text(strip=True) if event.select_one('.event-entry-fee') else ''
            duration = event.select_one('.event-duration').get_text(strip=True) if event.select_one('.event-duration') else ''
            events.append({
                "name": name,
                "rebate": rebate,
                "entry_fee": entry_fee,
                "duration": duration
            })
        return json.dumps({"events": events})
    except Exception as e:
        return json.dumps({"error": f"Failed to scrape events: {str(e)}"})

def get_sponsorship_info() -> str:
    """Get strategies on how to obtain sponsors"""
    strategies = [
        "Build a strong and engaged audience by consistently streaming high-quality content.",
        "Network with other streamers and industry professionals to increase visibility.",
        "Create a professional media kit showcasing your audience demographics and engagement.",
        "Reach out to potential sponsors with personalized proposals highlighting mutual benefits.",
        "Leverage social media platforms to promote your streaming brand and attract sponsors.",
        "Participate in community events and collaborations to expand your reach.",
        "Maintain transparency and professionalism in all sponsorship dealings.",
        "Offer unique sponsorship packages tailored to different sponsor needs."
    ]
    return json.dumps({"strategies": strategies})

def generate_tts(text: str) -> str:
    """
    Generate TTS audio as base64 encoded mp3 string for the given text using gTTS.
    """
    try:
        tts = gTTS(text=text, lang='en')
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        b64_audio = base64.b64encode(mp3_fp.read()).decode('utf-8')
        return f"data:audio/mp3;base64,{b64_audio}"
    except Exception as e:
        return ""

# Pydantic model for command parsing
class CommandParameters(BaseModel):
    command: str = Field(..., description="The command name without the ! prefix")
    args: Dict[str, Any] = Field(default_factory=dict, description="Command arguments as key-value pairs")

# Map command names to their functions
def convert_command(args):
    try:
        ctype = args.get("type")
        amount = float(args.get("amount", 0))
        if ctype not in conversion_rates:
            return json.dumps({"response": f"Unknown conversion type: {ctype}"})
        conversions = conversion_rates[ctype]
        result = {k: round(amount * v, 2) for k, v in conversions.items()}
        return json.dumps({"response": f"{amount} {ctype} converts to {result}"})
    except Exception as e:
        return json.dumps({"error": f"Error in convert command: {str(e)}"})

def track_command(args):
    try:
        beans = int(args.get("beans", 0))
        hours = int(args.get("hours", 0))
        current_tier = "Unranked"
        for tier in reversed(tiers):
            if beans >= tier["beans"] and hours >= tier["hours"]:
                current_tier = tier["name"]
                break
        return json.dumps({"response": f"With {beans} beans and {hours} hours, your tier is {current_tier}."})
    except Exception as e:
        return json.dumps({"error": f"Error in track command: {str(e)}"})

import scraper
import json

def scrape_command(args):
    html = args.get("html", "")
    if not html:
        return json.dumps({"error": "No HTML snippet provided for scraping."})
    results = scraper.scrape_links_from_html(html)
    summary = {url: f"Content length: {len(content)} characters" for url, content in results.items()}
    return json.dumps({"response": summary})

command_functions = {
    "track": track_command,
    "events": lambda args=None: get_events(),
    "growth": lambda args=None: json.dumps({"response": "To grow and build a huge community, focus on consistent streaming, engaging content, cross-platform promotion, and building strong relationships with your fans. Collaborate with other streamers and use social media effectively."}),
    "sponsorship": lambda args=None: json.dumps({"response": "To obtain sponsors online, build a strong audience, create a professional media kit, network with brands, and reach out with personalized proposals. Maintain professionalism and offer tailored sponsorship packages."}),
    "wishlist": lambda args=None: json.dumps({"response": "Guide your viewers to support you by setting up an Amazon wishlist, sharing it on your stream, and encouraging donations for the items you use during your streams."}),
    "cross_promote": lambda args=None: json.dumps({"response": "Use godlike strategies for cross promotion by collaborating with other streamers, sharing content across platforms, and engaging with multiple communities to expand your reach."}),
    "loan_info": lambda args=None: json.dumps({"response": "Loan info is coming soon."}),
    "credit_score": lambda args=None: json.dumps({"response": "Everyone starts with a credit score of 0."}),
    "scrape": scrape_command
}

def process_command(user_input: str, conversation_history: str = "") -> str:
    """Process a user input and intelligently decide which command to run or respond conversationally, using conversation history"""
    system_message = """You are Bean-Genie, a Discord bot for Bigo Live streamers.
    You can understand natural language input and decide which command to run if any.
    If the input is a command, extract the command name and arguments.
    If the input is conversational, respond appropriately without requiring a command prefix.
    Use the conversation history to maintain context.
    """
    
    combined_input = conversation_history + "\nUser: " + user_input
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": combined_input}
    ]
    
    global current_model_index
    
    # Try models in order until success or all exhausted
    for attempt in range(len(SUPPORTED_MODELS)):
        model_to_use = SUPPORTED_MODELS[current_model_index]
        try:
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            try:
                parsed = json.loads(content)
                command = parsed.get("command", "").lower()
                args = parsed.get("args", {})
                if command in command_functions:
                    result = command_functions[command](args)
                    # Append TTS audio info to response
                    tts_audio = generate_tts(result)
                    return json.dumps({"response": result, "tts": tts_audio})
                else:
                    return content
            except Exception:
                return content
            
        except Exception as e:
            error_message = str(e).lower()
            # Check for limit or model errors to switch model
            if "limit" in error_message or "model" in error_message or "unavailable" in error_message:
                # Switch to next model
                current_model_index = (current_model_index + 1) % len(SUPPORTED_MODELS)
                continue
            else:
                return json.dumps({"error": f"Error processing input: {str(e)}"})
    
    return json.dumps({"error": "All models exhausted or unavailable. Please try again later."})

# CLI application
def run_cli():
    print("Bean-Genie Discord Bot (CLI Version)")
    print("Type a command (e.g., !convert beans 1000) or 'exit' to quit.")
    print("-" * 50)
    
    while True:
        user_input = input("\nEnter command: ")
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        response = process_command(user_input)
        print("\nResponse:")
        print(response)
        print("-" * 50)

if __name__ == "__main__":
    run_cli()

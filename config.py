import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") # private repo idgaf
DISABLED_COMMANDS = {
    # Example: 'moderation': ['warn']
}

# Optional: Add a check to ensure the token was loaded
if DISCORD_TOKEN is None:
    raise ValueError("DISCORD_TOKEN is not set. Please check your .env file.")
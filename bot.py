import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from collections import defaultdict
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guild_messages = True  # Add this to ensure we can track messages
intents.guilds = True  # Add this to ensure we can access guild data

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Connected to {len(bot.guilds)} guilds:")
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")

@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    """Sync the slash commands with Discord (Admin only)"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} command(s) with Discord")
        print(f"Manually synced {len(synced)} command(s)")
    except Exception as e:
        await ctx.send(f"❌ Failed to sync commands: {e}")
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="recommend", description="Recommend a book")
@app_commands.describe(
    book="The name of the book you want to recommend",
    note="Optional: Add a short note about the book"
)
async def recommend(interaction: discord.Interaction, book: str, note: str = None):
    """Recommend a book in the current channel"""
    # Create and send embed
    embed = discord.Embed(
        title="Book Recommendation",
        description=f"**Book:** {book}",
        color=discord.Color.blue()
    )
    if note:
        embed.add_field(name="Note", value=note, inline=False)
    embed.set_footer(text=f"Recommended by {interaction.user.display_name} • React with 👍 to upvote")
    await interaction.response.send_message("Your recommendation has been posted!", ephemeral=True)
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction("👍")

@bot.tree.command(name="view", description="View the most popular book recommendations")
async def view(interaction: discord.Interaction):
    """View the leaderboard of book recommendations by fetching all bot messages in the channel"""
    await interaction.response.defer(ephemeral=True)
    
    # Fetch all messages in the channel (limit to last 1000 for performance)
    messages = []
    async for message in interaction.channel.history(limit=1000):
        if message.author.id == bot.user.id:
            # Check if this message is a book recommendation (by embed title)
            if message.embeds and message.embeds[0].title == "Book Recommendation":
                messages.append(message)
    
    if not messages:
        await interaction.followup.send("No active book recommendations found in this channel!", ephemeral=True)
        return
    
    # Build leaderboard: [(message, vote_count, book, note, recommender)]
    leaderboard = []
    for message in messages:
        embed = message.embeds[0]
        book = embed.description.replace("**Book:** ", "") if embed.description else "Unknown"
        note = None
        for field in embed.fields:
            if field.name == "Note":
                note = field.value
        recommender = embed.footer.text.split("Recommended by ")[1].split(" • ")[0] if embed.footer and embed.footer.text else "Unknown"
        vote_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == "👍":
                vote_count = reaction.count - 1  # Exclude bot's own reaction
                break
        leaderboard.append((message, vote_count, book, note, recommender))
    
    # Sort by vote count descending
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    
    # Create the leaderboard embed
    embed = discord.Embed(
        title="Book Recommendation Leaderboard",
        description="The most popular book recommendations:",
        color=discord.Color.gold()
    )
    place_emoji = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    for i, (msg, vote_count, book, note, recommender) in enumerate(leaderboard[:10], 1):
        emoji = place_emoji[i - 1] if i <= 3 else "🔹"
        field_value = f"Recommended by {recommender} • 👍 **{vote_count} vote{'s' if vote_count != 1 else ''}**"
        if note:
            field_value += f"\n*\"{note}\"*"
        embed.add_field(
            name=f"{emoji} {book}",
            value=field_value,
            inline=False
        )
    await interaction.followup.send(embed=embed)

# Also let's add a debug command to check recommendations
@bot.tree.command(name="debug_recommendations", description="Debug: Show current recommendations data")
async def debug_recommendations(interaction: discord.Interaction):
    """Debug command to show current recommendations data"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("This command is only available to administrators.", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    
    debug_info = {
        "total_channels": len(recommendations),
        "current_channel_recommendations": len(recommendations.get(interaction.channel_id, {})),
        "all_recommendations": recommendations
    }
    
    await interaction.followup.send(f"```json\n{json.dumps(debug_info, indent=2)}\n```", ephemeral=True)

# Add error handler
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in {event}:")
    import traceback
    traceback.print_exc()

# Run the bot with your token from environment variable
print("Starting bot...")
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("ERROR: DISCORD_TOKEN environment variable is not set!")
    exit(1)
print("Token found, attempting to connect...")
bot.run(token)  # Get token from environment variable 
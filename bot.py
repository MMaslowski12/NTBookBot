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

# Path to store recommendation data
DATA_FILE = "recommendations.json"

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Data structure to store recommendations and their votes
# Format: {channel_id: {message_id: {"book": book_name, "recommender": user_id, "votes": vote_count}}}
recommendations = defaultdict(dict)

# Load existing recommendations if available
def load_recommendations():
    global recommendations
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Convert keys back to int as JSON stores them as strings
                recommendations = defaultdict(dict)
                for channel_id, messages in data.items():
                    for message_id, info in messages.items():
                        # Ensure backward compatibility with old data format
                        if "note" not in info:
                            info["note"] = None
                        recommendations[int(channel_id)][int(message_id)] = info
        except Exception as e:
            print(f"Error loading recommendations: {e}")

# Save recommendations to file
def save_recommendations():
    with open(DATA_FILE, 'w') as f:
        json.dump(recommendations, f, indent=4)

@bot.event
async def on_ready():
    print(f"Bot is logged in as {bot.user}")
    load_recommendations()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

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

    # 🔍 Check for duplicates
    channel_recs = recommendations.get(interaction.channel_id, {})
    for rec in channel_recs.values():
        if rec["book"].strip().lower() == book.strip().lower():
            await interaction.response.send_message(
                f"⚠️ **{book}** has already been recommended in this channel!",
                ephemeral=True
            )
            return

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

    # Save recommendation
    recommendations[interaction.channel_id][message.id] = {
        "book": book,
        "recommender": interaction.user.id,
        "votes": 0,
        "note": note
    }
    save_recommendations()


@bot.tree.command(name="view", description="View the most popular book recommendations")
async def view(interaction: discord.Interaction):
    """View the leaderboard of book recommendations"""
    if not recommendations or interaction.channel_id not in recommendations:
        await interaction.response.send_message("No book recommendations have been made yet!", ephemeral=True)
        return
    
    # Get recommendations for this channel
    channel_recommendations = recommendations[interaction.channel_id]
    
    if not channel_recommendations:
        await interaction.response.send_message("No book recommendations have been made in this channel!", ephemeral=True)
        return
    
    # Create a list to store recommendations with their current vote counts
    recommendations_with_votes = []
    
    # Fetch all messages and count their reactions
    for msg_id, info in channel_recommendations.items():
        try:
            message = await interaction.channel.fetch_message(msg_id)
            # Count 👍 reactions
            vote_count = 0
            for reaction in message.reactions:
                if str(reaction.emoji) == "👍":
                    vote_count = reaction.count - 1  # Subtract 1 to exclude bot's own reaction
                    break
            
            recommendations_with_votes.append((msg_id, info, vote_count))
        except Exception as e:
            print(f"Error fetching message {msg_id}: {e}")
            # If message can't be fetched, use stored vote count as fallback
            recommendations_with_votes.append((msg_id, info, info.get("votes", 0)))
    
    # Sort recommendations by vote count (descending)
    sorted_recommendations = sorted(
        recommendations_with_votes,
        key=lambda x: x[2],  # Sort by vote count
        reverse=True
    )
    
    # Create the leaderboard embed
    embed = discord.Embed(
        title="Book Recommendation Leaderboard",
        description="The most popular book recommendations:",
        color=discord.Color.gold()
    )
    
    # Add top recommendations to the embed
    place_emoji = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    for i, (msg_id, info, vote_count) in enumerate(sorted_recommendations[:10], 1):
        recommender = f"<@{info['recommender']}>"
        book_title = info['book']
        note = info.get('note')

        emoji = place_emoji[i - 1] if i <= 3 else "🔹"

        field_value = f"Recommended by {recommender} • 👍 **{vote_count} vote{'s' if vote_count != 1 else ''}**"
        if note:
            field_value += f"\n*\"{note}\"*"
            
        embed.add_field(
            name=f"{emoji} {book_title}",
            value=field_value,
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

# Remove the old reaction handlers since we're not storing votes anymore
@bot.event
async def on_reaction_add(reaction, user):
    # Ignore bot's own reactions
    if user.bot:
        return
    
    # We don't need to store votes anymore as we count them directly
    pass

@bot.event
async def on_reaction_remove(reaction, user):
    # Ignore bot's own reactions
    if user.bot:
        return
    
    # We don't need to store votes anymore as we count them directly
    pass

# Run the bot with your token from environment variable
bot.run(os.getenv('DISCORD_TOKEN'))  # Get token from environment variable 
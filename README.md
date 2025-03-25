# Book Bot

A Discord bot that allows users to recommend books and vote on recommendations in your server.

## Features

- `/recommend` - Recommend a book with an optional note
- `/view` - View the most popular book recommendations
- React with 👍 to upvote recommendations

## Setup

1. Clone this repository
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_token_here
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```
   python book_bot.py
   ```

## Commands

- `/recommend <book> [note]` - Recommend a book with optional note
- `/view` - View the leaderboard of book recommendations
- `!sync` - Admin only: Sync slash commands with Discord (use after bot updates)

## Deployment

### Deploying on Render.com

1. Fork this repository to your GitHub account
2. Create a new Web Service on Render.com
3. Connect your GitHub repository
4. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python book_bot.py`
5. Add the `DISCORD_TOKEN` environment variable in the Render dashboard

## License

MIT License 
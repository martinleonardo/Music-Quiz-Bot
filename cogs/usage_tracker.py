import discord
from discord import app_commands
from discord.ext import commands

import json
import csv
from pathlib import Path
from datetime import datetime, timezone


DATA_DIR = Path("data")
COUNTS_FILE = DATA_DIR / "command_counts.json"
RUNS_FILE = DATA_DIR / "command_runs.csv"


class UsageTracker(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        DATA_DIR.mkdir(exist_ok=True)

        self.command_counts = self.load_counts()
        self.ensure_csv_header()

    # --------------------
    # Persistence
    # --------------------

    def load_counts(self) -> dict:
        if COUNTS_FILE.exists():
            with COUNTS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_counts(self):
        with COUNTS_FILE.open("w", encoding="utf-8") as f:
            json.dump(self.command_counts, f, indent=4)

    def ensure_csv_header(self):
        if not RUNS_FILE.exists():
            with RUNS_FILE.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp_utc",
                    "command",
                    "user_id",
                    "guild_id",
                    "channel_id"
                ])

    # --------------------
    # Tracking
    # --------------------

    def increment(self, command_name: str):
        self.command_counts[command_name] = self.command_counts.get(command_name, 0) + 1
        self.save_counts()

    def log_run(self, interaction: discord.Interaction):
        with RUNS_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now(timezone.utc).isoformat(),
                interaction.command.name,
                interaction.user.id,
                interaction.guild_id,
                interaction.channel_id
            ])

    def get_count(self, key: str) -> int:
        return self.command_counts.get(key, 0)

    async def track(self, interaction: discord.Interaction):
        self.increment(interaction.command.name)
        self.log_run(interaction)

    # --------------------
    # Autocomplete
    # --------------------

    async def command_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        return [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in self.command_counts.keys()
            if current.lower() in cmd.lower()
        ][:25]

    # --------------------
    # Example tracked command
    # --------------------

    @app_commands.command(
        name="tmar",
        description="Times Torrance has mentioned marmar"
    )
    async def tmar(self, interaction: discord.Interaction):
        key = "tmar"

        # Single source of truth
        self.increment(key)

        count = self.command_counts.get(key, 0)

        await interaction.response.send_message(
            f"Times Torrance has mentioned marmar: **{count}**"
        )



    # --------------------
    # Analytics commands
    # --------------------

    @app_commands.command(name="commandcount", description="Check how many times a command was used")
    @app_commands.autocomplete(command=command_autocomplete)
    async def commandcount(
        self,
        interaction: discord.Interaction,
        command: str,
    ):
        count = self.command_counts.get(command, 0)
        await interaction.response.send_message(
            f"`/{command}` has been used **{count}** times."
        )

    @app_commands.command(name="setcommandcount", description="Admin: override command usage count")
    @app_commands.autocomplete(command=command_autocomplete)
    async def setcommandcount(
        self,
        interaction: discord.Interaction,
        command: str,
        value: int,
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You need administrator permissions to do that.",
                ephemeral=True,
            )
            return

        if value < 0:
            await interaction.response.send_message(
                "Value must be >= 0.",
                ephemeral=True,
            )
            return

        self.command_counts[command] = value
        self.save_counts()

        await interaction.response.send_message(
            f"Usage count for `/{command}` set to **{value}**."
        )


async def setup(client: commands.Bot):
    await client.add_cog(UsageTracker(client))

from functions import *
from import_lib import *
import discord
from discord.ext import commands
import mysql.connector

class addbugs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.superuser = int(os.getenv("SUPER_USER_ID"))
        self.adminrole = int(os.getenv("ADMIN_ROLE_ID"))

    @commands.hybrid_command(name="addbugs", description="Adds bugs to a specified user", with_app_command=True)
    async def addbugs(self, ctx, member: discord.Member = None, amount: int = 0):
        """
        Adds bugs to a specified user.

        :param member: The user you want to add bugs to.
        :param amount: The amount you want to add.
        """
        # Check if the user has any of the specified roles
        if not any(role.id in {self.superuser, self.adminrole} for role in ctx.author.roles):
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description="Insufficient Permissions. You need the required roles to use this command.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description="You cannot add a negative amount of bugs.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        if member is None:
            member = ctx.author

        # Check if the user has linked their Steam ID
        player_data = get_player_data(member.id)
        if player_data is None:
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description=f"{member.mention} has not linked their Steam ID, so bugs cannot be added.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        try:
            # Establish the database connection and cursor
            with mysql.connector.connect(**config) as db:
                with db.cursor() as cursor:
                    # Update the user's balance in the database
                    current_balance = player_data["bugs"]
                    new_balance = current_balance + amount
                    cursor.execute(
                        "UPDATE players SET bugs = %s WHERE discord_id = %s",
                        (new_balance, member.id),
                    )
                    db.commit()

                    # Fetch the updated user data from the database
                    player_data = get_player_data(member.id)

                    # Send the command response with the updated user data
                    embed = discord.Embed(
                        title="Animalia Survial 🤖",
                        description=f"{amount} :bug: added to {member.mention}'s balance. New balance is {player_data['bugs']} :bug:.",
                        color=0x00FF00,
                    )
                    await ctx.send(embed=embed)
        except mysql.connector.Error as e:
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description=f"Database error occurred: {str(e)}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

    @addbugs.error
    async def addbugs_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description="Insufficient Permissions. You need the required roles to use this command.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description="Please use the command correctly: !addbugs {user} {amount}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Animalia Survial 🤖",
                description=f"An error occurred: {str(error)}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(addbugs(bot))

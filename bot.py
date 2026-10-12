import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ==================== НАСТРОЙКИ ====================
# ID ролей, которым разрешено выдавать/забирать роли
ALLOWED_ROLE_IDS = {
    1512321611884396665,
    1500474195211980980,
    1557799401072890017,
}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ==================== ПРОВЕРКА ПРАВ ====================

def has_allowed_role():
    """Проверяет, есть ли у пользователя одна из разрешённых ролей"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == interaction.guild.owner_id:
            return True  # владелец сервера всегда может
        
        user_role_ids = {role.id for role in interaction.user.roles}
        return bool(user_role_ids & ALLOWED_ROLE_IDS)
    
    return app_commands.check(predicate)


# ==================== СОБЫТИЯ ====================

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Синхронизировано команд: {len(synced)}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")


# ==================== КОМАНДЫ ====================

@bot.tree.command(name="give_role", description="Выдать роль пользователю")
@app_commands.describe(
    user="Кому выдать роль",
    role="Какую роль выдать"
)
@has_allowed_role()
async def give_role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):
    # Проверки иерархии
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ У бота недостаточно прав — роль выше или равна моей самой высокой роли.",
            ephemeral=True
        )
        return

    if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "❌ Ты не можешь выдавать роль выше или равную своей.",
            ephemeral=True
        )
        return

    if role in user.roles:
        await interaction.response.send_message(
            f"⚠️ У {user.mention} уже есть роль {role.mention}.",
            ephemeral=True
        )
        return

    try:
        await user.add_roles(role, reason=f"Выдано через бота пользователем {interaction.user}")
        embed = discord.Embed(
            title="✅ Роль выдана",
            description=f"Пользователю {user.mention} выдана роль {role.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Выдал: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ У бота нет прав на выдачу этой роли. Проверь права и иерархию ролей.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)


@bot.tree.command(name="remove_role", description="Забрать роль у пользователя")
@app_commands.describe(
    user="У кого забрать роль",
    role="Какую роль забрать"
)
@has_allowed_role()
async def remove_role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ У бота недостаточно прав — роль выше или равна моей самой высокой роли.",
            ephemeral=True
        )
        return

    if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "❌ Ты не можешь забирать роль выше или равную своей.",
            ephemeral=True
        )
        return

    if role not in user.roles:
        await interaction.response.send_message(
            f"⚠️ У {user.mention} нет роли {role.mention}.",
            ephemeral=True
        )
        return

    try:
        await user.remove_roles(role, reason=f"Забрано через бота пользователем {interaction.user}")
        embed = discord.Embed(
            title="✅ Роль забрана",
            description=f"У пользователя {user.mention} забрана роль {role.mention}",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Забрал: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ У бота нет прав на управление этой ролью.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)


@bot.tree.command(name="my_roles", description="Показать свои роли на сервере")
async def my_roles(interaction: discord.Interaction):
    roles = [role.mention for role in interaction.user.roles if role.name != "@everyone"]
    
    if not roles:
        await interaction.response.send_message("У тебя пока нет ролей.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🎭 Роли {interaction.user.display_name}",
        description="\n".join(roles),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="user_roles", description="Показать роли другого пользователя")
@app_commands.describe(user="Чьи роли посмотреть")
async def user_roles(interaction: discord.Interaction, user: discord.Member):
    roles = [role.mention for role in user.roles if role.name != "@everyone"]
    
    if not roles:
        await interaction.response.send_message(
            f"У {user.mention} пока нет ролей.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"🎭 Роли {user.display_name}",
        description="\n".join(roles),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed)


# ==================== ОБРАБОТКА ОШИБОК ====================

@give_role.error
@remove_role.error
async def role_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ У тебя нет доступа к этой команде.\n"
            "Нужна одна из специальных ролей.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ Произошла ошибка: {error}",
            ephemeral=True
        )


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Ошибка: не найден DISCORD_TOKEN в .env файле!")
        print("Создай файл .env и добавь туда токен.")
        exit(1)
    
    bot.run(TOKEN)

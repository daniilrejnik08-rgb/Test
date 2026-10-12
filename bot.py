import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Файл, где хранятся ID ролей с доступом
DATA_FILE = "allowed_roles.json"

# Если хочешь мгновенную синхронизацию — укажи ID сервера
GUILD_ID = None  # например: 1234567890123456789

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ==================== РАБОТА С ДАННЫМИ ====================

def load_allowed_roles() -> set[int]:
    """Загружает список разрешённых ролей из файла"""
    if not os.path.exists(DATA_FILE):
        return set()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("roles", []))
    except Exception:
        return set()


def save_allowed_roles(roles: set[int]):
    """Сохраняет список разрешённых ролей в файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"roles": list(roles)}, f, indent=2)


# ==================== ПРОВЕРКА ПРАВ ====================

def has_allowed_role():
    """Проверяет, есть ли у пользователя доступ к командам выдачи/снятия ролей"""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Владелец сервера всегда может
        if interaction.guild and interaction.user.id == interaction.guild.owner_id:
            return True

        # Администраторы тоже могут (удобно для управления)
        if isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator:
            return True

        member = interaction.user
        if not isinstance(member, discord.Member):
            if interaction.guild:
                member = interaction.guild.get_member(interaction.user.id)
            if member is None:
                return False

        allowed = load_allowed_roles()
        user_role_ids = {role.id for role in member.roles}
        return bool(user_role_ids & allowed)

    return app_commands.check(predicate)


def is_admin():
    """Только администраторы и владелец сервера"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild and interaction.user.id == interaction.guild.owner_id:
            return True
        if isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator:
            return True
        return False
    return app_commands.check(predicate)


# ==================== СОБЫТИЯ ====================

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")
    print(f"   Серверов: {len(bot.guilds)}")
    print(f"   Ролей с доступом: {len(load_allowed_roles())}")

    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"🔄 Команды синхронизированы на сервер {GUILD_ID}: {len(synced)} шт.")
        else:
            synced = await bot.tree.sync()
            print(f"🔄 Глобально синхронизировано команд: {len(synced)}")
            print("   ⏳ Глобальные команды могут появиться не сразу (до 1 часа)")
            print("   💡 Чтобы команды появились сразу — укажи GUILD_ID в bot.py")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")


# ==================== КОМАНДЫ ВЫДАЧИ / СНЯТИЯ РОЛЕЙ ====================

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


# ==================== УПРАВЛЕНИЕ ДОСТУПОМ ====================

@bot.tree.command(name="add_access", description="Выдать роли доступ к командам выдачи/снятия ролей")
@app_commands.describe(role="Роль, которой дать доступ")
@is_admin()
async def add_access(interaction: discord.Interaction, role: discord.Role):
    allowed = load_allowed_roles()

    if role.id in allowed:
        await interaction.response.send_message(
            f"⚠️ Роль {role.mention} уже имеет доступ.",
            ephemeral=True
        )
        return

    allowed.add(role.id)
    save_allowed_roles(allowed)

    embed = discord.Embed(
        title="✅ Доступ выдан",
        description=f"Роль {role.mention} теперь может использовать `/give_role` и `/remove_role`",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="remove_access", description="Забрать у роли доступ к командам выдачи/снятия ролей")
@app_commands.describe(role="Роль, у которой забрать доступ")
@is_admin()
async def remove_access(interaction: discord.Interaction, role: discord.Role):
    allowed = load_allowed_roles()

    if role.id not in allowed:
        await interaction.response.send_message(
            f"⚠️ У роли {role.mention} и так нет доступа.",
            ephemeral=True
        )
        return

    allowed.discard(role.id)
    save_allowed_roles(allowed)

    embed = discord.Embed(
        title="✅ Доступ забран",
        description=f"Роль {role.mention} больше не может использовать `/give_role` и `/remove_role`",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="list_access", description="Показать роли, у которых есть доступ к выдаче/снятию ролей")
async def list_access(interaction: discord.Interaction):
    allowed = load_allowed_roles()

    if not allowed:
        await interaction.response.send_message(
            "Список пуст. Пока никто не имеет доступа (кроме администраторов и владельца сервера).",
            ephemeral=True
        )
        return

    lines = []
    for role_id in allowed:
        role = interaction.guild.get_role(role_id)
        if role:
            lines.append(f"• {role.mention} (`{role_id}`)")
        else:
            lines.append(f"• ❌ Роль удалена (`{role_id}`)")

    embed = discord.Embed(
        title="🔐 Роли с доступом",
        description="\n".join(lines),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Администраторы и владелец сервера имеют доступ всегда")
    await interaction.response.send_message(embed=embed)


# ==================== ПРОЧИЕ КОМАНДЫ ====================

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


@bot.tree.command(name="sync", description="Принудительно синхронизировать команды (только админы)")
@app_commands.checks.has_permissions(administrator=True)
async def sync_commands(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync(guild=interaction.guild)
        await interaction.followup.send(
            f"✅ Синхронизировано команд на этом сервере: **{len(synced)}**\n"
            f"Команды должны появиться в течение нескольких секунд.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)


# ==================== ОБРАБОТКА ОШИБОК ====================

@give_role.error
@remove_role.error
async def role_cmd_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ У тебя нет доступа к этой команде.\n"
            "Нужна специальная роль (её выдаёт администратор через `/add_access`).",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(f"❌ Произошла ошибка: {error}", ephemeral=True)


@add_access.error
@remove_access.error
async def access_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ Только администраторы и владелец сервера могут управлять доступом.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(f"❌ Произошла ошибка: {error}", ephemeral=True)


@sync_commands.error
async def sync_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Нужны права администратора.", ephemeral=True)


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Ошибка: не найден DISCORD_TOKEN в .env файле!")
        print("Создай файл .env и добавь туда токен.")
        exit(1)

    bot.run(TOKEN)

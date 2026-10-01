import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== НАСТРОЙКИ ====================
TOKEN = os.getenv("DISCORD_TOKEN")
MSK = timezone(timedelta(hours=3))

# Цвета
COLOR_ACTIVE = 0x00FF9F      # Неоновый зелёный
COLOR_WARNING = 0xFFAA00     # Оранжевый (когда < 1 часа)
COLOR_CRITICAL = 0xFF3355    # Красный (когда < 10 минут)
COLOR_SUCCESS = 0x00FF88     # Успех
COLOR_ERROR = 0xFF4444

# Эмодзи
EMOJI_TIMER = "⏳"
EMOJI_ROCKET = "🚀"
EMOJI_FIRE = "🔥"
EMOJI_CLOCK = "🕒"
EMOJI_CHECK = "✅"
EMOJI_STOP = "🛑"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Хранилище активных таймеров
# {channel_id: {"end_time": datetime, "message": Message, "title": str, "started_by": str}}
active_timers: dict[int, dict] = {}


def format_time_left(td: timedelta) -> str:
    """Красивое форматирование оставшегося времени"""
    total = max(0, int(td.total_seconds()))
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if days > 0:
        parts.append(f"**{days}**д")
    if hours > 0 or days > 0:
        parts.append(f"**{hours}**ч")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"**{minutes}**м")
    parts.append(f"**{seconds}**с")

    return " ".join(parts)


def create_progress_bar(percent: float, length: int = 16) -> str:
    """Создаёт текстовый прогресс-бар"""
    filled = int(percent * length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    return f"`{bar}` {int(percent * 100)}%"


def get_color(remaining: timedelta) -> int:
    """Выбирает цвет в зависимости от оставшегося времени"""
    total = remaining.total_seconds()
    if total <= 600:      # < 10 минут
        return COLOR_CRITICAL
    elif total <= 3600:   # < 1 часа
        return COLOR_WARNING
    return COLOR_ACTIVE


def build_embed(
    title: str,
    end_time: datetime,
    remaining: timedelta,
    started_by: str | None = None,
    start_time: datetime | None = None
) -> discord.Embed:
    """Создаёт красивый embed"""
    color = get_color(remaining)
    time_str = format_time_left(remaining)
    timestamp = int(end_time.timestamp())

    # Прогресс-бар
    progress_line = ""
    if start_time:
        total = (end_time - start_time).total_seconds()
        if total > 0:
            elapsed = total - remaining.total_seconds()
            progress = max(0.0, min(1.0, elapsed / total))
            progress_line = f"\n{create_progress_bar(progress, 18)}\n"

    embed = discord.Embed(
        title=f"{EMOJI_TIMER}  {title}",
        description=(
            f"### Осталось\n"
            f"# {time_str}\n"
            f"{progress_line}"
        ),
        color=color,
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name=f"{EMOJI_CLOCK} Точное время старта",
        value=f"<t:{timestamp}:F>\n(<t:{timestamp}:R>)",
        inline=False
    )

    if started_by:
        embed.add_field(
            name="Запустил",
            value=started_by,
            inline=True
        )

    embed.set_footer(text="ZXC CS Servers • Обновляется автоматически")

    return embed


def build_finished_embed(title: str) -> discord.Embed:
    """Embed когда таймер завершён"""
    embed = discord.Embed(
        title=f"{EMOJI_ROCKET}  {title}",
        description=(
            f"# Серверы запущены!\n\n"
            f"{EMOJI_FIRE} **ZXC CS** онлайн\n"
            f"Заходите и играйте!"
        ),
        color=COLOR_SUCCESS,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="ZXC CS Servers")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} успешно запущен!")
    print(f"📊 Серверов: {len(bot.guilds)}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Синхронизировано команд: {len(synced)}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
    
    if not update_timers.is_running():
        update_timers.start()


@bot.tree.command(name="таймер", description="Запустить красивый отсчёт до старта серверов ZXC")
@app_commands.describe(
    дата="Дата в формате ДД.ММ.ГГГГ (пример: 05.10.2026)",
    время="Время по МСК в формате ЧЧ:ММ (пример: 18:00)",
    название="Название события (по умолчанию: Старт серверов ZXC)"
)
async def timer_command(
    interaction: discord.Interaction,
    дата: str,
    время: str,
    название: str = "Старт серверов ZXC CS"
):
    # Проверяем, есть ли уже таймер в канале
    if interaction.channel_id in active_timers:
        await interaction.response.send_message(
            f"{EMOJI_STOP} В этом канале уже есть активный таймер.\n"
            f"Сначала останови его командой `/стоп_таймер`",
            ephemeral=True
        )
        return

    try:
        # Парсим дату и время по МСК
        naive = datetime.strptime(f"{дата} {время}", "%d.%m.%Y %H:%M")
        end_time = naive.replace(tzinfo=MSK).astimezone(timezone.utc)

        now = datetime.now(timezone.utc)
        if end_time <= now:
            await interaction.response.send_message(
                f"{EMOJI_STOP} Указанное время уже прошло!",
                ephemeral=True
            )
            return

        remaining = end_time - now
        embed = build_embed(
            название,
            end_time,
            remaining,
            interaction.user.mention,
            start_time=now
        )

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        active_timers[interaction.channel_id] = {
            "end_time": end_time,
            "message": message,
            "title": название,
            "started_by": interaction.user.mention,
            "start_time": now
        }

        await interaction.followup.send(
            f"{EMOJI_CHECK} Таймер успешно запущен!",
            ephemeral=True
        )

    except ValueError:
        await interaction.response.send_message(
            f"{EMOJI_STOP} **Неверный формат!**\n\n"
            f"Правильно:\n"
            f"`/таймер дата:05.10.2026 время:18:00`\n\n"
            f"• Дата: `ДД.ММ.ГГГГ`\n"
            f"• Время: `ЧЧ:ММ` (по московскому времени)",
            ephemeral=True
        )


@bot.tree.command(name="стоп_таймер", description="Остановить активный таймер в этом канале")
async def stop_timer(interaction: discord.Interaction):
    if interaction.channel_id not in active_timers:
        await interaction.response.send_message(
            f"{EMOJI_STOP} В этом канале нет активного таймера.",
            ephemeral=True
        )
        return

    data = active_timers.pop(interaction.channel_id)
    try:
        embed = discord.Embed(
            title=f"{EMOJI_STOP} Таймер остановлен",
            description=f"**{data['title']}** был отменён.",
            color=COLOR_ERROR
        )
        await data["message"].edit(embed=embed)
    except Exception:
        pass

    await interaction.response.send_message(
        f"{EMOJI_CHECK} Таймер остановлен.",
        ephemeral=True
    )


@bot.tree.command(name="статус", description="Показать информацию об активном таймере")
async def status_command(interaction: discord.Interaction):
    if interaction.channel_id not in active_timers:
        await interaction.response.send_message(
            f"{EMOJI_STOP} В этом канале нет активного таймера.",
            ephemeral=True
        )
        return

    data = active_timers[interaction.channel_id]
    remaining = data["end_time"] - datetime.now(timezone.utc)
    
    embed = build_embed(
        data["title"],
        data["end_time"],
        remaining,
        data.get("started_by"),
        data.get("start_time")
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tasks.loop(seconds=20)
async def update_timers():
    """Обновляет все активные таймеры"""
    now = datetime.now(timezone.utc)
    to_remove = []

    for channel_id, data in list(active_timers.items()):
        end_time: datetime = data["end_time"]
        message: discord.Message = data["message"]
        title: str = data["title"]
        remaining = end_time - now

        try:
            if remaining.total_seconds() <= 0:
                # Таймер закончился
                finished = build_finished_embed(title)
                await message.edit(embed=finished)

                # Пингуем
                try:
                    await message.channel.send(
                        f"{EMOJI_ROCKET} @everyone\n"
                        f"**{title}** — серверы **ZXC** запущены! {EMOJI_FIRE}\n"
                        f"Залетайте играть!"
                    )
                except discord.Forbidden:
                    # Нет прав на mention everyone
                    await message.channel.send(
                        f"{EMOJI_ROCKET} **{title}** — серверы **ZXC** запущены! {EMOJI_FIRE}"
                    )

                to_remove.append(channel_id)
            else:
                # Обновляем embed
                embed = build_embed(
                    title,
                    end_time,
                    remaining,
                    data.get("started_by"),
                    data.get("start_time")
                )
                await message.edit(embed=embed)

        except discord.NotFound:
            # Сообщение удалили
            to_remove.append(channel_id)
        except discord.Forbidden:
            to_remove.append(channel_id)
        except Exception as e:
            print(f"Ошибка обновления таймера в канале {channel_id}: {e}")

    for cid in to_remove:
        active_timers.pop(cid, None)


@update_timers.before_loop
async def before_update():
    await bot.wait_until_ready()


if __name__ == "__main__":
    if not TOKEN:
        print("❌ Ошибка: не найден DISCORD_TOKEN в .env файле!")
        print("Создай файл .env и добавь туда токен.")
        exit(1)
    
    bot.run(TOKEN)

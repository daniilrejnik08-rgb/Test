# ⏳ ZXC Countdown Bot

Красивый Discord-бот для отсчёта времени до старта серверов **ZXC CS**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.3+-purple)

## Возможности

- 🎯 Красивый embed с живым отсчётом
- ⏱️ Автоматическое обновление каждую минуту
- 📢 Пинг `@everyone` при старте
- 🛑 Команда остановки таймера
- 🇷🇺 Полностью на русском языке
- 🎨 Стильный дизайн под ZXC

## Установка

1. **Установи Python 3.10+**

2. **Установи зависимости:**
```bash
pip install -r requirements.txt
```

3. **Создай файл `.env`** (скопируй из `.env.example`):
```env
DISCORD_TOKEN=твой_токен_бота
```

4. **Создай бота:**
   - Зайди на [Discord Developer Portal](https://discord.com/developers/applications)
   - New Application → Bot → Reset Token → скопируй токен
   - Включи **MESSAGE CONTENT INTENT** и **SERVER MEMBERS INTENT**
   - OAuth2 → URL Generator → scopes: `bot` + `applications.commands`
   - Permissions: `Send Messages`, `Embed Links`, `Manage Messages`, `Mention Everyone`
   - Пригласи бота на сервер

5. **Запусти:**
```bash
python bot.py
```

## Команды

| Команда | Описание |
|---------|----------|
| `/таймер` | Запустить отсчёт |
| `/стоп_таймер` | Остановить текущий таймер |
| `/статус` | Показать активный таймер |

### Пример использования

```
/таймер дата:05.10.2026 время:18:00 название:Старт ZXC Random Skills
```

Формат даты: `ДД.ММ.ГГГГ`  
Формат времени: `ЧЧ:ММ` (по МСК)

## Структура

```
zxc-countdown-bot/
├── bot.py              # Основной код бота
├── requirements.txt    # Зависимости
├── .env.example        # Пример конфигурации
└── README.md           # Эта инструкция
```

---

Сделано с ❤️ для сообщества ZXC

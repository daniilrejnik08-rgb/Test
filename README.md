# 🎭 Discord Role Bot

Простой и удобный Discord-бот для выдачи и снятия ролей.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.3+-purple)

## Возможности

- ✅ Выдача роли пользователю
- ✅ Снятие роли
- ✅ Просмотр своих ролей
- ✅ Просмотр ролей другого пользователя
- 🔒 Доступ только у указанных ролей
- 🇷🇺 Описания и сообщения на русском языке

> **Важно:** Discord не разрешает кириллицу в *названиях* слэш-команд, поэтому сами команды на английском, а всё остальное — на русском.

## Команды

| Команда | Описание | Кто может |
|---------|----------|-----------|
| `/give_role` | Выдать роль пользователю | Только указанные роли |
| `/remove_role` | Забрать роль у пользователя | Только указанные роли |
| `/my_roles` | Показать свои роли | Все |
| `/user_roles` | Показать роли другого человека | Все |

### Примеры

```
/give_role user:@Игрок role:@VIP
/remove_role user:@Игрок role:@VIP
/my_roles
/user_roles user:@Игрок
```

## Установка

1. **Установи Python 3.10+**

2. **Установи зависимости:**
```bash
pip install -r requirements.txt
```

3. **Создай файл `.env`:**
```env
DISCORD_TOKEN=твой_токен_бота
```

4. **Создай бота в Discord:**
   - Зайди на [Discord Developer Portal](https://discord.com/developers/applications)
   - New Application → вкладка **Bot** → Reset Token → скопируй токен
   - Включи **SERVER MEMBERS INTENT** (обязательно!)
   - OAuth2 → URL Generator:
     - Scopes: `bot` + `applications.commands`
     - Permissions: `Manage Roles`, `Send Messages`, `Embed Links`
   - Пригласи бота на сервер

5. **Важно про роли:**
   - Роль бота должна быть **выше** тех ролей, которые он будет выдавать
   - Перетащи роль бота выше нужных ролей в настройках сервера

6. **Запусти:**
```bash
python bot.py
```

## Структура

```
role-bot/
├── bot.py              # Основной код
├── requirements.txt    # Зависимости
├── .env.example        # Пример конфигурации
└── README.md           # Эта инструкция
```

---

Готово к использованию 🚀

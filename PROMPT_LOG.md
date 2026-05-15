# Prompt Log
## Задание Повышенной сложности 1: Создание полноценного веб-приложения
### Промпт 1
**Инструмент:** Auto режим в Cursor.
**Промпт:** "You need to help me create a Taxi order service web app. simplest interface. First task is - Bootstrap a FastAPI project with SQLAlchemy + SQLite. Create models for: `User` (id, name, email, hashed_password, role), `Order` (id, client_id, driver_id, tariff_id, status, created_at, pickup, destination), `Driver` (id, user_id, car, is_available), `Tariff` (id, name, price_per_km), `Payment` (id, order_id, amount, status, paid_at). Include Alembic migrations, a project folder structure, and a `/health` endpoint. Work in a current directory, create a logical file structure"
**Результат:** Базовая структура файловая струтура приложения, базы данных, автогенерирующейся документации (swagger). Работающий сервер, запустил uvicorn.
### Промпт 2
**Инструмент:** Auto режим в Cursor.
**Промпт:** "Now add JWT authentification. file auth.py for hashing password with bcrypt, creating access token, getting current user and role checker for role based things, plus a auth router with POSTs for register and Login. Create a simple UI with plain html pages - for login, register. "
**Результат:** Реализована аутентификация позьзователя, базовая проверка пароля на длину, почты на правильность ввода. Веб интерфейс для входа и регистрации пользователя по email. Шифрование пароля. Документация swagger так же обновилась. Также дополнился файл примера .env (.env.example). Для примера работы приложения, при регистрации можно сразу зарегистрироваться и как админ и как водитель.
### Промпт 3
**Инструмент:** Auto режим в Cursor.
**Промпт:** "Now add CRUD ROUTERS — create separate files routers/orders.py, routers/drivers.py,routers/tariffs.py, routers/payments.py.
Access rules:
orders: create = client only; update status = driver or admin
drivers: create/update/delete = admin only; read = anyone authenticated  
tariffs: write = admin only; read = public
payments: create = client; read = owner or admin
ADMIN ROUTER — routers/admin.py, all routes require require_role("admin"), it should list all users with roles plus a body: {role: "admin"|"client"|"driver"}
REPORTS — routers/reports.py, require authenticated user - GET /reports/summary returns JSON of total orders, revenue by tariff, top drivers and orders per day of last 7 days
DASHBOARD — follow project html style, show all 4 report metrics as plain HTML tables, add nav links to /docs, /admin/users."
**Результат:** Дополнен интерфейс, добавлен функицонал отчета. Создан дашборд, ссылка на swagger докумнтацию. Админ может менять роли пользователей, просматривать список всех пользователей - это может только он. Для заказов пока только backend. Осталось дополнить UI.
### Промпт 4
**Инструмент:** Auto режим в Cursor.
**Промпт:** "Lets finilize app by adding a UI for next elements:
orders (booking,listing orders,details,canceling,driver status), driver(for admin - create and change drivers, for drivers - see assigned orders, toggle availability), tariffs(Admin: manage tariff list/prices; client: pick tariff when ordering. Create 3 tarrifs - simple, medium and lux), profile page (change password, edit name). Follow style of app htmls."
**Результат:** Создал недостающий интерфейс для заказов, водителей, страницы профиля. При тестировании найден баг в приложении, даже если юзер водитель, при переходе на страницу водителя, спустя секунду выкидывает в форму логина. Осталось добавить интерфейс для оплаты заказа. Весь остальной функционал работает как предполагалось. Решение бага описано в CODE_REVIEW.md как часть второго задания. Админ назначает водителй по их id, у каждого водителя есть свой айди + обычный айди пользователя. Таким образом один аккаунт может использоваться как и для заказов, так и для работы.
### Промпт 5
**Инструмент:** Auto режим в Cursor.
**Промпт:** "Add a payment UI for Client users. User should enter payment information when making an order, he should be able to pay only started or done orders. It should be a simulated payment for demonstration. "
**Результат:** Реализован интерфейс для оплаты. Клиент может сделать это либо при публикации заказа на поездку, либо при изменении статуса на Завершено.
### Итого
- Количество промптов: 6
- Что пришлось исправлять вручную: .env файл, баг с панелью водителя.
- Время: ~ 2 часа
---

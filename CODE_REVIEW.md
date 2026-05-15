### Проблема 1
## Вылет на страницу регистрации при заходе на вкладку водителей.
Любая ошибка внутри onReady() попадала во внешний catch, который удалял токен из localStorage и перенаправлял на /login. Таким образом, даже обычная ошибка 404 от GET /drivers/me (профиль водителя не создан администратором) воспринималась как потеря сессии.
Починил - initPage() теперь очищает токен и редиректит на /login только при 401 от fetchMe(). Ошибки внутри onReady() выводятся на странице, сессия не затрагивается. На странице /drivers ошибка 404 от /drivers/me показывает сообщение с просьбой обратиться к администратору вместо редиректа.

### Проблема 2
## Хардкод JWT в конфиге 
jwt_secret_key: str = "change-me-in-production-use-a-long-random-string" в config.py. В данном случае не является проблемой, так как приложение для лабораторной, однако в реальном мире требуется указать его в .env
Для лаборатроной работы можно заменить на что-то простое по типу 
import secrets
from typing import Optional
jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

### Проблема 3
## Email не нормализирован.
В коде аутентификации есть строка - email=payload.email, для нее example@g.com и Example@g.com это разные записи. Для исправления перед user прописываем: email = payload.email.lower(), и уже в полях самого юзера используем 
просто email=email а не email=payload.email. 

### Проблема 4
## Отсутствие обработки исключений в verify_password
В app/auth.py если hashed_password пустой или None, bcrypt.checkpw() вызовет исключение. Добавим валидацию if not hashed_password: return False,
а также ошибки bcrypt except (ValueError, TypeError): return False

### Проблема 5
## Отсутствие валидации существования Tariff
При создании заказа, нет проверки существования тарифа (tariff_id=payload.tariff_id). Добави проверку - 

tariff = db.get(Tariff, payload.tariff_id)
    if tariff is None:
        raise HTTPException(status_code=404, detail="Tariff not found")

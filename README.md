# Foodgram

Учебный проект (109 когорта) для 18 спринта.
Проект «Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.   


### Использованные технологии:

1. Python 3.12 — язык программирования.
2. Django 4.2.7 — фреймворк для создания веб-приложений.
3. Django REST Framework (DRF) 3.14.0 — библиотека для создания RESTful API на Django.
4. Djoser 2.1.0 — библиотека для управления пользователями через REST API (регистрация, авторизация, сброс пароля и т.п.).

### Установка

- Установите Docker
- Клонируйте репозиторий `git@github.com:Oryshich/foodgram.git`
- введите следующие команды в папке foodgram

```
docker compose up -d
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```

### Особенности запуска

Для чувствительных данных после разворачивания проекта необходимо в корневой папке создать файл .env:

```
# Файл .env
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY=my_super_secret
DEBUG=False
ALLOWED_HOSTS='localhost,51.250.19.156,127.0.0.1,mynewfoodgram.gotdns.ch'
```

## Запуск CI/CD с помощью GitHub Actions (автоматическая доставка и развертывание)

Для корректной работы необходимо ввести в GitHub секретные переменные в
``Settings/Secrets and variables/Actions``:

```YAML
DOCKER_PASSWORD: Ваш пароль от аккаунта на docker
DOCKER_USERNAME: Ваше имя от аккаунта на docker
HOST: IP адрес сервера, на котором Вы хотите развернуть проект
SSH_KEY: закрытый ключ к серверу
SSH_PASSPHRASE: секретная фраза для доступа к закрытому ключу сервера
TELEGRAM_TO: ID Вашего аккаунта в телеграмме
TELEGRAM_TOKEN: токен для теграмм-бота (уведомление об успешном развертывании)
USER: имя пользователя на сервере для автоматического развертывания
```

## Над проектом работали

* разработчик : **Орышич Евгений** - https://github.com/Oryshich
* ревьюер: **Шкода Игорь**

![workflow](https://github.com/oryshich/foodgram/actions/workflows/main.yml/badge.svg)

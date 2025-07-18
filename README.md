# Foodgram

[![CI/CD](https://github.com/frank-stotch/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/frank-stotch/foodgram/actions/workflows/main.yml)

Foodgram — это веб-приложение, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на других авторов. Зарегистрированные пользователи также могут создавать «Список покупок», который поможет собрать все нужные продукты для приготовления выбранных блюд.

## Установка

1. Склонируйте репозиторий:

    ```bash
    git clone https://github.com/frank-stotch/foodgram.git
    cd foodgram
    ```

2. Установите зависимости для бекэнда:

    ```bash
    pip install -r backend/requirements.txt
    ```

3. Для установки зависимостей фронтенда перейдите в папку `frontend` и выполните команду:

    ```bash
    cd frontend
    npm install
    ```

## Запуск проекта

Для локального запуска проекта выполните следующие шаги:

1. В одном терминале примените миграции, загрузите фикстуры и запустите сервер разработки бекэнда:

    ```bash
    cd backend
    python manage.py migrate
    python manage.py import_tags
    python manage.py import_ingredients
    python manage.py runserver
    ```

2. В другом терминале запустите сервер разработки фронтенда:

    ```bash
    cd frontend
    npm start
    ```

Приложение будет доступно по адресу `http://localhost:3000`.

## Документация
Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу. 

По адресу [здесь](http://localhost) изучите фронтенд веб-приложения, а по [тут](http://localhost/api/docs/) — спецификацию API.

## Используемые технологии

- **Backend:**
  - **Django**: 3.2
  - **Django Rest Framework**: 3.13
  - **PostgreSQL**: 13.1
  - **Docker**


## Конфигурация

Для локального развёртывания проекта нет специфических настроек. Для продакшн-окружения потребуется настроить переменные окружения для подключения к базе данных PostgreSQL в файле `.env`, пример есть в репозитории.

## Примеры использования

Примеры действий и API-запросов будут добавлены позже.

## Автор

* Иван Курилов [Frank_Stotch](https://github.com/frank-stotch)
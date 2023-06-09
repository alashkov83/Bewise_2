# Проект PigWav

## Техническое задание
Необходимо реализовать веб-сервис, выполняющий следующие функции:
1. Создание пользователя
2. Для каждого пользователя - сохранение аудиозаписи в формате wav, преобразование её в формат mp3 и запись в базу данных
 и предоставление ссылки для скачивания аудиозаписи.

**Детализация задачи:**

1. С помощью Docker (предпочтительно - docker-compose) развернуть образ с любой опенсорсной СУБД (предпочтительно - PostgreSQL). 
Предоставить все необходимые скрипты и конфигурационные (docker/compose) файлы для развертывания СУБД, а также инструкции 
для подключения к ней. Необходимо обеспечить сохранность данных при рестарте контейнера (то есть - использовать volume-ы для хранения файлов СУБД
на хост-машине.
2. Реализовать веб-сервис со следующими REST методами:
   1. Создание пользователя, POST:
      1. Принимает на вход запросы с именем пользователя; 
      2. Создаёт в базе данных пользователя заданным именем, так же генерирует уникальный идентификатор пользователя и UUID токен доступа (в виде строки) для данного пользователя; 
      3. Возвращает сгенерированные идентификатор пользователя и токен. 
   2. Добавление аудиозаписи, POST:
      1. Принимает на вход запросы, содержащие уникальный идентификатор пользователя, токен доступа и аудиозапись в формате wav; 
      2. Преобразует аудиозапись в формат mp3, генерирует для неё уникальный UUID идентификатор и сохраняет их в базе данных;
      3. Возвращает URL для скачивания записи вида "http://host:port/record?id=id_записи&user=id_пользователя".
   3. Доступ к аудиозаписи, GET:
      1. Предоставляет возможность скачать аудиозапись по ссылке из п 2.2.3.
3. Для всех сервисов метода должна быть предусмотрена предусмотрена обработка различных ошибок, возникающих при выполнении запроса, с возвращением соответствующего HTTP статуса. 
4. Модель данных (таблицы, поля) для каждого из заданий можно выбрать по своему усмотрению. 
5. В репозитории с заданием должны быть предоставлены инструкции по сборке докер-образа с сервисами из пп. 2. и 3., их настройке и запуску. А также пример запросов к методам сервиса. 
6. Желательно, если при выполнении задания вы будете использовать docker-compose, SQLAlchemy,  пользоваться аннотацией типов.

## Стек технологий

- Язык: Python 3 (CPython)
- БД: PostgreSQL
- Фрейморк: Flask
- ORM: SQLAalchemy
- Среда контейнеров: Docker(docker-compose)

## Инструкция по сборке и запуску
Для удобства работы сервис включен в оркестратор вместе с ДБ и pgAdmin4 (Для просмотра ДБ). На уровне оркестратора они объединены в одну сеть. В качестве веб-сервера используется отладочный сервер Flask, поэтому данную установку не рекомендуется использовать в проде при серьёзных нагрузках и из за проблем с безопасностью. Сервис стартует (по-умолчанию) на порту 8080.

- Старт сервиса (с БД и pgAdmin):

```bash
docker-compose --profile apiapp up -d
```
**Для правильного формирования ссылки для закачки файла используются настройки переменных сред контейнера API_HOSTNAME и API_PORT.**

- Старт только БД:

```bash
docker-compose --profile only_db up -d
```

- Старт БД и pgAdmin:

```bash
docker-compose --profile admin_db up -d
```

В папке запуска при этом будут созданы папки для хранения данных БД, настроек БД и pgAdmin.

- Проверка работы:

```bash
docker-compose ps
```

__В контейнер встроена также дополнительная проверка состояния БД.__

- Просмотр логов:

```bash
docker-compose logs
```

Для ручной сборки и запуска контейнера только с сервисом можно использовать команды:

```bash
sudo docker build -t apiapp_image:latest .
docker run --name apiapp_container --rm -d -p 8080:8080 -e POSTGTRES_SQL_URI=postgresql://pigwavuser:pigwav1234@pigwavdb_container:5432/pigwavdb \
-e API_HOSTNAME=localhost -e API_PORT=8080 apiapp_image:latest
```

**Параметры для аутентификации БД**:
- Имя БД: pigwavdb
- Имя пользователя: pigwavuser
- Пароль БД: pigwav1234 (мастер пароль от pgAdmin тот же) 
- Имя хоста БД для подкючение pgAdmin в контейнере: quizdb_container

## Пример запроса


Для удобства запроса написа скрипт testAPI.py (находится в каталоге проекта)

- Добавление пользователя

```bash
python testAPI.py -m reg_user -u имя_пользователя # Например
python testAPI.py -m reg_user -u testuser
#User ID: 1
#Token: 23e10bfa-ce68-4444-95dd-4af608f2bf47
```

- Добавление записи

```bash
python testAPI.py -m wav_upload -d id_пользователя -t токен_пользователя -i имя_wav_файла # Например
python testAPI.py -m wav_upload -d 1 -t 23e10bfa-ce68-4444-95dd-4af608f2bf47 -i test.wav
# Download link: http://localhost:8080/record?id=afadaeeb-2842-41de-987c-ae31169310b5&user=1
```

- Скачивание записи

```bash
python testAPI.py -m mp3_download -o имя_mp3_файла -a 'ссылка_для_скачивания' # Например
python testAPI.py -m mp3_download -o test.mp3 -a 'http://localhost:8080/record?id=afadaeeb-2842-41de-987c-ae31169310b5&user=1'
```

**Для работы скрипта необходим пакет Python requests**

Параметры командной строки:

```bash
  -h, --help            show this help message and exit
  -m {reg_user,wav_upload,mp3_download}, --mode {reg_user,wav_upload,mp3_download}
                        Режим работы
  -i INPUT, --input INPUT
                        Имя входного файла
  -u USER, --user USER  Имя пользователя
  -d USER_ID, --user_id USER_ID
                        ID пользователя
  -t TOKEN, --token TOKEN
                        Токен доступа или ID записи (uuid)
  -o OUTPUT, --output OUTPUT
                        Имя выходного файла
  -a ADDRESS, --address ADDRESS
                        URI скачивания (для режима mp3_download) или базовый адрес сервиса
```
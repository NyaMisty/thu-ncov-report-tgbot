# THU 2019-nCoV Report Bot

[Click here to try Online](https://t.me/thuncovbot)

## Requirements

- Python3 (dev with 3.8.6)
- pip

Run `pip install -r requirements.txt` to install required components.

## Deployment

1. Copy `include/config.example.py` to `include/config.py`.
2. Fill `TG_BOT_TOKEN`, `TG_BOT_MASTER` in `include/config.py` with your own bot token and administrator's telegram userid.
3. Run `python main.py --initdb` **once** to initialize SQLite database (my_app.db).
4. Run `python main.py` to start the bot. 

By default, the bot will checkin all the normal accounts at 0:10 *UTC+8*, and retry the failed ones at 0:25.
You can change this behavior in `include/config.py`.

## How it works

Following step are proceed when checkin. 

1. Extracts "dcstr" text/tpl section from form HTML, which contains form template info
2. Parse dcstr and retriving the previously input value (preset)
3. Resolve databind and presetbind infos, and generate the final form data
5. Post final data to form API.

## Contributing

Pull requests and issues are always welcome.

## Credit

Special thanks to [HenryzhaoH/bupt-ncov-report-tgbot](https://github.com/HenryzhaoH/bupt-ncov-report-tgbot).
Special thanks to [ipid/bupt-ncov-report](https://github.com/ipid/bupt-ncov-report).

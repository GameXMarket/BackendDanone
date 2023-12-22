# Backend

Local installation && Startup
-----------------------------

Required:

* PostgreSQL, Tested on version 16
* PowerShell, Tested on version 5.1, 7.3 / Bash Tested on version 5.1.16(1)-release
* Python and pip in PATH, Tested on 3.11.4, pip 23.3.1

Installation:

1. Create local environment:
    ```shell
    python -m venv Venv && .\Venv\Scripts\Activate.ps1
    ```
2. Install dependencies:
    ```shell
    pip install -r .\requirements.txt
    ```
3. Copy and fill in the configuration.example.py file:
    ```shell
    cp example.env .env
    ```

Startup:

1. Fill it out .env file
2. Run main.py file
    ```shell
    python .\main.py
    ```


Debug
-----

...

Deploying
---------

...

The systemd file to run the application

```shell
[Unit]
Description=DanoneMarket systemd file
After=nginx.target

[Service]
Type=simple
ExecStart=... #/bin/bash -c ''
Restart=on-failure
RestartSec=3

[Install]
WantedBy=... #multi-user.target
```


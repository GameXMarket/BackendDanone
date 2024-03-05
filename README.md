# Backend

Local installation && Startup
-----------------------------

Required:

* PostgreSQL, Tested on version 16
* PowerShell, Tested on version 5.1, 7.3 / Bash Tested on version 5.1.16(1)-release
* Python and pip in PATH, Tested on 3.10, 3.11, 3.12, pip 23.3.1

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
Description=DanoneBeckend

[Service]
Type=simple
ExecStart=/bin/bash -c '/dir_to_proj/BackendDanone/Venv/bin/python /dir_to_proj/BackendDanone/main.py'
Restart=always
RestartSec=3
User=danone

[Install]
WantedBy=multi-user.target```


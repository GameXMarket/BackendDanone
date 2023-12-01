# Backend

# The main development is carried out in the dev branch!

Local installation && Startup
-----------------------------

Required:

* PowerShell, Tested on version 5.1, 7.3
* Python 3.11 and pip in PATH
* FastApi - 3.8+ python
* uvicorn[standard] - 3.8+ python, (this will install uvicorn with "Cython-based" dependencies (where possible) and other ["optional extras"](https://www.uvicorn.org/#:~:text=This%20will%20install%20uvicorn%20with%20%22Cython%2Dbased%22%20dependencies%20(where%20possible)%20and%20other%20%22optional%20extras%22))
* SQLAlchemy - Python3 compatible versions of PyPy
* python-multipart - ...
* python-jose[cryptography] - ...
* passlib[bcrypt] - ...

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
    cp configuration.example.py configuration.py
    ```

Startup:

1. Run main.py file
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


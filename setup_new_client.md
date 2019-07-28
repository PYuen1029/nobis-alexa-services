**This is assuming that you already have set up your developer environment in terms of installing packages.**

IP Address: 45.63.18.122

1. first create a new directory and create a virtualenv in it. See https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-ubuntu-16-04
`python3 -m venv env`

2. set it up as a git repo. see https://medium.com/29-degrees/setup-a-git-repository-on-a-shared-hostgator-account-7a7e306ef66f
    ```
    git remote add phillipyuen ssh://admin@45.63.18.122/home/admin/phillipyuen git push -u phillipyuen master
    ```

    * all client directories will receive the same code/git repo pushed to it. What allows differentiation of services (possible feature) and any user-specific information will be stored in databases. This will eventually include config stuff if it comes to that
3. pip install requirements
    * install pip packages: `pip install -r requirements.txt`
    * installing flask ask presents an obstacle
        - pip install pip==9.0.3 fixes it
    * the famous lib is missing requirement x509.3 bullshit: `pip install 'cryptography==2.1.4'`
4. set up the database using alexa_dump.sql. This will be differentiated going forward
    * setup phillip.db by running 
        ```
        sudo sqlite3 phillip.db. 
        .read alexa_dump.sql
        ```
5. create the wsgi file (see https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04)
    ```wsgi.py
    from alexa import app

    if __name__ == "__main__":
        app.run()
    ```
6. create systemd/system service file:
    ```
    [Unit]
    Description=Gunicorn instance to serve johnyuen
    After=network.target

    [Service]
    User=admin
    Group=www-data
    WorkingDirectory=/home/admin/johnyuen
    Environment="PATH=/home/admin/johnyuen/env/bin"
    ExecStart=/home/admin/johnyuen/env/bin/gunicorn --workers 3 --bind unix:johnyuen.sock -m 007 wsgi:app --access-logfile /home/admin/johnyuen/access.log --error-logfile /home/admin/johnyuen/error.log

    [Install]
    WantedBy=multi-user.target
    ```
7. configure nginx sites-available server
    ```
    server {

        server_name johnyuen.nobisalexa.services;

        root /home/admin/johnyuen;

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/admin/johnyuen/johnyuen.sock;
        }
    }
    ```
    * don't forget to link the file to sites-enabled
    ```
    sudo ln -s /etc/nginx/sites-available/johnyuen /etc/nginx/sites-enabled
    ```

8. configure ssh (see https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04)
    ```
    sudo certbot --nginx -d johnyuen.nobisalexa.services
    ```
    * use option 2, redirect
9. make sure to restart nginx, johnyuen.service, and do spot check.
10. Set up their alexa developer portal
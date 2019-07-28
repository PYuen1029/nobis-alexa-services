https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-16-04

https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-ubuntu-16-04

check out https://albertogrespan.com/blog/running-multiple-domains-or-subdomains-in-nginx-with-server-blocks/

so i might need to set up a domain name instead of just using the ip address. Then I can do subdomains. In case, and it seems possible that using different url paths won't work.

subdomains was done by doing wildcard subdomains on namecheap/whatever domain registrar you're using. I used https://www.namecheap.com/support/knowledgebase/article.aspx/597/10/how-can-i-set-up-a-catchall-wildcard-subdomain

then ii just had to change my sites-available to:
```
server {
        listen 80;

        server_name phillipyuen.nobisalexa.services;

        root /home/admin/phillipyuen;

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/admin/phillipyuen/phillipyuen.sock;
        }
}
```

**remember to link it to sites enabled**:
```
sudo ln -s /etc/nginx/sites-available/test /etc/nginx/sites-enabled/
```

restart phillipyuen and nginx services

onve youve set up your environment, yiu use git to push up the alexa service. add a file for wsgi. add a file to systemd/system. add a sites available server block. link it to enabled. 

use https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04 to enable ssh on a website

sudo certbot --nginx -d phillipyuen.nobisalexa.services

in the systemd/system file, you should set up logging in ../error.log, or something. The problem was the user didn't have privileges in /var/log/phillipyuen
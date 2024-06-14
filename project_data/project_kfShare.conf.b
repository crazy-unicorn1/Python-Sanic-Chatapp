server {
    listen 80;
    server_name easychat.pro www.easychat.pro;
    # server_name www.easychat.one easychat.one;
    root /www/project_kfShare;

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:5021;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 600M;
        client_body_buffer_size 600M;
        proxy_buffers   4 32k;
        proxy_buffer_size 64k;
        proxy_busy_buffers_size 64k;
    }

    location /static {
        alias /www/project_kfShare/static;
        expires 30d;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires 0;
    }

    location /socket.io {
        include proxy_params;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_pass http://127.0.0.1:5021/socket.io;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 20M;
        client_body_buffer_size 20M;
    }
}
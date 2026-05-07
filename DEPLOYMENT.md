# Autoflow 部署文档

完整的部署指南，支持 Docker、云服务器、Heroku 等多种部署方式。

---

## 📦 部署前检查清单

- [ ] Python 3.12+ 已安装
- [ ] OpenAI API Key 已获取且有充足余额
- [ ] 项目代码已推送到 GitHub (https://github.com/xuan599/Autoflow)
- [ ] 所有依赖已安装（`requirements.txt`）
- [ ] `.env` 文件已正确配置
- [ ] （可选）Docker 已安装

---

## 🐳 Docker 部署（推荐）

### 1. 创建 Dockerfile

在项目根目录创建 `Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

### 2. 创建 .dockerignore

```
venv/
__pycache__/
*.pyc
.env
output/
test_*/
.git/
.gitignore
*.md
docs/
```

### 3. 构建 Docker 镜像

```bash
docker build -t autoflow:latest .
```

### 4. 运行 Docker 容器

```bash
docker run -d \
  --name autoflow \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your_api_key_here \
  autoflow:latest
```

### 5. 验证部署

```bash
# 查看日志
docker logs -f autoflow

# 访问应用
curl http://localhost:8501
```

---

## ☁️ 云服务器部署（以阿里云/腾讯云为例）

### 1. 服务器准备

| 配置项 | 最低要求 | 推荐配置 |
|--------|---------|---------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 带宽 | 1Mbps | 5Mbps |
| 系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

### 2. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.12
sudo apt install -y python3.12 python3.12-venv python3-pip

# 安装 Git
sudo apt install -y git

# 安装 Nginx（反向代理）
sudo apt install -y nginx
```

### 3. 克隆项目

```bash
cd /opt
sudo git clone https://github.com/xuan599/Autoflow.git
cd Autoflow

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
sudo nano .env
```

填入：
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o
```

### 5. 创建 Systemd 服务

创建 `/etc/systemd/system/autoflow.service`：

```ini
[Unit]
Description=Autoflow Streamlit Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Autoflow
Environment="PATH=/opt/Autoflow/venv/bin"
ExecStart=/opt/Autoflow/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start autoflow
sudo systemctl enable autoflow

# 查看状态
sudo systemctl status autoflow
```

### 6. 配置 Nginx 反向代理

编辑 `/etc/nginx/sites-available/autoflow`：

```nginx
server {
    listen 80;
    server_name your_domain.com;  # 替换为你的域名或IP

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（Streamlit 需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/autoflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. 配置 HTTPS（可选但推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com
```

---

## 🚀 Heroku 部署

### 1. 创建 Procfile

```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

### 2. 创建 setup.sh（可选）

```bash
mkdir -p setup
cat > setup.sh << 'EOF'
#!/bin/bash
pip install -r requirements.txt
EOF
chmod +x setup.sh
```

### 3. 部署到 Heroku

```bash
# 登录 Heroku
heroku login

# 创建应用
heroku create autoflow-app

# 设置环境变量
heroku config:set OPENAI_API_KEY=your_api_key_here

# 推送代码
git push heroku main

# 打开应用
heroku open
```

---

## 🔧 环境变量配置

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API 密钥 | `sk-...` |
| `OPENAI_BASE_URL` | ❌ | API 基础URL | `https://api.openai.com/v1` |
| `MODEL_NAME` | ❌ | 使用的模型 | `gpt-4o` |
| `MAX_RETRY_TIMES` | ❌ | 最大重试次数 | `3` |
| `MAX_CLARIFY_ROUNDS` | ❌ | 最大澄清轮数 | `5` |
| `OUTPUT_DIR` | ❌ | 输出目录 | `output` |

---

## 🚨 常见问题

### 1. Streamlit 无法访问

**问题**：部署后无法通过浏览器访问

**解决**：
```bash
# 确保绑定到 0.0.0.0
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# 检查防火墙
sudo ufw allow 8501
```

### 2. OpenAI API 调用失败

**问题**：`AuthenticationError` 或 `RateLimitError`

**解决**：
- 检查 API Key 是否正确
- 检查 API 余额是否充足
- 检查网络是否能访问 `api.openai.com`
- 如需代理：
  ```bash
  export HTTPS_PROXY=http://proxy:port
  ```

### 3. 内存不足

**问题**：`MemoryError` 或容器被 Kill

**解决**：
- 增加服务器内存（最低 4GB）
- 减少并行任务（修改 `orchestrator.py` 中的并发逻辑）

### 4. 中文显示乱码

**问题**：Linux 服务器上中文显示为乱码

**解决**：
```bash
# 安装中文字体
sudo apt install -y fonts-noto-cjk

# 设置环境变量
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

---

## 📊 监控 & 日志

### Docker 部署

```bash
# 查看实时日志
docker logs -f autoflow

# 查看资源使用
docker stats autoflow
```

### Systemd 服务

```bash
# 查看日志
sudo journalctl -u autoflow -f

# 查看服务状态
sudo systemctl status autoflow
```

### Nginx 日志

```bash
# 访问日志
tail -f /var/log/nginx/access.log

# 错误日志
tail -f /var/log/nginx/error.log
```

---

## 🔒 安全建议

1. **不要将 `.env` 文件提交到 Git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **使用防火墙限制访问**
   ```bash
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

3. **定期更新系统**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **使用 HTTPS**（防止 API Key 泄露）
   - 参考上面的 Certbot 配置

5. **限制 Streamlit 访问**
   - 使用 Nginx 反向代理 + 基础认证
   - 或使用 VPN/内网访问

---

## 📈 性能优化

| 优化项 | 说明 |
|--------|------|
| 使用 Redis 缓存 | 缓存 API 响应，减少重复调用 |
| 调整 Worker 数量 | Streamlit 默认单线程，可考虑多实例 + 负载均衡 |
| 启用 Gzip 压缩 | Nginx 配置 `gzip on;` |
| 使用 CDN | 加速静态资源加载 |

---

## 🎯 部署验证清单

部署完成后，执行以下验证：

- [ ] 访问 `http://your-server:8501` 能看到界面
- [ ] 界面能正常切换中英文
- [ ] 输入测试需求："我想做一个用户积分兑换商品的功能"
- [ ] 能完成 3-5 轮澄清对话
- [ ] 能生成完整的 PRD 文档
- [ ] 能生成技术方案
- [ ] 能生成测试用例
- [ ] 能生成风险评估报告
- [ ] 能下载 Markdown 和 JSON 文件
- [ ] （可选）重启服务后能加载历史会话

---

## 📞 支持

- **项目地址**：https://github.com/xuan599/Autoflow
- **Issues**：https://github.com/xuan599/Autoflow/issues
- **作者**：Xuan (2717485102@qq.com)

---

**部署完成后，请访问你的应用并验证所有功能是否正常！ 🎉**

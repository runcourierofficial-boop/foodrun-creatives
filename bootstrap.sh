#!/usr/bin/env bash
# Food Run agency VPS bootstrap (Ubuntu 24.04). Idempotent. Run as root:
#   curl -sL https://raw.githubusercontent.com/runcourierofficial-boop/foodrun-creatives/main/bootstrap.sh | bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
APP_USER=agency
REPO_SSH=git@github.com:runcourierofficial-boop/foodrun-agency.git
APP_DIR=/opt/foodrun-agency

echo "== packages"
apt-get update -qq
apt-get install -y -qq ufw fail2ban git curl ca-certificates gnupg unattended-upgrades python3 python3-venv python3-pip ffmpeg fonts-inter >/dev/null

echo "== firewall + fail2ban + auto security updates"
ufw --force reset >/dev/null
ufw default deny incoming >/dev/null; ufw default allow outgoing >/dev/null
ufw allow 22/tcp >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null
systemctl enable --now fail2ban >/dev/null 2>&1 || true
dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true

echo "== docker"
if ! command -v docker >/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq && apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
fi
systemctl enable --now docker >/dev/null

echo "== app user + ssh hardening"
id -u $APP_USER >/dev/null 2>&1 || adduser --disabled-password --gecos "" $APP_USER
usermod -aG docker $APP_USER
mkdir -p /home/$APP_USER/.ssh && cp -n /root/.ssh/authorized_keys /home/$APP_USER/.ssh/authorized_keys 2>/dev/null || true
chown -R $APP_USER:$APP_USER /home/$APP_USER/.ssh && chmod 700 /home/$APP_USER/.ssh && chmod 600 /home/$APP_USER/.ssh/authorized_keys 2>/dev/null || true
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl reload ssh || systemctl reload sshd || true

echo "== deploy key (server pulls from GitHub)"
sudo -u $APP_USER bash -c '[ -f ~/.ssh/deploy_key ] || ssh-keygen -t ed25519 -N "" -C "foodrun-agency-vps" -f ~/.ssh/deploy_key -q'
sudo -u $APP_USER bash -c 'grep -q "github.com" ~/.ssh/config 2>/dev/null || printf "Host github.com\n  IdentityFile ~/.ssh/deploy_key\n  IdentitiesOnly yes\n  StrictHostKeyChecking accept-new\n" >> ~/.ssh/config'
mkdir -p $APP_DIR && chown $APP_USER:$APP_USER $APP_DIR

echo "== auto-deploy (pull every minute, restart on change)"
cat > /usr/local/bin/agency-deploy <<'EOF'
#!/usr/bin/env bash
set -e
APP_DIR=/opt/foodrun-agency
REPO=git@github.com:runcourierofficial-boop/foodrun-agency.git
if [ ! -d $APP_DIR/.git ]; then git clone -q $REPO $APP_DIR || exit 0; cd $APP_DIR; else cd $APP_DIR; fi
OLD=$(git rev-parse HEAD 2>/dev/null || echo none)
git fetch -q origin main && git reset -q --hard origin/main
NEW=$(git rev-parse HEAD)
if [ "$OLD" != "$NEW" ] || [ ! -f .deployed ]; then
  [ -x deploy/up.sh ] && ./deploy/up.sh
  echo "$NEW $(date -u +%FT%TZ)" > .deployed
  echo "deployed $NEW"
fi
EOF
chmod +x /usr/local/bin/agency-deploy
cat > /etc/systemd/system/agency-deploy.service <<EOF
[Unit]
Description=Food Run agency auto-deploy
[Service]
Type=oneshot
User=$APP_USER
ExecStart=/usr/local/bin/agency-deploy
EOF
cat > /etc/systemd/system/agency-deploy.timer <<'EOF'
[Unit]
Description=Run agency-deploy every minute
[Timer]
OnBootSec=30
OnUnitActiveSec=60
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload && systemctl enable --now agency-deploy.timer >/dev/null

echo
echo "================ DONE ================"
echo "Add this DEPLOY KEY (read-only) to GitHub repo runcourierofficial-boop/foodrun-agency -> Settings -> Deploy keys:"
echo
cat /home/$APP_USER/.ssh/deploy_key.pub
echo
echo "After that, the server pulls main every minute and runs deploy/up.sh on change."

# Container smoke test

Validate ShellForgeAI in Docker with read-only ops behavior and optional Codex model assist.

## Basic runtime smoke
```bash
cd /srv/compose/shellforgeai
sudo docker exec -it shellforgeai shellforgeai doctor
sudo docker exec -it shellforgeai shellforgeai inspect host
sudo docker exec -it shellforgeai shellforgeai tools list
sudo docker exec -it shellforgeai shellforgeai diagnose disk --save-plan
sudo docker exec -it shellforgeai shellforgeai audit list
```

## Codex install (Debian container)
```bash
sudo docker exec -u 0 -it shellforgeai sh -lc '
mkdir -p /var/lib/apt/lists/partial
apt-get update
apt-get install -y --no-install-recommends nodejs npm ca-certificates
npm install -g @openai/codex
command -v codex
codex --version
'
```

## Codex auth + model smoke
```bash
sudo docker exec -it shellforgeai codex login --device-auth
sudo docker exec -it shellforgeai shellforgeai model doctor
sudo docker exec -it shellforgeai shellforgeai model test
sudo docker exec -it shellforgeai shellforgeai ask "In one sentence, what is ShellForgeAI?"
sudo docker exec -it shellforgeai shellforgeai diagnose disk --model --save-plan
sudo docker exec -it shellforgeai shellforgeai diagnose network --model --save-plan
```

## Apply safety test
```bash
sudo docker exec -it shellforgeai shellforgeai apply /data/artifacts/<session-id>/plan.json
```
Expected: apply execution is intentionally disabled.

## Persistent Codex auth volume
Never commit `.codex/auth.json`; treat it as a password.

```yaml
services:
  shellforgeai:
    volumes:
      - ./data:/data
      - ./codex-home:/root/.codex
```

Check actual container home:
```bash
sudo docker exec -it shellforgeai sh -lc 'echo $HOME; whoami; id'
```

## Dockerfile snippet
```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm ca-certificates \
    && npm install -g @openai/codex \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

## Interactive check

Validate interactive startup in container:

```bash
shellforgeai
/help
/exit
```

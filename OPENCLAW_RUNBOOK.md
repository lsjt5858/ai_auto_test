# OpenClaw 远程自动化运行手册

## 目标

本项目在本地执行自动化框架，逐条读取测试用例，将用例内容发送到远程 ArkClaw/OpenClaw 主机执行，远程返回结果后，本地完成断言、报告记录，并继续执行下一条 case。

目标链路：

```text
本地 ai_auto_test
  -> SSH 连接远程 ArkClaw/OpenClaw 主机
  -> 远程执行 openclaw agent --agent main -m "<case内容>" --json
  -> Agent 在远程机器执行接口测试
  -> 返回 result.payloads[].text
  -> 本地断言、报告、执行下一条 case
```

## 当前远程机器信息

- 主机名：`arkclaw`
- 登录用户：`root`
- 操作系统：`Ubuntu 24.04 LTS`
- 内网 IP：`172.16.18.43`
- SSH：远程机器内 `sshd` 已监听 `0.0.0.0:22`
- 本机防火墙：`ufw inactive`，`iptables INPUT ACCEPT`
- Python：`Python 3.12.3`
- curl：已安装
- pytest：远程机器未安装
- OpenClaw CLI：`/usr/bin/openclaw`
- OpenClaw 版本：`OpenClaw 2026.4.15`
- 默认 Agent：`main`
- Gateway 健康接口：`http://127.0.0.1:18789/health`

## 已验证的远程 Agent 命令

在远程机器终端执行以下命令已成功：

```bash
openclaw agent --agent main \
  -m "请在当前远程机器上执行接口测试命令：curl -sS -i http://127.0.0.1:18789/health。请返回完整 HTTP 响应，并判断是否包含 ok:true。" \
  --timeout 180 \
  --json
```

关键返回：

```text
HTTP/1.1 200 OK
{"ok":true,"status":"live"}
健康检查通过
```

说明远程 OpenClaw Agent 能在 ArkClaw 机器上执行接口测试命令，并能返回结果。

## 本项目已完成的改造

- 新增 `openclaw://arkclaw` 平台协议。
- 新增 `integrations/openclaw.py`，支持 SSH 登录远程机器。
- 支持 `openclaw_mode: agent`，远程执行 `openclaw agent --agent main -m ... --json`。
- 支持解析 Agent JSON 输出，并提取 `result.payloads[].text` 作为断言内容。
- 更新 `config/skills/openclaw.yaml` 为 `execute_mode: openclaw_agent`。
- 更新 `data/templates/openclaw_cases.json`，包含 OpenClaw Gateway 健康检查和 8080 服务示例。
- 报告中会记录 `stdout`、`stderr`、退出码、Agent JSON、耗时等信息。
- 报告脱敏已覆盖 `PASSWORD`、`TOKEN`、`PRIVATE_KEY`、`PASSPHRASE`。

## 本地验证结果

已通过：

```bash
python -m pytest testcases/test_openclaw_executor.py -q
```

结果：

```text
5 passed
```

已通过：

```bash
python -m pytest -q
```

结果：

```text
11 passed
```

## 当前卡点

本地 Mac 无法 SSH 到当前 ArkClaw 托管机器：

```bash
ssh -i ~/.ssh/id_ed25519 -p 22 root@115.191.51.201
```

返回：

```text
ssh: connect to host 115.191.51.201 port 22: Operation timed out
```

已排除：

- 不是远程机器本机防火墙问题。
- 不是远程 SSH 服务未启动问题。
- 不是公钥未配置问题，本地公钥已写入远程 `/root/.ssh/authorized_keys`。

最可能原因：

- `115.191.x.x` 是 NAT 出口 IP，不是可入站 SSH IP。
- 火山引擎安全组未开放 `TCP 22` 入方向。
- ArkClaw 托管环境只提供 WebShell/Web 远程桌面，不开放公网 SSH。
- 平台外层网络未映射 SSH 到这台机器。

## 如果 SSH 放通后的运行方式

创建 `config/runtime_params.openclaw.json`：

```json
{
  "skills": {
    "openclaw": {
      "OPENCLAW_HOST": "115.191.51.201",
      "OPENCLAW_PORT": "22",
      "OPENCLAW_USERNAME": "root",
      "OPENCLAW_PRIVATE_KEY_FILE": "/Users/bytedance/.ssh/id_ed25519",
      "OPENCLAW_STRICT_HOST_KEY": "false",
      "OPENCLAW_CONNECT_TIMEOUT": "30",
      "OPENCLAW_COMMAND_TIMEOUT": "300",
      "OPENCLAW_MODE": "agent",
      "OPENCLAW_AGENT_NAME": "main",
      "OPENCLAW_AGENT_TIMEOUT": "180"
    }
  }
}
```

先本地验证 SSH：

```bash
ssh -i ~/.ssh/id_ed25519 -p 22 root@115.191.51.201
```

再运行本项目：

```bash
python run.py \
  --runtime-params config/runtime_params.openclaw.json \
  --case-file data/templates/openclaw_cases.json \
  -m smoke \
  --html-report reports/openclaw.html
```

## 如果当前 ArkClaw SSH 卡点无法解决

可选方案：

- 暂时跳过 `openclaw` 远程执行链路，只跑本地接口自动化。
- 将本项目复制到远程机器，在远程机器上运行 `python run.py ...`，绕过本地 SSH 入站问题。
- 使用平台提供的其他通道，例如 WebShell、Feishu channel、Gateway API、反向 SSH、frp、Tailscale，但需要额外实现。
- 重新购买一台可控的火山 ECS，在 ECS 上安装部署 OpenClaw，并开放安全组 `TCP 22`，这是更可控的长期方案。

## 新购火山 ECS 方案

如果购买一台标准火山 ECS，并在上面安装部署 OpenClaw，可以解决当前最大卡点，因为你可以控制：

- 公网 IP 或弹性公网 IP。
- 安全组入方向规则。
- SSH 密钥登录。
- OpenClaw Gateway 端口。
- 被测服务、测试脚本和依赖。

推荐 ECS 配置步骤：

1. 创建 ECS，系统选择 Ubuntu 24.04 或 22.04。
2. 绑定公网 IP 或 EIP。
3. 安全组开放 `TCP 22`，来源建议限制为本地公网 IP `/32`。
4. 将本地公钥加入 ECS 的 `root` 或测试用户 `~/.ssh/authorized_keys`。
5. 本地验证 SSH：

```bash
ssh -i ~/.ssh/id_ed25519 -p 22 root@<ECS公网IP>
```

6. 在 ECS 上安装 OpenClaw，并确认：

```bash
openclaw --version
openclaw gateway status
openclaw agent --agent main -m "请回复 hello_openclaw" --timeout 120 --json
```

7. 修改 `config/runtime_params.openclaw.json` 中的 `OPENCLAW_HOST` 为新 ECS 公网 IP。
8. 运行本项目 `openclaw` case。

这个方案最适合作为稳定自动化执行机。

## 当前建议

优先尝试两条路：

1. 在现有 ArkClaw 托管机器上找到真正可入站的 SSH 入口或开放安全组 `TCP 22`。
2. 如果现有环境无法开放 SSH，则购买一台标准 ECS，自主安装 OpenClaw，作为长期稳定的远程自动化执行机。


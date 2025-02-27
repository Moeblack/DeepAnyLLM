<div>
<h1>DeepAnyLLM 🐬🧠 - OpenAI Compatible（deepclaude & deepgemini）</h1>

<a href="https://github.com/getasterisk/deepclaude"> Inspiration from getasterisk/deepclaude</a>

<a href="https://github.com/ErlichLiu/DeepClaude"> Edit on ErlichLiu/deepclaude</a>


[![GitHub license](https://img.erlich.fun/personal-blog/uPic/deepclaude.svg)](#)
[![Compatible with](https://img.shields.io/badge/-ChatGPT-412991?style=flat-square&logo=openai&logoColor=FFFFFF)](https://openai.com)

</div>

<div>
<h4 style="color: #FF9909"> 特别说明：本项目完全基于[ErlichLiu/deepclaude](https://github.com/ErlichLiu/DeepClaude)的低创作品，目的仅为了方便自己使用各种不同的LLM搭配R1思维链使用
<br />
</h4>
</div>

<details>
<summary><strong>更新日志：</strong></summary> 
<div>
2025-02-27.1: 弃用`OPENAI_COMPOSITE_MODEL`环境变量

2025-02-25.1: 添加 system message 对于 Claude 3.5 Sonnet 的支持

2025-02-23.1: 重构代码，支持 OpenAI 兼容模型，deepgeminiflash 和 deepgeminipro 配置更方便（请详细查看 READEME 和 .env.example 内的说明）。

2025-02-21.1: 添加 Claude 这段的详细数据结构安全检查。

2025-02-16.1: 支持 claude 侧采用请求体中的自定义模型名称。（如果你采用 oneapi 等中转方，那么现在可以通过配置环境变量或在 API 请求中采用任何 Gemini 等模型完成后半部分。接下来将重构代码，更清晰地支持不同的思考模型组合。）

2025-02-08.2: 支持非流式请求，支持 OpenAI 兼容的 models 接口返回。（⚠️ 当前暂未实现正确的 tokens 消耗统计，稍后更新）

2025-02-08.1: 添加 Github Actions，支持 fork 自动同步、支持自动构建 Docker 最新镜像、支持 docker-compose 部署

2025-02-07.2: 修复 Claude temperature 参数可能会超过范围导致的请求失败的 bug

2025-02-07.1: 支持 Claude temputerature 等参数；添加更详细的 .env.example 说明

2025-02-06.1：修复非原生推理模型无法获得到推理内容的 bug

2025-02-05.1: 支持通过环境变量配置是否是原生支持推理字段的模型，满血版本通常支持

2025-02-04.2: 支持跨域配置，可在 .env 中配置

2025-02-04.1: 支持 Openrouter 以及 OneAPI 等中转服务商作为 Claude 部分的供应商

2025-02-03.3: 支持 OpenRouter 作为 Claude 的供应商，详见 .env.example 说明

2025-02-03.2: 由于 deepseek r1 在某种程度上已经开启了一个规范，所以我们也遵循推理标注的这种规范，更好适配支持的更好的 Cherry Studio 等软件。

2025-02-03.1: Siliconflow 的 DeepSeek R1 返回结构变更，支持新的返回结构

</div>
</details>

---

<details>
<summary><strong>简介</strong></summary>
最近 DeepSeek 推出了 [DeepSeek R1 模型](https://platform.deepseek.com)，在推理能力上已经达到了第一梯队。但是 DeepSeek R1 在一些日常任务的输出上可能仍然无法匹敌 Claude 3.5 Sonnet。Aider 团队最近有一篇研究，表示通过[采用 DeepSeek R1 + Claude 3.5 Sonnet 可以实现最好的效果](https://aider.chat/2025/01/24/r1-sonnet.html)。

<img src="https://img.erlich.fun/personal-blog/uPic/heiQYX.png" alt="deepseek r1 and sonnet benchmark" style="width=400px;"/>

> **R1 as architect with Sonnet as editor has set a new SOTA of 64.0%** on the [aider polyglot benchmark](https://aider.chat/2024/12/21/polyglot.html). They achieve this at **14X less cost** compared to the previous o1 SOTA result.

本项目受到该项目的启发，通过 fastAPI 完全重写.

项目**支持 OpenAI 兼容格式的输入输出**，支持 DeepSeek 官方 API 以及第三方托管的 API、生成部分也支持 Claude 官方 API 以及中转 API，并对 OpenAI 兼容格式的其他 Model 做了特别支持。

</details>

# Implementation

![image-20250201212456050](https://img.erlich.fun/personal-blog/uPic/image-20250201212456050.png)

# How to run

> 项目支持本地运行和服务器运行，推荐使用服务器部署，实现随时随处可访问的最强大语言模型服务，甚至可以完全免费使用。

## 1. 获得运行所需的 API

1.  获取 DeepSeek API：https://platform.deepseek.com
2.  获取 Claude 的 API KEY：https://console.anthropic.com。(也可采用其他中转服务，如 Openrouter 以及其他服务商的 API KEY)
3.  获取 Gemini 的 API KEY：https://aistudio.google.com/apikey (有免费的额度，日常够用)

## 2. 开始运行（本地运行）

Step 1. 克隆本项目到适合的文件夹并进入项目

```bash
git clone https://github.com/Moeblack/DeepAnyLLM.git
cd DeepAnyLLM
```

Step 2. 通过 uv 安装依赖（如果你还没有安装 uv，请看下方注解）

```bash
# 通过 uv 在本地创建虚拟环境，并安装依赖
uv sync
# macOS 激活虚拟环境
source .venv/bin/activate
# Windows 激活虚拟环境
.venv\Scripts\activate
```

Step 3. 配置环境变量
```bash
# 复制 .env 环境变量到本地
cp .env.example .env
```

Step 4. 按照环境变量当中的注释依次填写配置信息
```bash
# 此处为各个环境变量的解释
ALLOW_API_KEY=你允许向你本地或服务器发起请求所需的 API 密钥，可随意设置
DEEPSEEK_API_KEY=deepseek r1 所需的 API 密钥，可在👆上面步骤 1 处获取
DEEPSEEK_API_URL=请求 deepseek r1 所需的请求地址，根据你的供应商说明进行填写
DEEPSEEK_MODEL=不同供应商的 deepseek r1 模型名称不同，根据你的供应商说明进行填写
IS_ORIGIN_REASONING=是否原生支持推理，只有满血版 671B 的 deepseek r1 支持，其余蒸馏模型不支持

CLAUDE_API_KEY=Claude 3.5 Sonnet 的 API 密钥，可在👆上面步骤 1 处获取
CLAUDE_MODEL=Claude 3.5 Sonnet 的模型名称，不同供应商的名称不同，根据你的供应商说明进行填写
CLAUDE_PROVIDER=支持 anthropic (官方) 以及 oneapi（其他中转服务商）两种模式，根据你的供应商填写
CLAUDE_API_URL=请求 Claude 3.5 Sonnet 所需的请求地址，根据你的供应商说明进行填写

# OPENAI兼容模型
# 使用非deepclaude模型的时候可以传入任意openai兼容格式的模型名, 会自动附加上deepseek-R1思维链
OPENAI_COMPOSITE_API_KEY=your_api_key
OPENAI_COMPOSITE_API_URL=your_openai_baseurl
# 已弃用 OPENAI_COMPOSITE_MODEL 字段，模型名称将直接使用请求中传入的名称。

```

Step 5. 通过命令行启动
```bash
# 本地运行
uvicorn app.main:app
```
---
如果公开到局域网或自定义端口号
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Step 6. 配置程序到你的 Chatbox

```bash
# 如果你的客户端是 Cherry Studio、Chatbox（OpenAI API 模式，注意不是 OpenAI 兼容模式）
# API 地址为 http://127.0.0.1:8000
# API 密钥为你在 ENV 环境变量内设置的 ALLOW_API_KEY

# 如果你的客户端是 LobeChat
# API 地址为：http://127.0.0.1:8000/v1
# API 密钥为你在 ENV 环境变量内设置的 ALLOW_API_KEY

```

**注：本项目采用 uv 作为包管理器，这是一个更快速更现代的管理方式，用于替代 pip，你可以[在此了解更多](https://docs.astral.sh/uv/)**

# 部署到服务器

> 项目支持 Docker 服务器部署，可自行调用接入常用的 Chatbox，也可以作为渠道一直，将其视为一个特殊的 `DeepClaude`模型接入到 [OneAPI](https://github.com/songquanpeng/one-api) 等产品使用。

## Docker 部署（自行 Build）

1. **构建 Docker 镜像**

   在项目根目录下，使用 Dockerfile 构建镜像。请确保已经安装 Docker 环境。

   ```bash
   docker build -t deepclaude:latest .
   ```

2. **运行 Docker 容器**

   运行构建好的 Docker 镜像，将容器的 8000 端口映射到宿主机的 8000 端口。同时，通过 `-e` 参数设置必要的环境变量，包括 API 密钥、允许的域名等。请根据 `.env.example` 文件中的说明配置环境变量。

   ```bash
   docker run -d \
       -p 8000:8000 \
       -e ALLOW_API_KEY=your_allow_api_key \
       -e ALLOW_ORIGINS="*" \
       -e DEEPSEEK_API_KEY=your_deepseek_api_key \
       -e DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions \
       -e DEEPSEEK_MODEL=deepseek-reasoner \
       -e IS_ORIGIN_REASONING=true \
       -e CLAUDE_API_KEY=your_claude_api_key \
       -e CLAUDE_MODEL=claude-3-5-sonnet-20241022 \
       -e CLAUDE_PROVIDER=anthropic \
       -e CLAUDE_API_URL=https://api.anthropic.com/v1/messages \
       -e OPENAI_COMPOSITE_API_KEY=your_gemini_api_key
       -e OPENAI_COMPOSITE_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
       -e LOG_LEVEL=INFO \
       --restart always \
       DeepAnyLLM:latest
   ```

   请替换上述命令中的 `your_allow_api_key`，`your_allow_origins`，`your_deepseek_api_key` 和 `your_claude_api_key` 为你实际的 API 密钥和配置。`ALLOW_ORIGINS` 请设置为允许访问的域名，如 `"http://localhost:3000,https://chat.example.com"` 或 `"*"` 表示允许所有来源。
   **注意：已弃用 `OPENAI_COMPOSITE_MODEL` 环境变量。模型名称将直接使用请求中传入的 OpenAI 兼容模型名称。**

# Automatic fork sync
项目已经支持 Github Actions 自动更新 fork 项目的代码，保持你的 fork 版本与当前 main 分支保持一致。如需开启，请 frok 后在 Settings 中开启 Actions 权限即可。


# Technology Stack
- [FastAPI](https://fastapi.tiangolo.com/)
- [UV as package manager](https://docs.astral.sh/uv/#project-management)
- [Docker](https://www.docker.com/)

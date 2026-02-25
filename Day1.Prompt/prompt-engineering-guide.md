# Prompt Engineering 完全指南 —— 后端工程师实战手册

> 面向后端工程师的系统性 Prompt 工程知识梳理，从基础到进阶，包含方法论、结构模板、注意事项与优秀开源资源。

---

## 第一部分：如何写出优秀的 Prompt

### 1.1 Prompt 的四大基本要素

一个完整的 Prompt 通常由以下四个部分组成（不一定全部需要，按需组合）：

| 要素 | 说明 | 示例 |
|------|------|------|
| **Role（角色）** | 告诉模型"你是谁" | `你是一个资深的 Go 后端工程师` |
| **Context（上下文）** | 提供背景信息和约束条件 | `我们的项目使用 Go 1.22 + Gin 框架 + GORM` |
| **Task（任务）** | 明确要求模型做什么 | `请帮我设计一个用户认证中间件` |
| **Format（格式）** | 指定输出的结构和形式 | `用代码块输出，附带注释说明` |

### 1.2 六大核心原则

**原则一：具体而非模糊**

```
❌ 差："帮我写个接口"
✅ 好："帮我用 Go + Gin 框架编写一个 RESTful 用户注册接口，
      接收 JSON body（包含 username, password, email），
      使用 GORM 写入 PostgreSQL，
      返回 201 状态码和创建的用户信息（不包含密码），
      包含参数校验和错误处理"
```

**原则二：使用分隔符/结构化标记**

对 Claude 特别有效的是 XML 标签，对 GPT 则常用 markdown 或三引号：

```xml
<role>你是一个 Kubernetes 运维专家</role>
<context>
生产环境 K8s 1.28, 3 master + 10 worker 节点
最近频繁出现 Pod OOMKilled
</context>
<task>分析可能原因并给出排查步骤</task>
<format>按优先级排列，每个步骤包含具体命令</format>
```

**原则三：提供示例（Few-shot Prompting）**

```
请将以下错误日志分类为 "数据库错误"、"网络错误" 或 "业务逻辑错误"。

示例：
输入: "connection refused to postgres:5432"
分类: 数据库错误

输入: "timeout waiting for response from api.example.com"
分类: 网络错误

现在请分类：
输入: "duplicate key value violates unique constraint"
分类:
```

**原则四：引导逐步思考（Chain-of-Thought）**

```
分析这段 Go 代码的性能瓶颈。请按以下步骤思考：
1. 首先识别代码中的热点路径
2. 分析每个热点的时间/空间复杂度
3. 检查是否有不必要的内存分配
4. 提出优化方案并说明预期效果

<code>
// 你的代码粘贴在这里
</code>
```

**原则五：指定输出格式**

```
请生成一个 Nginx 配置文件，要求：
- 反向代理到 localhost:8080
- 启用 gzip 压缩
- 配置 SSL（证书路径 /etc/ssl/certs/）
- 设置请求速率限制 100r/s

输出格式：直接给出可用的 nginx.conf 配置内容，
用代码块包裹，关键配置项用注释说明。
```

**原则六：迭代优化**

Prompt 工程本质上是一个实验科学，你需要像调试代码一样不断迭代：
- 第一版：写出基本需求
- 第二版：根据输出问题补充约束
- 第三版：加入边界条件和示例
- 第四版：精简冗余，固化为模板

### 1.3 进阶技巧

**技巧 1：Prompt 链式调用（Prompt Chaining）**

将复杂任务拆解为多步，每步一个 Prompt：

```
步骤1 Prompt: "分析这个 API 的安全漏洞"       → 得到漏洞列表
步骤2 Prompt: "针对漏洞 X，生成修复方案"        → 得到修复代码
步骤3 Prompt: "为修复方案编写单元测试"           → 得到测试代码
```

**技巧 2：负面指令（说清楚不要什么）**

```
帮我写一个 Go HTTP 客户端封装。
要求：
- 支持超时设置、重试机制、请求/响应日志
- 不要使用任何第三方库，仅用标准库
- 不要过度抽象，保持简单实用
- 不要加不必要的注释
```

**技巧 3：角色设定的高级用法**

```
你是一个同时精通 Go 和 Rust 的系统工程师。
现在有一段 Go 代码在高并发下出现数据竞争，
请从 Rust 的所有权模型视角分析这段 Go 代码的问题，
并建议用 Go 的方式（channel / sync 包）来解决。
```

**技巧 4：用 XML 结构化复杂 Prompt（Claude 最佳实践）**

```xml
<system>
你是一个 DevOps 自动化专家，擅长 CI/CD 流水线设计。
</system>

<context>
<tech_stack>GitLab CI, Docker, Kubernetes, Harbor</tech_stack>
<current_problem>构建时间过长（平均 15 分钟），需要优化到 5 分钟以内</current_problem>
<constraints>不能更换 CI 平台，镜像仓库必须用内部 Harbor</constraints>
</context>

<task>
设计优化方案，包含：
1. 多阶段构建优化
2. 缓存策略
3. 并行化方案
</task>

<output_format>
对每个方案：简述原理 → 给出具体配置/代码 → 预估优化效果
</output_format>
```

### 1.4 后端工程师常用 Prompt 模板

**代码审查模板：**

```
请审查以下 {语言} 代码，从这些维度评估：
1. 安全性（SQL注入、XSS、敏感信息泄露等）
2. 性能（N+1 查询、内存泄漏、不必要的拷贝）
3. 可维护性（命名规范、函数拆分、错误处理）
4. 并发安全（数据竞争、死锁风险）

对每个问题：指出位置 → 说明风险 → 给出修复代码

<code>
{粘贴代码}
</code>
```

**故障排查模板：**

```
<role>你是一个 SRE 专家</role>
<incident>
- 现象：{描述现象}
- 时间：{发生时间}
- 影响范围：{影响的服务/用户}
- 已有信息：{日志片段、监控截图描述等}
</incident>
<task>
1. 给出可能的根因列表（按概率排序）
2. 对每个根因，给出验证命令
3. 给出临时缓解措施和根本修复方案
</task>
```

**架构设计模板：**

```
请设计 {系统名称} 的架构方案。

背景：{业务场景描述}
核心需求：
- 性能：{QPS/延迟要求}
- 可用性：{SLA 要求}
- 数据量：{预估规模}

约束条件：
- 技术栈：{现有技术栈}
- 团队：{团队规模和技能}
- 预算：{基础设施预算}

请输出：
1. 整体架构图（用文字描述或 mermaid）
2. 核心组件设计
3. 数据流说明
4. 关键技术选型及理由
5. 潜在风险和应对措施
```

### 1.5 注意事项清单

| 类别 | 注意事项 |
|------|---------|
| **准确性** | LLM 会"幻觉"，生成的代码/命令务必验证后再用于生产 |
| **安全性** | 不要在 Prompt 中包含真实的密码、密钥、内部 IP 等敏感信息 |
| **模型差异** | Claude 对 XML 标签响应好；GPT 对 markdown 和 JSON 格式友好；不同模型需要不同调优 |
| **上下文窗口** | 注意模型的 token 限制，大段代码考虑分块发送 |
| **温度参数** | 需要精确输出（代码/配置）时用低温度（0-0.3）；需要创意时用高温度（0.7-1.0） |
| **幂等性** | 同样的 Prompt 可能产生不同输出，关键场景需要多次验证 |
| **版本管理** | 将有效的 Prompt 像代码一样进行版本管理 |
| **成本意识** | 过长的 Prompt 消耗更多 token，在保持效果的前提下尽量精简 |

---

## 第二部分：推荐的开源优秀 Prompt 资源

### 2.1 官方权威资源

| 资源 | 说明 | 链接 |
|------|------|------|
| **Anthropic 官方 Prompt 工程指南** | Claude 最权威的 Prompt 最佳实践文档 | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview |
| **Anthropic Claude Prompting Best Practices** | Claude 4.x 模型最新的 prompting 技巧 | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices |
| **OpenAI Prompt Engineering Guide** | OpenAI 官方最佳实践指南 | https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api |
| **Anthropic Cookbook (GitHub)** | 官方示例 Notebook，含分类、RAG、工具调用等 | https://github.com/anthropics/anthropic-cookbook |
| **Anthropic Interactive Tutorial** | 官方互动式 Prompt 工程教程（9章+练习） | https://github.com/anthropics/prompt-eng-interactive-tutorial |
| **Anthropic Courses** | 官方 API 基础 + Prompt 工程课程 | https://github.com/anthropics/courses |
| **Anthropic Context Engineering** | 官方 Agent 上下文工程博客 | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |

### 2.2 社区高星开源项目

| 项目 | Stars | 说明 | 链接 |
|------|-------|------|------|
| **Awesome ChatGPT Prompts** | 143k+ | 世界最大开源 Prompt 库，适配所有主流模型 | https://github.com/f/awesome-chatgpt-prompts |
| **Prompt Engineering Guide** | — | 最全面的 Prompt 工程学术指南（DAIR.AI 维护） | https://github.com/dair-ai/Prompt-Engineering-Guide |
| **Awesome Prompt Engineering** | — | 精选 Prompt 工程资源集合（论文、工具、数据集） | https://github.com/promptslab/Awesome-Prompt-Engineering |
| **AI System Prompts Collection** | — | 收集了 Cursor、Devin、Claude Code 等 30+ AI 工具的 System Prompt | https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools |
| **Awesome Awesome Prompts** | — | Prompt 相关 Awesome List 的 Awesome List | https://github.com/dukeluo/awesome-awesome-prompts |
| **AI Boost Awesome Prompts** | — | GPT Store 高评分 GPT 的 Prompt 收集 + Prompt 工程论文 | https://github.com/ai-boost/awesome-prompts |

### 2.3 学习网站

| 网站 | 说明 | 链接 |
|------|------|------|
| **promptingguide.ai** | 最全面的 Prompt 工程在线教程，涵盖所有技术和论文 | https://www.promptingguide.ai/ |
| **prompts.chat** | Awesome ChatGPT Prompts 的 Web 版，可在线浏览和贡献 | https://prompts.chat/ |
| **Anthropic Academy** | Anthropic 官方学习路径 | https://www.anthropic.com/learn/build-with-claude |
| **Lakera Prompt Engineering Guide** | 包含安全性视角的完整指南 | https://www.lakera.ai/blog/prompt-engineering-guide |

---

## 第三部分：Prompt 生成工具

见随附的 Python CLI 工具 `prompt_generator.py`，提供：
- 内置后端开发/运维场景的 Prompt 模板
- 交互式 Prompt 构建器
- 模板变量替换
- 支持导出为文件

运行方式：`python prompt_generator.py`

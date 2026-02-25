#!/usr/bin/env python3
"""
CLAUDE.md Generator v2 — 交互式 CLAUDE.md 配置文件生成工具
================================================================

为 Claude Code 生成高质量的 CLAUDE.md 项目配置文件。
支持中英文切换，按角色差异化引导，生成内容可直接驱动 Claude Code 工作。

用法:
  python claudemd_generator.py                    # 交互式菜单
  python claudemd_generator.py wizard              # 交互式向导
  python claudemd_generator.py quick <preset>      # 快速预设
  python claudemd_generator.py quick <preset> --en # 快速预设(英文)
  python claudemd_generator.py presets             # 列出预设
  python claudemd_generator.py example             # 完整示例
  python claudemd_generator.py help                # 帮助

预设: go-api, go-cli, python-api, python-data, devops, fullstack,
      microservice, monorepo, k8s-operator, terraform
"""

import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# ANSI 颜色
# ============================================================================
class C:
    RST = "\033[0m"; B = "\033[1m"; DIM = "\033[2m"
    RED = "\033[31m"; GRN = "\033[32m"; YLW = "\033[33m"
    BLU = "\033[34m"; MAG = "\033[35m"; CYN = "\033[36m"

def c(t, color): return f"{color}{t}{C.RST}"
def hdr(t): return c(f"\n{'='*64}\n  {t}\n{'='*64}", C.CYN + C.B)
def sub(t): return c(f"\n  ── {t} ──", C.YLW)

# ============================================================================
# i18n — 中英文文案系统
# ============================================================================
# 全局语言标记：由 wizard 第一步或 CLI 参数 --en 设置
_LANG = "zh"

def set_lang(lang: str):
    global _LANG
    _LANG = lang

def L(zh: str, en: str) -> str:
    """根据当前语言返回对应文案"""
    return zh if _LANG == "zh" else en

# ============================================================================
# 交互辅助函数
# ============================================================================
def ask(prompt, default=""):
    if default:
        raw = input(f"  {c(prompt, C.CYN)} [{c(default, C.DIM)}]: ").strip()
        return raw if raw else default
    return input(f"  {c(prompt, C.CYN)}: ").strip()

def ask_yn(prompt, default=True):
    hint = "Y/n" if default else "y/N"
    raw = input(f"  {c(prompt, C.CYN)} [{hint}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "是")

def ask_multi(prompt, options, default=None):
    print(f"\n  {c(prompt, C.CYN)}")
    for i, (key, label) in enumerate(options, 1):
        marker = c(" (*)", C.DIM) if default == key else ""
        print(f"    {c(f'[{i}]', C.YLW)} {label}{marker}")
    raw = input(f"  {L('选择序号', 'Choose')}: ").strip()
    if not raw and default:
        return default
    try:
        idx = int(raw) - 1
        return options[idx][0] if 0 <= idx < len(options) else (default or options[0][0])
    except (ValueError, IndexError):
        return default or options[0][0]

def ask_lines(prompt):
    print(f"  {c(prompt, C.CYN)} {c(L('(每行一条，空行结束)', '(one per line, empty to finish)'), C.DIM)}")
    lines = []
    while True:
        line = input("    > ").strip()
        if not line:
            break
        lines.append(line)
    return lines

def ask_cmds(prompt):
    """输入命令对: label=command"""
    print(f"  {c(prompt, C.CYN)} {c(L('(格式: 名称=命令，空行结束)', '(format: label=cmd, empty to finish)'), C.DIM)}")
    print(f"  {c(L('例如: 运行测试=go test ./...', 'e.g.: Run tests=go test ./...'), C.DIM)}")
    cmds = {}
    while True:
        raw = input("    > ").strip()
        if not raw:
            break
        if "=" in raw:
            k, v = raw.split("=", 1)
            cmds[k.strip()] = v.strip()
        else:
            print(f"    {c(L('格式：名称=命令', 'Format: label=cmd'), C.RED)}")
    return cmds


# ============================================================================
# 章节标题 i18n 映射
# ============================================================================
def T(key: str) -> str:
    """返回章节标题"""
    _TITLES = {
        "overview":    L("项目概述", "Project Overview"),
        "role":        L("角色定义", "Role Definition"),
        "tech":        L("技术栈与环境", "Tech Stack & Environment"),
        "structure":   L("项目结构", "Project Structure"),
        "commands":    L("常用命令", "Common Commands"),
        "style":       L("代码规范", "Code Style"),
        "core":        L("核心规范", "Core Rules"),
        "workflow":    L("工作流程", "Workflow"),
        "thinking":    L("思考策略", "Thinking Strategy"),
        "testing":     L("测试规范", "Testing"),
        "error":       L("错误处理", "Error Handling"),
        "security":    L("安全规范", "Security"),
        "git":         L("Git 规范", "Git Conventions"),
        "hard":        L("禁止事项", "Hard Rules — NEVER Do"),
        "gotchas":     L("特殊注意", "Gotchas & Warnings"),
        "verify":      L("验证检查清单", "Verification Checklist"),
        "references":  L("参考资源", "References"),
    }
    return _TITLES.get(key, key)


# ============================================================================
# 章节渲染器 — 每个函数从 cfg dict 生成一段 markdown
# ============================================================================

def _bullet(items: list, prefix: str = "-") -> str:
    return "\n".join(f"{prefix} {x}" for x in items) if items else ""

def _numbered(items: list) -> str:
    return "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1)) if items else ""


def render_overview(cfg: dict) -> str:
    name = cfg.get("project_name", "my-project")
    desc = cfg.get("project_desc", "")
    ptype = cfg.get("project_type", "")
    status = cfg.get("project_status", "")
    lines = [f"# {name}", ""]
    lines.append(f"## {T('overview')}")
    lines.append("")
    if desc:
        lines.append(desc)
        lines.append("")
    if ptype:
        lines.append(f"- **{L('类型','Type')}**: {ptype}")
    if status:
        lines.append(f"- **{L('状态','Status')}**: {status}")
    lines.append("")
    return "\n".join(lines)


def render_role(cfg: dict) -> str:
    role = cfg.get("role", "")
    extras = cfg.get("persona_extras", [])
    if not role:
        return ""
    lines = [f"## {T('role')}", ""]
    lines.append(f"You are a {role}.")
    lines.append("")
    if extras:
        lines.append(_bullet(extras))
        lines.append("")
    return "\n".join(lines)


def render_tech(cfg: dict) -> str:
    """根据 tech_items 列表渲染技术栈，不再硬编码 language/framework/db 字段"""
    items = cfg.get("tech_items", [])
    # 兼容旧格式
    if not items:
        for key, label_zh, label_en in [
            ("language",       "语言",   "Language"),
            ("framework",      "框架",   "Framework"),
            ("database",       "数据库", "Database"),
            ("infrastructure", "基础设施","Infrastructure"),
            ("os",             "操作系统","OS / Runtime"),
        ]:
            val = cfg.get(key, "")
            if val:
                items.append(f"**{L(label_zh, label_en)}**: {val}")
        items.extend(cfg.get("tech_extras", []))
    if not items:
        return ""
    lines = [f"## {T('tech')}", ""]
    lines.append(_bullet(items))
    lines.append("")
    return "\n".join(lines)


def render_structure(cfg: dict) -> str:
    s = cfg.get("project_structure", "")
    if not s:
        return ""
    lines = [f"## {T('structure')}", "", "```", s, "```", ""]
    return "\n".join(lines)


def render_commands(cfg: dict) -> str:
    cmds = cfg.get("commands", {})
    if not cmds:
        return ""
    lines = [f"## {T('commands')}", ""]
    for label, cmd in cmds.items():
        lines.append(f"- **{label}**: `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def render_style(cfg: dict) -> str:
    items = cfg.get("code_style_rules", [])
    if not items:
        return ""
    return f"## {T('style')}\n\n{_bullet(items)}\n"


def render_core(cfg: dict) -> str:
    items = cfg.get("core_rules", [])
    if not items:
        return ""
    return f"## {T('core')}\n\n{_bullet(items)}\n"


def render_workflow(cfg: dict) -> str:
    items = cfg.get("workflow", [])
    if not items:
        return ""
    return f"## {T('workflow')}\n\n{_numbered(items)}\n"


def render_thinking(cfg: dict) -> str:
    """Claude Code 思考策略引导——这是让 CLAUDE.md 真正能驱动 Claude 的核心增量"""
    items = cfg.get("thinking_strategy", [])
    if not items:
        return ""
    lines = [f"## {T('thinking')}", ""]
    lines.append(_bullet(items))
    lines.append("")
    return "\n".join(lines)


def render_testing(cfg: dict) -> str:
    items = cfg.get("testing_rules", [])
    if not items:
        return ""
    return f"## {T('testing')}\n\n{_bullet(items)}\n"


def render_error(cfg: dict) -> str:
    items = cfg.get("error_handling", [])
    if not items:
        return ""
    return f"## {T('error')}\n\n{_bullet(items)}\n"


def render_security(cfg: dict) -> str:
    items = cfg.get("security_rules", [])
    if not items:
        return ""
    return f"## {T('security')}\n\n{_bullet(items)}\n"


def render_git(cfg: dict) -> str:
    items = cfg.get("git_rules", [])
    if not items:
        return ""
    return f"## {T('git')}\n\n{_bullet(items)}\n"


def render_hard(cfg: dict) -> str:
    items = cfg.get("hard_rules", [])
    if not items:
        return ""
    warn = L("重要：以下规则绝对不可违反。", "IMPORTANT: The following rules must NEVER be violated.")
    lines = [f"## {T('hard')}", "", warn, ""]
    for item in items:
        lines.append(f"- ❌ {item}")
    lines.append("")
    return "\n".join(lines)


def render_gotchas(cfg: dict) -> str:
    items = cfg.get("gotchas", [])
    if not items:
        return ""
    lines = [f"## {T('gotchas')}", ""]
    for item in items:
        lines.append(f"- ⚠️ {item}")
    lines.append("")
    return "\n".join(lines)


def render_verify(cfg: dict) -> str:
    """验证检查清单——让 Claude Code 在完成任务后自我验证"""
    items = cfg.get("verification", [])
    if not items:
        return ""
    title = L(
        "完成任何修改后，必须按以下清单逐项验证：",
        "After completing any change, verify each item below:"
    )
    lines = [f"## {T('verify')}", "", title, ""]
    for item in items:
        lines.append(f"- [ ] {item}")
    lines.append("")
    return "\n".join(lines)


def render_references(cfg: dict) -> str:
    items = cfg.get("references", [])
    if not items:
        return ""
    return f"## {T('references')}\n\n{_bullet(items)}\n"


# 渲染管线 — 按顺序组装
_RENDERERS = [
    render_overview, render_role, render_tech, render_structure,
    render_commands, render_style, render_core, render_workflow,
    render_thinking, render_testing, render_error, render_security,
    render_git, render_hard, render_gotchas, render_verify, render_references,
]

def assemble(cfg: dict) -> str:
    parts = [fn(cfg) for fn in _RENDERERS]
    return "\n".join(p for p in parts if p.strip())


# ============================================================================
# 角色定义 — 每个角色携带独立的向导提问流程和默认预填
# ============================================================================

ROLE_DEFS = {
    "go_backend": {
        "key": "go_backend",
        "label_zh": "Go 后端工程师",
        "label_en": "Go Backend Engineer",
        "role_en": "senior Go backend engineer with expertise in high-performance API design, concurrency patterns, and production-grade systems",
        "role_zh": "资深 Go 后端工程师，擅长高性能 API 设计、并发模式和生产级系统",
        # 向导步骤列表——只问这些
        "wizard_steps": [
            "project_info", "tech_go", "project_structure", "commands",
            "code_style", "core_rules", "workflow", "testing",
            "error_handling", "security", "git", "hard_rules", "gotchas", "references",
        ],
    },
    "python_backend": {
        "key": "python_backend",
        "label_zh": "Python 后端工程师",
        "label_en": "Python Backend Engineer",
        "role_en": "senior Python backend engineer with deep expertise in FastAPI/Django, SQLAlchemy, async programming, and production Python systems",
        "role_zh": "资深 Python 后端工程师，擅长 FastAPI/Django、SQLAlchemy、异步编程和生产级 Python 系统",
        "wizard_steps": [
            "project_info", "tech_python", "project_structure", "commands",
            "code_style", "core_rules", "workflow", "testing",
            "error_handling", "security", "git", "hard_rules", "gotchas", "references",
        ],
    },
    "devops_sre": {
        "key": "devops_sre",
        "label_zh": "DevOps / SRE 运维工程师",
        "label_en": "DevOps / SRE Engineer",
        "role_en": "senior DevOps/SRE engineer with deep expertise in Linux systems, containers, Kubernetes, CI/CD, monitoring, and infrastructure automation",
        "role_zh": "资深 DevOps/SRE 工程师，擅长 Linux 系统、容器化、Kubernetes、CI/CD、监控和基础设施自动化",
        "wizard_steps": [
            "project_info", "tech_devops", "project_structure", "commands",
            "iac_rules", "workflow", "monitoring",
            "security", "git", "hard_rules", "gotchas", "references",
        ],
    },
    "fullstack": {
        "key": "fullstack",
        "label_zh": "全栈工程师",
        "label_en": "Full-Stack Engineer",
        "role_en": "senior full-stack engineer with expertise in modern frontend frameworks and backend API design",
        "role_zh": "资深全栈工程师，擅长现代前端框架和后端 API 设计",
        "wizard_steps": [
            "project_info", "tech_fullstack", "project_structure", "commands",
            "code_style", "core_rules", "workflow", "testing",
            "security", "git", "hard_rules", "gotchas", "references",
        ],
    },
    "data_engineer": {
        "key": "data_engineer",
        "label_zh": "数据工程师",
        "label_en": "Data Engineer",
        "role_en": "senior data engineer with expertise in ETL pipelines, data quality, batch/stream processing, and data warehousing",
        "role_zh": "资深数据工程师，擅长 ETL 流水线、数据质量、批流处理和数据仓库",
        "wizard_steps": [
            "project_info", "tech_data", "project_structure", "commands",
            "data_rules", "workflow", "testing",
            "security", "git", "hard_rules", "gotchas", "references",
        ],
    },
    "custom": {
        "key": "custom",
        "label_zh": "自定义角色",
        "label_en": "Custom Role",
        "role_en": "",
        "role_zh": "",
        "wizard_steps": [
            "project_info", "tech_generic", "project_structure", "commands",
            "code_style", "core_rules", "workflow", "testing",
            "error_handling", "security", "git", "hard_rules", "gotchas", "references",
        ],
    },
}


# ============================================================================
# 向导步骤实现 — 每个 step 函数接收 cfg 并就地修改
# ============================================================================

def step_project_info(cfg: dict):
    print(sub(L("项目基础信息", "Project Info")))
    cfg["project_name"] = ask(L("项目名称", "Project name"), "my-project")
    cfg["project_desc"] = ask(L("一句话项目描述", "One-line description"), "")
    cfg["project_type"] = ask_multi(L("项目类型", "Project type"), [
        ("Backend API",     L("后端 API 服务",        "Backend API Service")),
        ("CLI Tool",        L("命令行工具",            "CLI Tool")),
        ("Microservices",   L("微服务架构",            "Microservices")),
        ("Full-Stack",      L("全栈 Web 应用",        "Full-Stack Web App")),
        ("Data Pipeline",   L("数据处理 / ETL",       "Data Pipeline / ETL")),
        ("DevOps/Infra",    L("基础设施 / DevOps",    "Infrastructure / DevOps")),
        ("K8s Operator",    L("Kubernetes Operator",  "Kubernetes Operator")),
        ("Library/SDK",     L("库 / SDK",             "Library / SDK")),
        ("Other",           L("其他",                  "Other")),
    ], default="Backend API")
    cfg["project_status"] = ask(L("项目状态", "Project status"), L("开发中", "Active development"))


def step_tech_go(cfg: dict):
    print(sub(L("Go 技术栈配置", "Go Tech Stack")))
    go_ver = ask(L("Go 版本", "Go version"), "Go 1.23+")
    framework = ask(L("HTTP 框架", "HTTP framework"), "Gin")
    db = ask(L("数据库", "Database"), "PostgreSQL + Redis")
    orm = ask(L("数据库访问层", "DB access layer"), "sqlx")
    migration = ask(L("数据库迁移工具", "Migration tool"), "golang-migrate")
    config = ask(L("配置管理", "Config management"), "Viper")
    logging = ask(L("日志方案", "Logging"), "slog (stdlib)")
    observability = ask(L("可观测性", "Observability"), "OpenTelemetry + Prometheus")
    infra = ask(L("部署目标", "Deploy target"), "Docker + Kubernetes")
    os_env = ask(L("操作系统", "OS"), "Linux (Ubuntu 22.04+)")
    cfg["tech_items"] = [
        f"**{L('语言','Language')}**: {go_ver}",
        f"**{L('HTTP 框架','HTTP Framework')}**: {framework}",
        f"**{L('数据库','Database')}**: {db}",
        f"**{L('数据库访问','DB Access')}**: {orm}",
        f"**{L('迁移工具','Migration')}**: {migration}",
        f"**{L('配置管理','Config')}**: {config}",
        f"**{L('日志','Logging')}**: {logging}",
        f"**{L('可观测性','Observability')}**: {observability}",
        f"**{L('部署','Deploy')}**: {infra}",
        f"**{L('操作系统','OS')}**: {os_env}",
    ]
    if ask_yn(L("是否有其他技术组件?", "Any other tech components?"), False):
        extras = ask_lines(L("补充技术组件", "Additional components"))
        cfg["tech_items"].extend(extras)


def step_tech_python(cfg: dict):
    print(sub(L("Python 技术栈配置", "Python Tech Stack")))
    py_ver = ask(L("Python 版本", "Python version"), "Python 3.12+")
    framework = ask(L("Web 框架", "Web framework"), "FastAPI + Uvicorn")
    db = ask(L("数据库", "Database"), "PostgreSQL")
    orm = ask(L("ORM / 数据访问", "ORM / DB access"), "SQLAlchemy 2.0 (async)")
    migration = ask(L("迁移工具", "Migration tool"), "Alembic")
    validation = ask(L("数据验证", "Validation"), "Pydantic v2")
    pkg_mgr = ask(L("包管理器", "Package manager"), "uv")
    lint = ask(L("Lint / Format", "Lint / Format"), "ruff")
    typecheck = ask(L("类型检查", "Type checking"), "mypy")
    test_fw = ask(L("测试框架", "Test framework"), "pytest + httpx")
    infra = ask(L("部署目标", "Deploy target"), "Docker + Kubernetes")
    os_env = ask(L("操作系统", "OS"), "Linux (Ubuntu 22.04+)")
    cfg["tech_items"] = [
        f"**{L('语言','Language')}**: {py_ver}",
        f"**{L('Web 框架','Web Framework')}**: {framework}",
        f"**{L('数据库','Database')}**: {db}",
        f"**{L('ORM','ORM')}**: {orm}",
        f"**{L('迁移工具','Migration')}**: {migration}",
        f"**{L('数据验证','Validation')}**: {validation}",
        f"**{L('包管理','Package Manager')}**: {pkg_mgr}",
        f"**{L('Lint / Format','Lint / Format')}**: {lint}",
        f"**{L('类型检查','Type Check')}**: {typecheck}",
        f"**{L('测试框架','Test Framework')}**: {test_fw}",
        f"**{L('部署','Deploy')}**: {infra}",
        f"**{L('操作系统','OS')}**: {os_env}",
    ]


def step_tech_devops(cfg: dict):
    print(sub(L("运维技术栈配置", "DevOps Tech Stack")))
    cloud = ask(L("云平台", "Cloud provider"), "AWS")
    iac = ask(L("IaC 工具", "IaC tool"), "Terraform")
    config_mgmt = ask(L("配置管理工具", "Config management"), "Ansible")
    container = ask(L("容器运行时", "Container runtime"), "Docker + containerd")
    orchestration = ask(L("编排平台", "Orchestration"), "Kubernetes (EKS)")
    cicd = ask(L("CI/CD 平台", "CI/CD platform"), "GitHub Actions")
    monitoring = ask(L("监控方案", "Monitoring"), "Prometheus + Grafana")
    logging = ask(L("日志方案", "Logging"), "Loki + Grafana")
    secrets = ask(L("密钥管理", "Secret management"), "AWS Secrets Manager / Vault")
    scripting = ask(L("脚本语言", "Scripting languages"), "Bash, Python, Go")
    os_env = ask(L("操作系统", "OS"), "Ubuntu 22.04 / Amazon Linux 2023")
    cfg["tech_items"] = [
        f"**{L('云平台','Cloud')}**: {cloud}",
        f"**{L('IaC 工具','IaC')}**: {iac}",
        f"**{L('配置管理','Config Mgmt')}**: {config_mgmt}",
        f"**{L('容器','Container')}**: {container}",
        f"**{L('编排','Orchestration')}**: {orchestration}",
        f"**{L('CI/CD','CI/CD')}**: {cicd}",
        f"**{L('监控','Monitoring')}**: {monitoring}",
        f"**{L('日志','Logging')}**: {logging}",
        f"**{L('密钥管理','Secrets')}**: {secrets}",
        f"**{L('脚本','Scripting')}**: {scripting}",
        f"**{L('操作系统','OS')}**: {os_env}",
    ]


def step_tech_fullstack(cfg: dict):
    print(sub(L("全栈技术栈配置", "Full-Stack Tech Stack")))
    fe_lang = ask(L("前端语言", "Frontend language"), "TypeScript")
    fe_framework = ask(L("前端框架", "Frontend framework"), "React / Next.js")
    be_lang = ask(L("后端语言", "Backend language"), "Go")
    be_framework = ask(L("后端框架", "Backend framework"), "Gin")
    db = ask(L("数据库", "Database"), "PostgreSQL + Redis")
    api_style = ask(L("API 风格", "API style"), "RESTful + OpenAPI")
    infra = ask(L("部署方式", "Deployment"), "Docker + Vercel (FE) + K8s (BE)")
    cfg["tech_items"] = [
        f"**{L('前端','Frontend')}**: {fe_lang} + {fe_framework}",
        f"**{L('后端','Backend')}**: {be_lang} + {be_framework}",
        f"**{L('数据库','Database')}**: {db}",
        f"**{L('API 风格','API Style')}**: {api_style}",
        f"**{L('部署','Deploy')}**: {infra}",
    ]


def step_tech_data(cfg: dict):
    print(sub(L("数据工程技术栈", "Data Engineering Tech Stack")))
    lang = ask(L("语言", "Language"), "Python 3.12+")
    processing = ask(L("数据处理框架", "Data processing"), "pandas / polars")
    orchestration = ask(L("调度 / 编排", "Orchestration"), "Airflow / Dagster")
    storage = ask(L("数据存储", "Data storage"), "S3 + Parquet")
    warehouse = ask(L("数据仓库", "Data warehouse"), "ClickHouse / BigQuery")
    validation = ask(L("数据验证", "Data validation"), "pandera / great_expectations")
    infra = ask(L("基础设施", "Infrastructure"), "Docker, Airflow")
    cfg["tech_items"] = [
        f"**{L('语言','Language')}**: {lang}",
        f"**{L('数据处理','Processing')}**: {processing}",
        f"**{L('调度','Orchestration')}**: {orchestration}",
        f"**{L('存储','Storage')}**: {storage}",
        f"**{L('数据仓库','Warehouse')}**: {warehouse}",
        f"**{L('数据验证','Validation')}**: {validation}",
        f"**{L('基础设施','Infrastructure')}**: {infra}",
    ]


def step_tech_generic(cfg: dict):
    print(sub(L("技术栈配置", "Tech Stack")))
    cfg["tech_items"] = []
    print(f"  {c(L('逐行输入技术组件，格式自由，空行结束', 'Enter tech items, one per line, empty to finish'), C.DIM)}")
    print(f"  {c(L('例如: **语言**: Go 1.23+', 'e.g.: **Language**: Go 1.23+'), C.DIM)}")
    while True:
        line = input("    > ").strip()
        if not line:
            break
        cfg["tech_items"].append(line)


def step_project_structure(cfg: dict):
    print(sub(L("项目结构", "Project Structure")))
    if ask_yn(L("是否添加目录结构?", "Add directory structure?"), True):
        print(f"  {c(L('粘贴 tree 输出，空行结束', 'Paste tree output, empty to finish'), C.DIM)}")
        lines = ask_lines(L("目录结构", "Directory structure"))
        cfg["project_structure"] = "\n".join(lines)


def step_commands(cfg: dict):
    print(sub(L("常用命令", "Common Commands")))
    cfg["commands"] = ask_cmds(L("常用命令", "Common commands"))


def step_code_style(cfg: dict):
    print(sub(L("代码规范", "Code Style")))
    print(f"  {c(L('提示：格式化/lint 最好交给工具，这里写 Claude 无法推断的约定', 'Tip: let linters handle formatting; write conventions Claude cannot infer'), C.DIM)}")
    cfg["code_style_rules"] = ask_lines(L("代码规范", "Code style rules"))


def step_core_rules(cfg: dict):
    print(sub(L("核心规范", "Core Rules")))
    print(f"  {c(L('只写「不写就会出错」的规则，保持精简', 'Only rules that prevent mistakes. Keep it lean.'), C.DIM)}")
    cfg["core_rules"] = ask_lines(L("核心规范", "Core rules"))


def step_iac_rules(cfg: dict):
    """运维角色特有：IaC / 基础设施规则"""
    print(sub(L("基础设施与 IaC 规范", "Infrastructure & IaC Rules")))
    print(f"  {c(L('涵盖 Terraform/Ansible/K8s/脚本 等规范', 'Terraform, Ansible, K8s, scripts, etc.'), C.DIM)}")
    cfg["core_rules"] = ask_lines(L("IaC 核心规范", "IaC core rules"))
    print(f"\n  {c(L('Shell 脚本规范:', 'Shell scripting rules:'), C.CYN)}")
    cfg["code_style_rules"] = ask_lines(L("脚本 / 代码规范", "Script / code style"))


def step_data_rules(cfg: dict):
    """数据工程角色特有：数据质量规则"""
    print(sub(L("数据工程规范", "Data Engineering Rules")))
    print(f"  {c(L('数据正确性、幂等、质量校验等', 'Correctness, idempotency, quality checks, etc.'), C.DIM)}")
    cfg["core_rules"] = ask_lines(L("数据工程核心规范", "Data engineering core rules"))
    cfg["code_style_rules"] = ask_lines(L("代码规范", "Code style rules"))


def step_monitoring(cfg: dict):
    """运维角色特有：监控规范"""
    print(sub(L("监控与告警规范", "Monitoring & Alerting")))
    cfg["testing_rules"] = ask_lines(L("监控 / 验证 / 测试规范", "Monitoring / validation / testing rules"))


def step_workflow(cfg: dict):
    print(sub(L("工作流程", "Workflow")))
    print(f"  {c(L('Claude Code 处理任务时应该遵循的步骤', 'Steps Claude Code should follow when handling tasks'), C.DIM)}")
    cfg["workflow"] = ask_lines(L("工作流步骤", "Workflow steps"))


def step_testing(cfg: dict):
    print(sub(L("测试规范", "Testing")))
    cfg["testing_rules"] = ask_lines(L("测试规范", "Testing rules"))


def step_error_handling(cfg: dict):
    print(sub(L("错误处理", "Error Handling")))
    cfg["error_handling"] = ask_lines(L("错误处理规范", "Error handling rules"))


def step_security(cfg: dict):
    print(sub(L("安全规范", "Security")))
    cfg["security_rules"] = ask_lines(L("安全规范", "Security rules"))


def step_git(cfg: dict):
    print(sub(L("Git 规范", "Git Conventions")))
    cfg["git_rules"] = ask_lines(L("Git 规范", "Git rules"))


def step_hard_rules(cfg: dict):
    print(sub(L("禁止事项 (NEVER DO)", "Hard Rules (NEVER DO)")))
    print(f"  {c(L('用 NEVER/禁止 句式写清楚红线', 'Write clear red lines with NEVER'), C.DIM)}")
    cfg["hard_rules"] = ask_lines(L("禁止事项", "Hard rules"))


def step_gotchas(cfg: dict):
    print(sub(L("特殊注意 / 项目陷阱", "Gotchas & Warnings")))
    cfg["gotchas"] = ask_lines(L("特殊注意事项", "Gotchas"))


def step_references(cfg: dict):
    print(sub(L("参考资源", "References")))
    print(f"  {c(L('填入文档路径或链接让 Claude 需要时去查', 'Paths or URLs Claude can consult when needed'), C.DIM)}")
    cfg["references"] = ask_lines(L("参考资源", "References"))


# 步骤注册表
STEP_REGISTRY = {
    "project_info":      step_project_info,
    "tech_go":           step_tech_go,
    "tech_python":       step_tech_python,
    "tech_devops":       step_tech_devops,
    "tech_fullstack":    step_tech_fullstack,
    "tech_data":         step_tech_data,
    "tech_generic":      step_tech_generic,
    "project_structure": step_project_structure,
    "commands":          step_commands,
    "code_style":        step_code_style,
    "core_rules":        step_core_rules,
    "iac_rules":         step_iac_rules,
    "data_rules":        step_data_rules,
    "monitoring":        step_monitoring,
    "workflow":          step_workflow,
    "testing":           step_testing,
    "error_handling":    step_error_handling,
    "security":          step_security,
    "git":               step_git,
    "hard_rules":        step_hard_rules,
    "gotchas":           step_gotchas,
    "references":        step_references,
}


# ============================================================================
# 预设模板 — 内容大幅增加，加入 thinking_strategy 和 verification
# ============================================================================

def _go_api_preset(lang: str) -> dict:
    zh = (lang == "zh")
    return {
        "project_name": "my-go-api",
        "project_desc": "Go RESTful API 后端服务。" if zh else "Go RESTful API backend service.",
        "project_type": "Backend API Service",
        "project_status": "开发中" if zh else "Active development",
        "role": "senior Go backend engineer with expertise in high-performance API design, concurrency patterns, and production-grade systems",
        "persona_extras": [
            "Write idiomatic Go — simple, readable, and explicit",
            "Prefer stdlib solutions over third-party libraries when reasonable",
            "Think about performance, but measure before optimizing",
            "When unsure about project conventions, read existing code in `internal/` first",
        ],
        "tech_items": [
            f"**{'语言' if zh else 'Language'}**: Go 1.23+",
            f"**{'HTTP 框架' if zh else 'HTTP Framework'}**: Gin / Echo / Chi",
            f"**{'数据库' if zh else 'Database'}**: PostgreSQL + Redis",
            f"**{'数据库访问' if zh else 'DB Access'}**: sqlx ({('优先原生 SQL' if zh else 'prefer raw SQL over heavy ORM')})",
            f"**{'迁移工具' if zh else 'Migration'}**: golang-migrate",
            f"**{'配置' if zh else 'Config'}**: Viper / envconfig",
            f"**{'日志' if zh else 'Logging'}**: slog ({('标准库结构化日志' if zh else 'stdlib structured logging')})",
            f"**{'可观测性' if zh else 'Observability'}**: OpenTelemetry + Prometheus",
            f"**{'部署' if zh else 'Deploy'}**: Docker + Kubernetes",
            f"**{'操作系统' if zh else 'OS'}**: Linux (Ubuntu 22.04+)",
        ],
        "project_structure": textwrap.dedent("""\
            .
            ├── cmd/              # 应用入口
            │   └── server/       # API 服务主程序
            ├── internal/         # 私有代码（不可被外部导入）
            │   ├── handler/      # HTTP 处理器
            │   ├── service/      # 业务逻辑层
            │   ├── repository/   # 数据访问层
            │   ├── model/        # 领域模型
            │   └── middleware/   # HTTP 中间件
            ├── pkg/              # 可复用公共包
            ├── api/              # OpenAPI/Swagger 规范
            ├── migrations/       # 数据库迁移文件
            ├── deploy/           # 部署配置 (Dockerfile, K8s)
            ├── scripts/          # 构建与工具脚本
            ├── Makefile
            ├── go.mod
            └── CLAUDE.md""") if zh else textwrap.dedent("""\
            .
            ├── cmd/              # Application entrypoints
            │   └── server/       # Main API server
            ├── internal/         # Private application code
            │   ├── handler/      # HTTP handlers
            │   ├── service/      # Business logic
            │   ├── repository/   # Data access layer
            │   ├── model/        # Domain models
            │   └── middleware/   # HTTP middleware
            ├── pkg/              # Public reusable packages
            ├── api/              # OpenAPI/Swagger specs
            ├── migrations/       # Database migrations
            ├── deploy/           # Deployment configs (Docker, K8s)
            ├── scripts/          # Build and utility scripts
            ├── Makefile
            ├── go.mod
            └── CLAUDE.md"""),
        "commands": {
            ("启动开发服务" if zh else "Run dev server"):  "go run ./cmd/server",
            ("运行全部测试" if zh else "Run all tests"):   "go test ./...",
            ("运行单个测试" if zh else "Run single test"): "go test ./internal/service -run TestXxx -v",
            ("代码检查" if zh else "Lint"):                "golangci-lint run ./...",
            ("编译" if zh else "Build"):                   "go build -o bin/server ./cmd/server",
            ("数据库迁移" if zh else "Migration up"):      "migrate -path migrations -database $DB_URL up",
            ("生成 Mock" if zh else "Generate mocks"):     "go generate ./...",
        },
        "code_style_rules": [
            ("遵循 Effective Go 和 Go Code Review Comments" if zh else "Follow Effective Go and Go Code Review Comments"),
            ("`gofmt` / `goimports` 格式化——不争论风格" if zh else "`gofmt` / `goimports` for formatting — never argue about style"),
            ("导出名称必须有文档注释" if zh else "Exported names must have doc comments"),
            ("函数不超过 50 行；超过则拆分" if zh else "Keep functions under 50 lines; split if longer"),
            ("使用 Table-Driven 测试" if zh else "Use table-driven tests"),
            ("错误信息：小写、无标点、用 `fmt.Errorf(\"doing x: %w\", err)` 包装" if zh else "Error messages: lowercase, no punctuation, wrap with `fmt.Errorf(\"doing x: %w\", err)`"),
            ("接口按行为命名: `Reader`, `Validator`，不用 `IReader`" if zh else "Name interfaces by behavior: `Reader`, `Validator`, not `IReader`"),
        ],
        "core_rules": [
            ("始终处理错误——禁止用 `_` 丢弃 error" if zh else "Always handle errors — never use `_` to discard errors"),
            ("I/O 函数的第一个参数必须是 `context.Context`" if zh else "Use `context.Context` as first parameter in functions that do I/O"),
            ("打开资源后立即用 `defer` 关闭" if zh else "Close resources with `defer` immediately after opening"),
            ("禁止在 `init()` 中放非平凡逻辑" if zh else "Never use `init()` for non-trivial logic"),
            ("使用依赖注入；不使用全局可变状态" if zh else "Use dependency injection; no global mutable state"),
            ("所有 SQL 必须使用参数化查询（防 SQL 注入）" if zh else "All SQL must use parameterized queries (prevent SQL injection)"),
            ("HTTP Handler 必须校验和清理所有输入" if zh else "HTTP handlers must validate and sanitize all input"),
            ("共享状态的并发访问必须用 mutex 或 channel 保护" if zh else "Concurrent access to shared state must use mutexes or channels"),
        ],
        "workflow": [
            ("先阅读相关代码，理解现有模式，再动手修改" if zh else "Read relevant code and understand existing patterns before making changes"),
            ("对非平凡功能，先制定计划并确认后再实现" if zh else "Create a plan and confirm before implementing non-trivial features"),
            ("修改代码时同步编写或更新测试" if zh else "Write or update tests alongside code changes"),
            ("运行 `golangci-lint run ./...` 确保无 lint 问题" if zh else "Run `golangci-lint run ./...` to verify no lint issues"),
            ("运行 `go test ./...` 确保无回归" if zh else "Run `go test ./...` to verify no regressions"),
            ("保持 commit 小且聚焦——一个逻辑变更一个 commit" if zh else "Keep commits small and focused — one logical change per commit"),
        ],
        "thinking_strategy": [
            ("接到复杂任务时，先用 think/ultrathink 规划方案，得到确认后再写代码" if zh else "For complex tasks, use think/ultrathink to plan first. Get confirmation before coding."),
            ("遇到不确定的项目约定时，先搜索 `internal/` 目录中的现有代码作为参考" if zh else "When unsure about conventions, search existing code in `internal/` for reference patterns"),
            ("修改公共接口前，先用 grep 查找所有调用方，评估影响范围" if zh else "Before changing public interfaces, grep all callers and assess impact"),
            ("如果任务涉及多个文件，先列出需要修改的文件清单" if zh else "If a task spans multiple files, list all files to change before starting"),
        ],
        "testing_rules": [
            ("用 Table-Driven 测试覆盖多输入场景" if zh else "Use table-driven tests for functions with multiple input/output cases"),
            ("用 `testify/assert` 或标准库 `testing` 做断言" if zh else "Use `testify/assert` or stdlib `testing` for assertions"),
            ("通过接口 Mock 外部依赖，不依赖具体实现" if zh else "Mock external dependencies with interfaces, not concrete types"),
            ("集成测试放在 `_test.go` 中，用 build tag `//go:build integration`" if zh else "Integration tests in `_test.go` files with build tag `//go:build integration`"),
            ("为性能关键路径编写 Benchmark: `func BenchmarkXxx(b *testing.B)`" if zh else "Benchmark critical paths with `func BenchmarkXxx(b *testing.B)`"),
        ],
        "error_handling": [
            ("返回错误，不要 panic（除非真正不可恢复）" if zh else "Return errors, don't panic (except truly unrecoverable situations)"),
            ("用上下文包装错误: `fmt.Errorf(\"creating user: %w\", err)`" if zh else "Wrap errors with context: `fmt.Errorf(\"creating user: %w\", err)`"),
            ("用哨兵错误处理预期错误: `var ErrNotFound = errors.New(...)`" if zh else "Use sentinel errors for expected errors: `var ErrNotFound = errors.New(...)`"),
            ("在边界层（handler）记录日志，不在业务逻辑深处" if zh else "Log errors at the boundary (handler), not deep in business logic"),
            ("Handler 层将领域错误映射为对应 HTTP 状态码" if zh else "HTTP handlers: map domain errors to appropriate status codes"),
        ],
        "security_rules": [
            ("禁止硬编码密钥——使用环境变量或密钥管理器" if zh else "Never hardcode secrets — use environment variables or secret managers"),
            ("所有用户输入必须验证后再处理" if zh else "All user input must be validated before processing"),
            ("只使用参数化 SQL 查询——禁止字符串拼接 SQL" if zh else "Use parameterized SQL queries exclusively — NO string concatenation"),
            ("所有 HTTP 客户端和数据库连接必须设置超时" if zh else "Set timeouts on all HTTP clients and database connections"),
            ("对外接口实施限流" if zh else "Rate limit public-facing endpoints"),
        ],
        "git_rules": [
            ("分支命名: `feature/xxx`, `fix/xxx`, `refactor/xxx`" if zh else "Branch naming: `feature/xxx`, `fix/xxx`, `refactor/xxx`"),
            ("Commit 消息: Conventional Commits 格式 — `type(scope): description`" if zh else "Commit messages: Conventional Commits — `type(scope): description`"),
            ("始终在功能分支开发，禁止直接提交到 main" if zh else "Always work on feature branches, never commit directly to main"),
        ],
        "hard_rules": [
            ("NEVER commit secrets, API keys, passwords, or certificates" if not zh else "禁止提交密钥、API Key、密码或证书到仓库"),
            ("NEVER use `os.Exit()` outside of `main()`" if not zh else "禁止在 `main()` 之外使用 `os.Exit()`"),
            ("NEVER use `panic()` for normal error handling" if not zh else "禁止用 `panic()` 处理常规错误"),
            ("NEVER ignore errors with blank identifier `_`" if not zh else "禁止用 `_` 忽略 error 返回值"),
            ("NEVER use `unsafe` package without explicit approval" if not zh else "禁止未经批准使用 `unsafe` 包"),
            ("NEVER modify generated files (protobuf, mocks) by hand" if not zh else "禁止手动修改生成的文件（protobuf, mock 等）"),
            ("NEVER add dependencies without discussing the rationale" if not zh else "禁止未经讨论添加新依赖"),
        ],
        "gotchas": [
            ("`internal/` 目录有 Go 包可见性限制——外部模块无法导入" if zh else "`internal/` enforces Go package visibility — external modules cannot import"),
            ("`context.Background()` 只在 `main()` 或顶层使用——其他地方必须传递 context" if zh else "`context.Background()` only in `main()` — pass context everywhere else"),
            ("注意 goroutine 泄漏——始终确保 goroutine 有退出路径" if zh else "Watch for goroutine leaks — always ensure goroutines can exit"),
            ("JSON struct tag 使用 snake_case: `json:\"field_name\"`" if zh else "JSON struct tags use snake_case: `json:\"field_name\"`"),
            ("时间处理: 始终使用 `time.Time` 和 `time.Duration`，不用裸整数" if zh else "Time: always use `time.Time` / `time.Duration`, never raw integers"),
        ],
        "verification": [
            ("`golangci-lint run ./...` 通过，无报错" if zh else "`golangci-lint run ./...` passes with no errors"),
            ("`go test ./...` 全部通过" if zh else "`go test ./...` all pass"),
            ("`go build ./...` 编译成功" if zh else "`go build ./...` compiles successfully"),
            ("新增公共函数有文档注释" if zh else "New public functions have doc comments"),
            ("没有引入未讨论的新依赖" if zh else "No undiscussed new dependencies introduced"),
            ("没有硬编码的密钥或配置值" if zh else "No hardcoded secrets or config values"),
            ("修改过的代码有对应的测试覆盖" if zh else "Changed code has corresponding test coverage"),
        ],
        "references": [
            (f"{'项目布局' if zh else 'Project layout'}: `cmd/`, `internal/`, `pkg/`"),
            (f"{'API 规范' if zh else 'API spec'}: `api/openapi.yaml`"),
            (f"{'部署配置' if zh else 'Deployment'}: `deploy/` (Dockerfile, K8s)"),
            (f"{'业务逻辑示例' if zh else 'Business logic examples'}: `internal/service/`"),
        ],
    }

def _devops_preset(lang: str) -> dict:
    zh = (lang == "zh")
    return {
        "project_name": "infra",
        "project_desc": "基础设施即代码与 DevOps 自动化。" if zh else "Infrastructure as Code and DevOps automation.",
        "project_type": "DevOps / Infrastructure",
        "project_status": "运行中" if zh else "Active",
        "role": "senior DevOps/SRE engineer with deep expertise in Linux, containers, Kubernetes, CI/CD, monitoring, and infrastructure automation",
        "persona_extras": [
            ("每次变更都要考虑幂等性、可靠性和回滚方案" if zh else "Think about idempotency, reliability, and rollback for every change"),
            ("做两次以上的事情就要自动化" if zh else "Automate everything done more than twice"),
            ("基础设施即代码——版本控制、审查、测试" if zh else "Treat infrastructure as code — version control, review, test"),
            ("变更前评估影响范围（爆炸半径）" if zh else "Always consider blast radius before applying changes"),
        ],
        "tech_items": [
            f"**{'云平台' if zh else 'Cloud'}**: AWS / GCP / Azure",
            f"**{'IaC' if zh else 'IaC'}**: Terraform",
            f"**{'配置管理' if zh else 'Config Mgmt'}**: Ansible",
            f"**{'容器' if zh else 'Container'}**: Docker + containerd",
            f"**{'编排' if zh else 'Orchestration'}**: Kubernetes (EKS/GKE/AKS)",
            f"**{'CI/CD' if zh else 'CI/CD'}**: GitHub Actions / GitLab CI",
            f"**{'监控' if zh else 'Monitoring'}**: Prometheus + Grafana + AlertManager",
            f"**{'日志' if zh else 'Logging'}**: Loki / ELK",
            f"**{'密钥管理' if zh else 'Secrets'}**: Vault / AWS Secrets Manager",
            f"**{'脚本' if zh else 'Scripting'}**: Bash, Python, Go",
            f"**{'操作系统' if zh else 'OS'}**: Ubuntu 22.04 / Amazon Linux 2023",
        ],
        "project_structure": textwrap.dedent("""\
            .
            ├── terraform/
            │   ├── modules/        # {m}
            │   ├── environments/   # {e}
            │   │   ├── dev/
            │   │   ├── staging/
            │   │   └── prod/
            │   └── global/         # {g}
            ├── ansible/
            │   ├── roles/
            │   ├── playbooks/
            │   └── inventory/
            ├── k8s/
            │   ├── base/           # Kustomize base
            │   └── overlays/       # {o}
            ├── docker/
            ├── scripts/            # {s}
            ├── .github/workflows/  # CI/CD
            ├── Makefile
            └── CLAUDE.md""".format(
                m="可复用 TF 模块" if zh else "Reusable TF modules",
                e="按环境区分配置" if zh else "Per-environment configs",
                g="全局共享资源" if zh else "Global shared resources",
                o="按环境覆盖层" if zh else "Per-env overlays",
                s="运维脚本" if zh else "Operational scripts",
            )),
        "commands": {
            ("TF 初始化" if zh else "TF init"):           "cd terraform/environments/dev && terraform init",
            ("TF 计划" if zh else "TF plan"):              "terraform plan -var-file=terraform.tfvars",
            ("TF 执行" if zh else "TF apply"):             "terraform apply -var-file=terraform.tfvars",
            ("Ansible 检测" if zh else "Ansible ping"):    "ansible all -m ping -i ansible/inventory/dev",
            ("Ansible 执行" if zh else "Ansible playbook"):"ansible-playbook -i ansible/inventory/dev ansible/playbooks/site.yml",
            ("K8s 部署" if zh else "K8s apply"):           "kubectl apply -k k8s/overlays/dev/",
            ("Docker 构建" if zh else "Docker build"):     "docker build -t app:latest -f docker/Dockerfile .",
            ("TF 格式化" if zh else "TF format"):          "terraform fmt -check -recursive",
            ("Shell 检查" if zh else "Shell lint"):         "shellcheck scripts/*.sh",
        },
        "code_style_rules": [
            ("Shell 脚本: 开头必须 `set -euo pipefail`" if zh else "Shell scripts: `set -euo pipefail` at the top"),
            ("Shell 脚本: 必须通过 `shellcheck`" if zh else "Shell scripts: must pass `shellcheck`"),
            ("Terraform: `terraform fmt` 格式化，`tflint` 检查" if zh else "Terraform: `terraform fmt` + `tflint`"),
            ("YAML: 2 空格缩进，不用 Tab" if zh else "YAML: 2-space indent, no tabs"),
            ("命名: 资源用 snake_case, K8s 对象用 kebab-case" if zh else "Naming: snake_case for resources, kebab-case for k8s objects"),
        ],
        "core_rules": [
            ("所有基础设施变更必须通过代码审查 (PR)" if zh else "ALL infrastructure changes must go through PR review"),
            ("执行 `terraform apply` 前必须先 `plan` 并审查" if zh else "ALWAYS run `terraform plan` and review before `terraform apply`"),
            ("生产环境变更必须有回滚方案" if zh else "Production changes must have a documented rollback plan"),
            ("用模块封装可复用基础设施——禁止复制粘贴" if zh else "Use modules for reusable infrastructure — don't copy-paste"),
            ("所有云资源打标签: environment, team, managed-by" if zh else "Tag all cloud resources: environment, team, managed-by"),
            ("Terraform 状态必须用远端存储 + 锁" if zh else "Use remote state with locking for Terraform"),
            ("密钥必须在 Vault 或云密钥管理器中，禁止写在代码里" if zh else "Secrets must be in Vault or cloud secret managers, never in code"),
        ],
        "workflow": [
            ("先了解当前基础设施状态和模块结构" if zh else "Read the current infrastructure state and module structure first"),
            ("制定变更计划：影响哪些模块、哪些环境、回滚步骤" if zh else "Plan: which modules, which environments, rollback steps"),
            ("按 dev → staging → prod 顺序逐环境应用" if zh else "Apply in dev → staging → prod order"),
            ("每个环境变更后运行冒烟测试验证" if zh else "Verify with smoke tests after each environment"),
            ("变更完成后更新文档和 runbook" if zh else "Update docs and runbooks after changes"),
        ],
        "thinking_strategy": [
            ("变更基础设施前，先列出影响的资源和依赖关系" if zh else "Before infra changes, list affected resources and dependencies"),
            ("高风险操作（删除、迁移状态）前，先确认备份和回滚方案" if zh else "Before high-risk ops (destroy, state mv), confirm backup and rollback"),
            ("不确定时，先用 `terraform plan` 输出评估影响" if zh else "When unsure, assess impact with `terraform plan` output first"),
            ("跨环境变更时，先在 dev 验证，确认后再推进" if zh else "For cross-env changes, validate in dev first before proceeding"),
        ],
        "testing_rules": [
            ("`terraform validate` + `tflint` 检查所有 TF 代码" if zh else "`terraform validate` + `tflint` on all TF code"),
            ("`tfsec` / `checkov` 安全扫描" if zh else "`tfsec` / `checkov` for security scanning"),
            ("Shell 脚本: `shellcheck` + `bats` 测试框架" if zh else "Shell scripts: `shellcheck` + `bats` testing"),
            ("Ansible: `molecule` 测试角色" if zh else "Ansible: `molecule` for role testing"),
        ],
        "error_handling": [
            ("Shell: `set -e` 快速失败; `trap` 清理资源" if zh else "Shell: `set -e` fail fast; `trap` for cleanup"),
            ("Terraform: 隐式依赖不够时显式使用 `depends_on`" if zh else "Terraform: use `depends_on` explicitly when implicit deps aren't enough"),
            ("始终有回滚方案: 上一版 TF 状态、上一版 K8s 清单" if zh else "Always have rollback: previous TF state, previous K8s manifests"),
        ],
        "security_rules": [
            ("禁止在 Terraform/Ansible/脚本中硬编码密钥" if zh else "NEVER hardcode secrets in Terraform, Ansible, or scripts"),
            ("IAM 最小权限——生产环境禁止 wildcard (*)" if zh else "Least-privilege IAM — no wildcard (*) in production"),
            ("所有存储和数据库启用静态加密 + 传输加密" if zh else "Enable encryption at rest and in transit for all data stores"),
            ("Docker 镜像漏洞扫描 (Trivy/Snyk)" if zh else "Scan Docker images for vulnerabilities (Trivy/Snyk)"),
            ("网络: 默认拒绝，仅放行所需流量" if zh else "Network: default-deny; allow only required traffic"),
        ],
        "git_rules": [
            ("分支: `infra/xxx` 用于基础设施变更" if zh else "Branch: `infra/xxx` for infrastructure changes"),
            ("Conventional Commits: `infra(scope): description`" if zh else "Conventional Commits: `infra(scope): description`"),
            ("PR 描述中包含 `terraform plan` 输出" if zh else "Include `terraform plan` output in PR description"),
        ],
        "hard_rules": [
            ("禁止未经审查的 plan 直接 apply 到生产" if zh else "NEVER `terraform apply` on prod without a reviewed plan"),
            ("禁止提交密钥、Token 或私钥" if zh else "NEVER commit secrets, tokens, or private keys"),
            ("禁止使用 `chmod 777`" if zh else "NEVER use `chmod 777`"),
            ("禁止未备份就删除有状态资源（数据库、S3）" if zh else "NEVER delete stateful resources without backup verification"),
            ("禁止关闭安全功能（防火墙、SELinux）来排障" if zh else "NEVER disable security features as a troubleshooting step"),
            ("禁止用 `curl | bash` 安装生产软件" if zh else "NEVER use `curl | bash` for production software"),
            ("禁止在版本控制之外修改生产基础设施" if zh else "NEVER modify production infra outside version-controlled IaC"),
        ],
        "gotchas": [
            ("Terraform state 含敏感数据——加密且限制访问" if zh else "Terraform state contains secrets — encrypt and restrict access"),
            ("`terraform destroy` 对有状态资源不可逆——反复确认" if zh else "`terraform destroy` is irreversible for stateful resources"),
            ("K8s `default` 命名空间不应跑工作负载" if zh else "K8s `default` namespace should not run workloads"),
            ("Ansible `become: yes` 以 root 执行——注意文件权限" if zh else "Ansible `become: yes` runs as root — watch file permissions"),
        ],
        "verification": [
            ("`terraform fmt -check` 通过" if zh else "`terraform fmt -check` passes"),
            ("`terraform validate` 通过" if zh else "`terraform validate` passes"),
            ("`tflint` 无错误" if zh else "`tflint` has no errors"),
            ("`shellcheck scripts/*.sh` 通过" if zh else "`shellcheck scripts/*.sh` passes"),
            ("没有硬编码的密钥或 IP 地址" if zh else "No hardcoded secrets or IP addresses"),
            ("云资源标签完整" if zh else "Cloud resource tags are complete"),
            ("变更有对应的回滚步骤记录" if zh else "Changes have documented rollback steps"),
        ],
        "references": [
            (f"{'TF 模块' if zh else 'TF modules'}: `terraform/modules/`"),
            (f"{'环境配置' if zh else 'Env configs'}: `terraform/environments/{{env}}/`"),
            (f"{'K8s 清单' if zh else 'K8s manifests'}: `k8s/` (Kustomize overlays)"),
            (f"{'运维脚本' if zh else 'Scripts'}: `scripts/`"),
        ],
    }


# 精简的预设工厂注册表（其余预设复用结构，此处只注册最关键的两个作为演示，其他走通用路径）
PRESET_FACTORIES = {
    "go-api":       _go_api_preset,
    "devops":       _devops_preset,
}

# 简单预设 — 基于旧格式的预设直接嵌入（保持向后兼容、精简代码量）
# 这里只保留 key→描述映射，实际数据在 _get_preset() 中按需加载
_SIMPLE_PRESET_META = {
    "go-cli":        ("Go CLI 工具",                "Go CLI Tool"),
    "python-api":    ("Python FastAPI 后端",        "Python FastAPI Backend"),
    "python-data":   ("Python 数据工程",            "Python Data Engineering"),
    "fullstack":     ("全栈 Web 应用",              "Full-Stack Web App"),
    "microservice":  ("微服务架构",                  "Microservices"),
    "monorepo":      ("Monorepo 多模块",            "Monorepo"),
    "k8s-operator":  ("Kubernetes Operator",        "Kubernetes Operator"),
    "terraform":     ("Terraform IaC",              "Terraform IaC"),
}


def _get_preset(name: str) -> Optional[dict]:
    """获取预设配置"""
    if name in PRESET_FACTORIES:
        return PRESET_FACTORIES[name](_LANG)
    # 未独立实现的预设，返回 None 让调用方提示用户
    return None


# ============================================================================
# 交互式向导
# ============================================================================

def wizard():
    print(hdr("🧙 CLAUDE.md " + L("交互式生成向导", "Interactive Generator")))
    print(f"  {c(L('按步骤回答，生成适合你项目的 CLAUDE.md', 'Answer step by step to generate your CLAUDE.md'), C.DIM)}")
    print(f"  {c(L('回车使用默认值，Ctrl+C 退出', 'Enter for defaults, Ctrl+C to exit'), C.DIM)}")

    # Step 0: 选语言
    print(sub(L("语言选择", "Language Selection")))
    lang_choice = ask_multi(L("CLAUDE.md 输出语言", "CLAUDE.md output language"), [
        ("zh", "中文"),
        ("en", "English"),
    ], default="zh")
    set_lang(lang_choice)

    # Step 1: 选角色
    print(sub(L("角色选择", "Role Selection")))
    print(f"  {c(L('不同角色会有不同的引导步骤和默认内容', 'Different roles have different wizard steps'), C.DIM)}")
    role_options = [(rd["key"], rd[f"label_{_LANG}"]) for rd in ROLE_DEFS.values()]
    role_key = ask_multi(L("你的角色", "Your role"), role_options, default="go_backend")

    role_def = ROLE_DEFS[role_key]
    cfg = {
        "role": role_def[f"role_{_LANG}"] or role_def["role_en"],
    }

    # 自定义角色
    if role_key == "custom":
        cfg["role"] = ask(L("描述你的角色", "Describe your role"))

    # 角色特征
    print(f"\n  {c(L('为角色补充额外要求（可选，空行跳过）', 'Add extra persona requirements (optional, empty to skip)'), C.DIM)}")
    extras = ask_lines(L("角色特征", "Persona extras"))
    cfg["persona_extras"] = extras

    # 按角色的 wizard_steps 执行
    steps = role_def["wizard_steps"]
    total = len(steps)
    for i, step_name in enumerate(steps, 1):
        step_fn = STEP_REGISTRY.get(step_name)
        if step_fn:
            print(f"\n  {c(f'[{i}/{total}]', C.DIM)}")
            step_fn(cfg)

    # 自动填充 thinking_strategy 和 verification（如果向导中用户未填）
    if "thinking_strategy" not in cfg:
        cfg["thinking_strategy"] = [
            L("接到复杂任务时，先规划方案再实现", "For complex tasks, plan before implementing"),
            L("不确定项目约定时，先搜索现有代码参考", "When unsure about conventions, search existing code first"),
            L("修改公共接口前，先查找所有调用方评估影响", "Before changing interfaces, grep callers to assess impact"),
        ]
    if "verification" not in cfg:
        cfg["verification"] = []
        if any("go" in str(cfg.get("tech_items", [])).lower() for _ in [1]):
            cfg["verification"] = [
                L("lint 检查通过", "Lint checks pass"),
                L("测试全部通过", "All tests pass"),
                L("编译成功", "Build succeeds"),
                L("没有硬编码密钥", "No hardcoded secrets"),
            ]

    return cfg


# ============================================================================
# 输出与保存
# ============================================================================

def preview_and_save(content: str, default_path: str = "CLAUDE.md"):
    lines = content.split("\n")
    print(hdr(L("✅ 生成完成", "✅ Generation Complete")))
    print(f"  {L('行数','Lines')}: {c(str(len(lines)), C.YLW)} | {L('字符','Chars')}: {c(str(len(content)), C.YLW)}")
    print()
    border = c("─" * 60, C.DIM)
    print(f"  {border}")
    for line in lines[:50]:
        print(f"  │ {line}")
    if len(lines) > 50:
        remaining = len(lines) - 50
        print(f"  │ {c(f'... ({remaining} more lines)', C.DIM)}")
    print(f"  {border}")

    print(sub(L("保存", "Save")))
    print(f"  {c('[1]', C.CYN)} {L('保存到当前目录', 'Save to current directory')} ({default_path})")
    print(f"  {c('[2]', C.CYN)} {L('保存到指定路径', 'Save to custom path')}")
    print(f"  {c('[3]', C.CYN)} {L('输出到终端', 'Print to terminal')}")
    print(f"  {c('[Enter]', C.CYN)} {L('退出', 'Exit')}")

    choice = input(f"\n  {L('选择','Choose')}: ").strip()
    if choice == "1":
        Path(default_path).write_text(content, encoding="utf-8")
        print(c(f"\n  ✅ {L('已保存到','Saved to')} ./{default_path}", C.GRN))
        print(f"  {c(L('提示：提交到 git 让团队共享', 'Tip: commit to git for team sharing'), C.DIM)}")
    elif choice == "2":
        path = input(f"  {L('路径','Path')}: ").strip() or default_path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        print(c(f"\n  ✅ {L('已保存到','Saved to')} {path}", C.GRN))
    elif choice == "3":
        print("\n" + content)


# ============================================================================
# CLI 子命令
# ============================================================================

def cmd_wizard():
    try:
        cfg = wizard()
        content = assemble(cfg)
        preview_and_save(content)
    except KeyboardInterrupt:
        print(c(f"\n\n  {L('已取消。','Cancelled.')}", C.YLW))

def cmd_quick(preset_name: str):
    preset = _get_preset(preset_name)
    if preset is None:
        print(c(f"\n  ❌ {L('预设','Preset')} '{preset_name}' {L('暂未内置详细配置，请使用 wizard 自定义生成','not yet fully built-in. Use wizard for custom generation.')}", C.YLW))
        print(f"  {L('已内置详细配置的预设','Fully built presets')}: {', '.join(c(k, C.CYN) for k in PRESET_FACTORIES)}")
        print(f"  {L('全部预设名称','All preset names')}: {', '.join(c(k, C.CYN) for k in list(PRESET_FACTORIES) + list(_SIMPLE_PRESET_META))}")
        return
    content = assemble(preset)
    preview_and_save(content)

def cmd_presets():
    print(hdr(L("📦 可用预设模板", "📦 Available Presets")))
    for key in PRESET_FACTORIES:
        p = PRESET_FACTORIES[key](_LANG)
        print(f"  {c(key, C.CYN + C.B):<24} {p['project_desc']}  {c('✅', C.GRN)}")
    for key, (zh_desc, en_desc) in _SIMPLE_PRESET_META.items():
        desc = zh_desc if _LANG == "zh" else en_desc
        print(f"  {c(key, C.CYN + C.B):<24} {desc}  {c(L('(待完善)', '(coming)'), C.DIM)}")
    print(f"\n  {L('使用方法','Usage')}: {c('python claudemd_generator.py quick <preset>', C.DIM)}")
    print(f"  {L('英文输出','English')}: {c('python claudemd_generator.py quick <preset> --en', C.DIM)}")

def cmd_example():
    print(hdr(L("📄 完整示例 (go-api)", "📄 Full Example (go-api)")))
    content = assemble(_go_api_preset(_LANG))
    print(content)

def cmd_help():
    print(__doc__)

# ============================================================================
# 主入口
# ============================================================================
def print_banner():
    banner = r"""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   📋  CLAUDE.md Generator v2                          ║
    ║   ──────────────────────────                          ║
    ║   为 Claude Code 生成高质量项目配置文件                  ║
    ║   支持中/英文 · 按角色差异化引导 · 深度驱动                ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(c(banner, C.CYN))

def main():
    # 解析全局 --en 参数
    if "--en" in sys.argv:
        set_lang("en")
        sys.argv.remove("--en")

    if len(sys.argv) <= 1:
        print_banner()
        print(f"  {c('[1]', C.CYN)} 🧙 {L('交互式向导（按角色引导）','Interactive Wizard (role-aware)')}")
        print(f"  {c('[2]', C.CYN)} ⚡ {L('快速预设生成','Quick Preset')}")
        print(f"  {c('[3]', C.CYN)} 📦 {L('查看所有预设','List Presets')}")
        print(f"  {c('[4]', C.CYN)} 📄 {L('查看完整示例','Full Example')}")
        print(f"  {c('[h]', C.CYN)} {L('帮助','Help')}")
        print(f"  {c('[q]', C.CYN)} {L('退出','Quit')}")

        choice = input(f"\n  {L('请选择','Choose')}: ").strip().lower()
        if choice == "1":
            cmd_wizard()
        elif choice == "2":
            cmd_presets()
            print()
            preset = input(f"  {L('输入预设名称','Enter preset name')}: ").strip()
            if preset:
                cmd_quick(preset)
        elif choice == "3":
            cmd_presets()
        elif choice == "4":
            cmd_example()
        elif choice in ("h", "help"):
            cmd_help()
        elif choice in ("q", "quit", "exit"):
            print(c(f"\n  👋 {L('再见！','Bye!')}", C.GRN))
        return

    command = sys.argv[1].lower()
    if command in ("wizard", "w"):
        cmd_wizard()
    elif command in ("quick", "q"):
        if len(sys.argv) < 3:
            cmd_presets()
            return
        cmd_quick(sys.argv[2])
    elif command in ("presets", "p", "list", "ls"):
        cmd_presets()
    elif command in ("example", "ex"):
        cmd_example()
    elif command in ("help", "h", "-h", "--help"):
        cmd_help()
    else:
        print(c(f"  {L('未知命令','Unknown command')}: {command}", C.RED))
        cmd_help()


if __name__ == "__main__":
    main()

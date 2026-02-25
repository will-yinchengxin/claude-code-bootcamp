#!/Users/yinchengxin/miniconda/bin/python
"""
Prompt Generator - 后端工程师日常开发运维 Prompt 生成工具
==========================================================
功能:
  1. 内置 20+ 后端开发/运维场景的 Prompt 模板
  2. 交互式 Prompt 构建器（自定义角色、上下文、任务、格式）
  3. 模板变量自动替换
  4. 搜索/过滤模板
  5. 导出为文件或复制到剪贴板
  6. 支持自定义模板管理（增删改查）

用法:
  python prompt_generator.py              # 交互式菜单
  python prompt_generator.py list         # 列出所有模板
  python prompt_generator.py search 数据库  # 搜索模板
  python prompt_generator.py use code_review  # 使用指定模板
  python prompt_generator.py build        # 从零构建 Prompt
  python prompt_generator.py export       # 导出所有模板
"""

import json
import os
import sys
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# ANSI 颜色常量
# ============================================================================

class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    BG_BLUE = "\033[44m"

def c(text: str, color: str) -> str:
    """给文本加颜色"""
    return f"{color}{text}{Colors.RESET}"

def header(text: str) -> str:
    return c(f"\n{'='*60}\n  {text}\n{'='*60}", Colors.CYAN + Colors.BOLD)

def subheader(text: str) -> str:
    return c(f"\n--- {text} ---", Colors.YELLOW)

# ============================================================================
# 内置 Prompt 模板
# ============================================================================

BUILTIN_TEMPLATES: dict[str, dict] = {
    # ---- 代码开发类 ----
    "code_review": {
        "name": "代码审查",
        "category": "开发",
        "description": "全方位代码审查（安全、性能、可维护性、并发）",
        "variables": ["language", "code"],
        "template": textwrap.dedent("""\
            请审查以下 {language} 代码，从这些维度进行评估：

            1. **安全性**：SQL注入、XSS、敏感信息泄露、权限校验缺失
            2. **性能**：N+1 查询、内存泄漏、不必要的拷贝、算法复杂度
            3. **可维护性**：命名规范、函数拆分、错误处理、代码重复
            4. **并发安全**：数据竞争、死锁风险、goroutine 泄漏

            对每个问题：
            - 指出具体位置（行号或函数名）
            - 说明风险等级（高/中/低）
            - 给出修复后的代码

            <code>
            {code}
            </code>"""),
    },
    "api_design": {
        "name": "RESTful API 设计",
        "category": "开发",
        "description": "设计规范的 RESTful API 接口",
        "variables": ["resource", "tech_stack", "requirements"],
        "template": textwrap.dedent("""\
            请为 {resource} 资源设计一套完整的 RESTful API。

            技术栈：{tech_stack}

            业务需求：
            {requirements}

            请输出：
            1. API 端点列表（方法 + 路径 + 说明）
            2. 请求/响应的 JSON Schema
            3. 错误码定义
            4. 认证/授权方案
            5. 分页、过滤、排序的参数设计
            6. 示例的 cURL 请求"""),
    },
    "write_function": {
        "name": "编写函数/方法",
        "category": "开发",
        "description": "按需求编写高质量函数",
        "variables": ["language", "function_desc", "constraints"],
        "template": textwrap.dedent("""\
            请用 {language} 编写一个函数，功能如下：

            {function_desc}

            约束条件：
            {constraints}

            要求：
            - 包含完整的错误处理
            - 添加必要的注释
            - 编写对应的单元测试（至少覆盖正常路径 + 2 个边界情况）
            - 分析时间和空间复杂度"""),
    },
    "debug_help": {
        "name": "调试求助",
        "category": "开发",
        "description": "分析错误日志或异常行为",
        "variables": ["language", "error_info", "code_context"],
        "template": textwrap.dedent("""\
            我在 {language} 项目中遇到以下问题，请帮我分析。

            错误信息/异常表现：
            {error_info}

            相关代码：
            <code>
            {code_context}
            </code>

            请：
            1. 分析错误的根本原因
            2. 给出修复方案（附代码）
            3. 解释为什么会出现这个问题
            4. 建议如何避免类似问题再次发生"""),
    },
    "unit_test": {
        "name": "编写单元测试",
        "category": "开发",
        "description": "为已有代码生成完整的单元测试",
        "variables": ["language", "test_framework", "code"],
        "template": textwrap.dedent("""\
            请为以下 {language} 代码编写单元测试。

            测试框架：{test_framework}

            <code>
            {code}
            </code>

            要求：
            - 覆盖所有公开方法
            - 包含正常路径、边界情况、错误路径的测试用例
            - 使用 Table-Driven 测试风格（如果语言支持）
            - Mock 外部依赖
            - 每个测试用例有清晰的命名，说明测试意图"""),
    },
    "refactor": {
        "name": "代码重构",
        "category": "开发",
        "description": "分析并重构代码以提升质量",
        "variables": ["language", "refactor_goal", "code"],
        "template": textwrap.dedent("""\
            请重构以下 {language} 代码。

            重构目标：{refactor_goal}

            <code>
            {code}
            </code>

            请：
            1. 指出当前代码的问题
            2. 给出重构后的完整代码
            3. 解释每个重构决策的理由
            4. 确保重构后功能不变（列出需要验证的测试点）"""),
    },

    # ---- 数据库类 ----
    "sql_optimize": {
        "name": "SQL 优化",
        "category": "数据库",
        "description": "分析并优化 SQL 查询性能",
        "variables": ["database", "sql", "table_schema"],
        "template": textwrap.dedent("""\
            请优化以下 SQL 查询。

            数据库：{database}

            表结构：
            {table_schema}

            待优化 SQL：
            ```sql
            {sql}
            ```

            请：
            1. 分析当前 SQL 的执行计划（预估）
            2. 指出性能瓶颈
            3. 给出优化后的 SQL
            4. 建议需要添加的索引
            5. 如果数据量很大，给出分页/分批方案"""),
    },
    "db_schema_design": {
        "name": "数据库表设计",
        "category": "数据库",
        "description": "根据业务需求设计数据库 Schema",
        "variables": ["database", "business_desc", "scale"],
        "template": textwrap.dedent("""\
            请根据以下业务需求设计数据库表结构。

            数据库类型：{database}
            业务描述：{business_desc}
            预估数据规模：{scale}

            请输出：
            1. 完整的 CREATE TABLE DDL
            2. 索引设计及理由
            3. 表关系 ER 图（用 mermaid 语法）
            4. 针对高频查询的优化建议
            5. 数据归档/分表策略（如果需要）"""),
    },

    # ---- 运维/DevOps 类 ----
    "incident_analysis": {
        "name": "故障排查",
        "category": "运维",
        "description": "系统故障的根因分析和应急处理",
        "variables": ["symptom", "environment", "known_info"],
        "template": textwrap.dedent("""\
            <role>你是一个资深 SRE 工程师</role>

            <incident>
            现象：{symptom}
            环境：{environment}
            已知信息：{known_info}
            </incident>

            请按以下步骤处理：
            1. 列出可能的根因（按概率从高到低排序）
            2. 对每个根因给出验证命令或排查步骤
            3. 给出临时缓解措施（止血）
            4. 给出根本修复方案
            5. 建议后续的预防措施和监控告警配置"""),
    },
    "dockerfile": {
        "name": "Dockerfile 编写",
        "category": "运维",
        "description": "编写生产级 Dockerfile",
        "variables": ["language", "app_desc", "requirements"],
        "template": textwrap.dedent("""\
            请为以下应用编写生产级 Dockerfile。

            语言/框架：{language}
            应用描述：{app_desc}
            特殊要求：{requirements}

            要求：
            - 使用多阶段构建，最小化镜像体积
            - 使用非 root 用户运行
            - 合理利用缓存层
            - 包含健康检查
            - 添加必要的 LABEL
            - 附带 .dockerignore 文件内容
            - 给出构建和运行命令"""),
    },
    "k8s_manifest": {
        "name": "K8s 资源清单",
        "category": "运维",
        "description": "生成 Kubernetes 部署资源清单",
        "variables": ["app_name", "image", "requirements"],
        "template": textwrap.dedent("""\
            请为应用 {app_name} 生成 Kubernetes 部署清单。

            镜像：{image}
            要求：{requirements}

            请生成以下资源的 YAML：
            1. Deployment（含资源限制、健康检查、滚动更新策略）
            2. Service
            3. HPA（自动伸缩）
            4. ConfigMap / Secret（如需要）
            5. Ingress（如需要）

            每个资源附带关键配置项的注释说明。"""),
    },
    "cicd_pipeline": {
        "name": "CI/CD 流水线",
        "category": "运维",
        "description": "设计 CI/CD 流水线配置",
        "variables": ["ci_platform", "tech_stack", "requirements"],
        "template": textwrap.dedent("""\
            请为以下项目设计 CI/CD 流水线。

            CI 平台：{ci_platform}
            技术栈：{tech_stack}
            要求：{requirements}

            请输出：
            1. 完整的流水线配置文件
            2. 各阶段说明（lint → test → build → deploy）
            3. 缓存优化策略
            4. 安全扫描集成
            5. 环境分支策略（dev/staging/prod）"""),
    },
    "nginx_config": {
        "name": "Nginx 配置",
        "category": "运维",
        "description": "生成 Nginx 配置文件",
        "variables": ["scenario", "requirements"],
        "template": textwrap.dedent("""\
            请生成 Nginx 配置文件。

            使用场景：{scenario}
            具体要求：{requirements}

            请输出：
            - 完整的可直接使用的 nginx.conf
            - 关键配置项的注释说明
            - 性能调优建议
            - 安全加固建议（如 Header 设置、限流等）"""),
    },
    "monitoring_alert": {
        "name": "监控告警配置",
        "category": "运维",
        "description": "设计监控指标和告警规则",
        "variables": ["system", "monitoring_tool", "sla"],
        "template": textwrap.dedent("""\
            请为 {system} 设计监控和告警方案。

            监控工具：{monitoring_tool}
            SLA 要求：{sla}

            请输出：
            1. 关键监控指标列表（黄金信号：延迟、流量、错误率、饱和度）
            2. 告警规则配置（含阈值、持续时间、告警等级）
            3. Dashboard 设计建议
            4. 告警通知策略（升级路径）
            5. 常见的误报场景和处理建议"""),
    },

    # ---- 架构/设计类 ----
    "system_design": {
        "name": "系统架构设计",
        "category": "架构",
        "description": "系统级架构设计方案",
        "variables": ["system_name", "business_scenario", "nfr"],
        "template": textwrap.dedent("""\
            请设计 {system_name} 的系统架构方案。

            业务场景：{business_scenario}

            非功能性需求：
            {nfr}

            请输出：
            1. 架构概览图（mermaid 语法）
            2. 核心组件设计及职责
            3. 数据流说明
            4. 关键技术选型（对比至少 2 个选项，说明取舍）
            5. 容量规划
            6. 高可用和容灾方案
            7. 潜在风险及应对措施"""),
    },
    "tech_selection": {
        "name": "技术选型对比",
        "category": "架构",
        "description": "对比分析多种技术方案",
        "variables": ["scenario", "candidates", "constraints"],
        "template": textwrap.dedent("""\
            场景：{scenario}
            候选方案：{candidates}
            约束条件：{constraints}

            请从以下维度对比分析：
            1. 功能满足度
            2. 性能表现
            3. 学习曲线和社区生态
            4. 运维复杂度
            5. 成本（许可证/资源消耗）
            6. 团队现有经验匹配度

            输出格式：对比表格 + 最终推荐 + 推荐理由"""),
    },

    # ---- 文档/沟通类 ----
    "tech_doc": {
        "name": "技术文档",
        "category": "文档",
        "description": "生成技术设计文档或 README",
        "variables": ["doc_type", "project", "content_scope"],
        "template": textwrap.dedent("""\
            请为 {project} 编写 {doc_type}。

            需要覆盖的内容：{content_scope}

            要求：
            - 语言简洁专业
            - 包含代码示例
            - 使用 Markdown 格式
            - 适合团队内部共享阅读"""),
    },
    "commit_message": {
        "name": "Git Commit Message",
        "category": "文档",
        "description": "根据代码变更生成规范的 Commit Message",
        "variables": ["changes"],
        "template": textwrap.dedent("""\
            请根据以下代码变更生成符合 Conventional Commits 规范的 commit message。

            变更内容：
            {changes}

            格式要求：
            - type(scope): subject
            - 空行
            - body（解释 what 和 why，不是 how）
            - 空行
            - footer（Breaking Changes, Issue 引用等）

            type 选择：feat/fix/refactor/perf/test/docs/chore/ci
            subject: 不超过 50 个字符，使用祈使语气"""),
    },
    "explain_code": {
        "name": "代码解释",
        "category": "开发",
        "description": "解释复杂代码的工作原理",
        "variables": ["language", "code"],
        "template": textwrap.dedent("""\
            请详细解释以下 {language} 代码的工作原理。

            <code>
            {code}
            </code>

            请：
            1. 概述这段代码的整体功能
            2. 逐段解释关键逻辑
            3. 说明使用了哪些设计模式或编程技巧
            4. 指出潜在的问题或可以改进的地方
            5. 用通俗易懂的语言，假设读者有基本编程基础但不熟悉这个领域"""),
    },

    # ---- 通用类 ----
    "general_query": {
        "name": "通用技术查询",
        "category": "通用",
        "description": "通用的技术问题查询模板",
        "variables": ["topic", "specific_question", "context"],
        "template": textwrap.dedent("""\
            <role>你是一个资深全栈工程师，擅长 {topic}</role>

            <context>
            {context}
            </context>

            <question>
            {specific_question}
            </question>

            请：
            - 直接回答问题
            - 给出具体的代码示例或命令
            - 如有多种方案，说明各自的优缺点
            - 注明适用的版本或环境"""),
    },
    "performance_optimize": {
        "name": "性能优化",
        "category": "开发",
        "description": "分析和优化系统/代码性能",
        "variables": ["system_desc", "current_metrics", "target_metrics"],
        "template": textwrap.dedent("""\
            请帮我优化以下系统的性能。

            系统描述：{system_desc}
            当前性能指标：{current_metrics}
            目标性能指标：{target_metrics}

            请：
            1. 分析当前瓶颈点
            2. 按投入产出比排序给出优化方案
            3. 每个方案包含：具体操作步骤、预期提升、风险评估
            4. 给出性能测试/压测方案来验证优化效果"""),
    },
}

# ============================================================================
# 自定义模板存储
# ============================================================================

CUSTOM_TEMPLATES_FILE = Path.home() / ".prompt_generator" / "custom_templates.json"

def load_custom_templates() -> dict:
    """加载用户自定义模板"""
    if CUSTOM_TEMPLATES_FILE.exists():
        try:
            return json.loads(CUSTOM_TEMPLATES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_custom_templates(templates: dict):
    """保存用户自定义模板"""
    CUSTOM_TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_TEMPLATES_FILE.write_text(
        json.dumps(templates, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def get_all_templates() -> dict:
    """获取所有模板（内置 + 自定义）"""
    templates = dict(BUILTIN_TEMPLATES)
    templates.update(load_custom_templates())
    return templates

# ============================================================================
# 核心功能
# ============================================================================

def list_templates(category_filter: Optional[str] = None):
    """列出所有模板"""
    templates = get_all_templates()
    categories: dict[str, list] = {}

    for key, tpl in templates.items():
        cat = tpl.get("category", "未分类")
        if category_filter and cat != category_filter:
            continue
        categories.setdefault(cat, []).append((key, tpl))

    print(header("📋 Prompt 模板列表"))

    if not categories:
        print(c("  没有找到匹配的模板", Colors.DIM))
        return

    for cat, items in sorted(categories.items()):
        print(c(f"\n  【{cat}】", Colors.GREEN + Colors.BOLD))
        for key, tpl in items:
            is_custom = key not in BUILTIN_TEMPLATES
            tag = c(" [自定义]", Colors.MAGENTA) if is_custom else ""
            print(f"    {c(key, Colors.CYAN):<40} {tpl['name']}{tag}")
            print(f"    {' ' * 24}{c(tpl['description'], Colors.DIM)}")

    print(f"\n  共 {c(str(sum(len(v) for v in categories.values())), Colors.YELLOW)} 个模板")
    print(f"  使用方法: {c('python prompt_generator.py use <模板ID>', Colors.DIM)}")

def search_templates(keyword: str):
    """搜索模板"""
    templates = get_all_templates()
    keyword_lower = keyword.lower()
    results = []

    for key, tpl in templates.items():
        searchable = f"{key} {tpl['name']} {tpl['description']} {tpl['category']} {tpl['template']}".lower()
        if keyword_lower in searchable:
            results.append((key, tpl))

    print(header(f"🔍 搜索结果: '{keyword}'"))

    if not results:
        print(c(f"  没有找到包含 '{keyword}' 的模板", Colors.YELLOW))
        print(f"  试试用其他关键词，或者输入 {c('list', Colors.CYAN)} 查看所有模板")
        return

    for key, tpl in results:
        print(f"\n  {c(key, Colors.CYAN + Colors.BOLD)} - {tpl['name']}")
        print(f"  分类: {c(tpl['category'], Colors.GREEN)}  |  {tpl['description']}")
        vars_str = ", ".join(f"{{{v}}}" for v in tpl.get("variables", []))
        print(f"  变量: {c(vars_str, Colors.YELLOW)}")

    print(f"\n  找到 {c(str(len(results)), Colors.GREEN)} 个匹配模板")

def use_template(template_id: str):
    """交互式使用模板"""
    templates = get_all_templates()

    if template_id not in templates:
        print(c(f"\n  ❌ 模板 '{template_id}' 不存在", Colors.RED))
        # 模糊搜索建议
        suggestions = [k for k in templates if template_id.lower() in k.lower()]
        if suggestions:
            print(f"  你是不是要找: {', '.join(c(s, Colors.CYAN) for s in suggestions)}")
        return

    tpl = templates[template_id]
    print(header(f"📝 使用模板: {tpl['name']}"))
    print(f"  {c(tpl['description'], Colors.DIM)}")
    print(f"  分类: {c(tpl['category'], Colors.GREEN)}")

    # 收集变量值
    variables = tpl.get("variables", [])
    values = {}

    if variables:
        print(subheader("请填写以下变量（支持多行输入，空行结束）"))

        for var in variables:
            print(f"\n  {c(f'{{{var}}}', Colors.YELLOW)}: ", end="")
            # 对于可能需要多行输入的变量
            if var in ("code", "code_context", "sql", "table_schema", "changes",
                       "requirements", "nfr", "error_info", "known_info",
                       "content_scope", "business_desc"):
                print(c("(多行输入，输入空行结束)", Colors.DIM))
                lines = []
                while True:
                    line = input("  > ")
                    if line == "":
                        break
                    lines.append(line)
                values[var] = "\n".join(lines)
            else:
                values[var] = input("")

    # 渲染 Prompt
    try:
        rendered = tpl["template"]
        for var, val in values.items():
            rendered = rendered.replace(f"{{{var}}}", val)
    except KeyError as e:
        print(c(f"\n  ❌ 缺少变量: {e}", Colors.RED))
        return

    # 显示结果
    print(header("✅ 生成的 Prompt"))
    print()

    # 带框显示
    border = c("─" * 60, Colors.DIM)
    print(f"  {border}")
    for line in rendered.split("\n"):
        print(f"  │ {line}")
    print(f"  {border}")

    # 操作选项
    print(subheader("操作"))
    print(f"  {c('[1]', Colors.CYAN)} 复制到剪贴板")
    print(f"  {c('[2]', Colors.CYAN)} 保存到文件")
    print(f"  {c('[3]', Colors.CYAN)} 重新生成（修改变量）")
    print(f"  {c('[Enter]', Colors.CYAN)} 返回")

    choice = input(f"\n  请选择: ").strip()

    if choice == "1":
        try:
            import subprocess
            # 尝试多种剪贴板工具
            for cmd in [["pbcopy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    process.communicate(rendered.encode("utf-8"))
                    if process.returncode == 0:
                        print(c("\n  ✅ 已复制到剪贴板！", Colors.GREEN))
                        return
                except FileNotFoundError:
                    continue
            # Windows
            try:
                process = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
                process.communicate(rendered.encode("utf-16le"))
                print(c("\n  ✅ 已复制到剪贴板！", Colors.GREEN))
                return
            except FileNotFoundError:
                pass
            print(c("\n  ⚠️  未找到剪贴板工具，请手动复制上方内容", Colors.YELLOW))
        except Exception as e:
            print(c(f"\n  ⚠️  复制失败: {e}", Colors.YELLOW))

    elif choice == "2":
        filename = input(f"  文件名 (默认 prompt_{template_id}.md): ").strip()
        if not filename:
            filename = f"prompt_{template_id}.md"
        filepath = Path(filename)
        filepath.write_text(rendered, encoding="utf-8")
        print(c(f"\n  ✅ 已保存到 {filepath.absolute()}", Colors.GREEN))

    elif choice == "3":
        use_template(template_id)

def build_prompt():
    """交互式从零构建 Prompt"""
    print(header("🔨 Prompt 构建器"))
    print(f"  {c('按步骤构建一个自定义 Prompt，每步可留空跳过', Colors.DIM)}")

    # 步骤 1: 角色
    print(subheader("步骤 1/5: 角色设定 (Role)"))
    print(f"  {c('示例: 你是一个资深的 Go 后端工程师', Colors.DIM)}")
    role = input("  角色: ").strip()

    # 步骤 2: 上下文
    print(subheader("步骤 2/5: 上下文 (Context)"))
    print(f"  {c('提供背景信息，如技术栈、业务场景、约束条件等', Colors.DIM)}")
    print(f"  {c('多行输入，空行结束', Colors.DIM)}")
    context_lines = []
    while True:
        line = input("  > ")
        if line == "":
            break
        context_lines.append(line)
    context = "\n".join(context_lines)

    # 步骤 3: 任务
    print(subheader("步骤 3/5: 任务 (Task)"))
    print(f"  {c('明确告诉 AI 要做什么', Colors.DIM)}")
    print(f"  {c('多行输入，空行结束', Colors.DIM)}")
    task_lines = []
    while True:
        line = input("  > ")
        if line == "":
            break
        task_lines.append(line)
    task = "\n".join(task_lines)

    # 步骤 4: 输出格式
    print(subheader("步骤 4/5: 输出格式 (Format)"))
    print(f"  {c('指定期望的输出结构和形式', Colors.DIM)}")
    print(f"  {c('示例: 用代码块输出，附带注释；输出为JSON；用表格对比', Colors.DIM)}")
    fmt = input("  格式: ").strip()

    # 步骤 5: 额外约束
    print(subheader("步骤 5/5: 额外约束 (Constraints)"))
    print(f"  {c('其他限制条件，如不要用第三方库、保持简洁等', Colors.DIM)}")
    constraints = input("  约束: ").strip()

    # 选择风格
    print(subheader("选择 Prompt 风格"))
    print(f"  {c('[1]', Colors.CYAN)} XML 标签风格 (适合 Claude)")
    print(f"  {c('[2]', Colors.CYAN)} Markdown 风格 (通用)")
    print(f"  {c('[3]', Colors.CYAN)} 纯文本风格 (简洁)")
    style = input("  选择 [1/2/3，默认1]: ").strip() or "1"

    # 构建 Prompt
    if style == "1":
        prompt = _build_xml_style(role, context, task, fmt, constraints)
    elif style == "2":
        prompt = _build_markdown_style(role, context, task, fmt, constraints)
    else:
        prompt = _build_plain_style(role, context, task, fmt, constraints)

    # 显示结果
    print(header("✅ 生成的 Prompt"))
    print()
    border = c("─" * 60, Colors.DIM)
    print(f"  {border}")
    for line in prompt.split("\n"):
        print(f"  │ {line}")
    print(f"  {border}")

    # 保存选项
    print(subheader("操作"))
    print(f"  {c('[1]', Colors.CYAN)} 保存为自定义模板")
    print(f"  {c('[2]', Colors.CYAN)} 保存到文件")
    print(f"  {c('[Enter]', Colors.CYAN)} 返回")

    choice = input(f"\n  请选择: ").strip()
    if choice == "1":
        _save_as_custom_template(prompt, role)
    elif choice == "2":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = input(f"  文件名 (默认 prompt_{ts}.md): ").strip()
        if not filename:
            filename = f"prompt_{ts}.md"
        Path(filename).write_text(prompt, encoding="utf-8")
        print(c(f"\n  ✅ 已保存到 {Path(filename).absolute()}", Colors.GREEN))

def _build_xml_style(role, context, task, fmt, constraints) -> str:
    parts = []
    if role:
        parts.append(f"<role>{role}</role>")
    if context:
        parts.append(f"\n<context>\n{context}\n</context>")
    if task:
        parts.append(f"\n<task>\n{task}\n</task>")
    if fmt:
        parts.append(f"\n<output_format>{fmt}</output_format>")
    if constraints:
        parts.append(f"\n<constraints>{constraints}</constraints>")
    return "\n".join(parts)

def _build_markdown_style(role, context, task, fmt, constraints) -> str:
    parts = []
    if role:
        parts.append(f"## 角色\n{role}")
    if context:
        parts.append(f"\n## 上下文\n{context}")
    if task:
        parts.append(f"\n## 任务\n{task}")
    if fmt:
        parts.append(f"\n## 输出格式\n{fmt}")
    if constraints:
        parts.append(f"\n## 约束条件\n{constraints}")
    return "\n".join(parts)

def _build_plain_style(role, context, task, fmt, constraints) -> str:
    parts = []
    if role:
        parts.append(role)
    if context:
        parts.append(f"\n背景信息：\n{context}")
    if task:
        parts.append(f"\n请完成以下任务：\n{task}")
    if fmt:
        parts.append(f"\n输出要求：{fmt}")
    if constraints:
        parts.append(f"\n注意：{constraints}")
    return "\n".join(parts)

def _save_as_custom_template(prompt: str, role: str):
    """将构建的 Prompt 保存为自定义模板"""
    print(subheader("保存为自定义模板"))
    template_id = input("  模板 ID (英文，如 my_debug): ").strip()
    if not template_id or not re.match(r'^[a-zA-Z_]\w*$', template_id):
        print(c("  ❌ 无效的模板 ID，请使用英文字母和下划线", Colors.RED))
        return

    name = input("  模板名称 (中文): ").strip() or template_id
    category = input("  分类 (开发/运维/架构/文档/通用): ").strip() or "自定义"
    description = input("  描述: ").strip() or "自定义模板"

    # 提取变量（花括号中的内容）
    variables = list(set(re.findall(r'\{(\w+)\}', prompt)))

    custom_templates = load_custom_templates()
    custom_templates[template_id] = {
        "name": name,
        "category": category,
        "description": description,
        "variables": variables,
        "template": prompt,
    }
    save_custom_templates(custom_templates)
    print(c(f"\n  ✅ 已保存自定义模板: {template_id}", Colors.GREEN))
    print(f"  存储位置: {c(str(CUSTOM_TEMPLATES_FILE), Colors.DIM)}")

def export_templates():
    """导出所有模板"""
    templates = get_all_templates()
    output_lines = [
        "# Prompt 模板导出",
        f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# 模板总数: {len(templates)}",
        "",
    ]

    categories: dict[str, list] = {}
    for key, tpl in templates.items():
        categories.setdefault(tpl.get("category", "未分类"), []).append((key, tpl))

    for cat, items in sorted(categories.items()):
        output_lines.append(f"\n## {cat}\n")
        for key, tpl in items:
            output_lines.append(f"### {tpl['name']} (`{key}`)")
            output_lines.append(f"> {tpl['description']}")
            output_lines.append(f"> 变量: {', '.join(f'`{{{v}}}`' for v in tpl.get('variables', []))}")
            output_lines.append(f"\n```\n{tpl['template']}\n```\n")

    filename = f"prompt_templates_export_{datetime.now().strftime('%Y%m%d')}.md"
    Path(filename).write_text("\n".join(output_lines), encoding="utf-8")
    print(c(f"\n  ✅ 已导出到 {Path(filename).absolute()}", Colors.GREEN))
    print(f"  共 {len(templates)} 个模板")

def delete_custom_template():
    """删除自定义模板"""
    custom = load_custom_templates()
    if not custom:
        print(c("\n  没有自定义模板可删除", Colors.YELLOW))
        return

    print(subheader("自定义模板列表"))
    for key, tpl in custom.items():
        print(f"  {c(key, Colors.CYAN)} - {tpl['name']}")

    template_id = input("\n  输入要删除的模板 ID: ").strip()
    if template_id in custom:
        confirm = input(f"  确认删除 {c(template_id, Colors.RED)}? [y/N]: ").strip().lower()
        if confirm == "y":
            del custom[template_id]
            save_custom_templates(custom)
            print(c(f"\n  ✅ 已删除模板: {template_id}", Colors.GREEN))
        else:
            print("  取消删除")
    else:
        print(c(f"  ❌ 未找到模板: {template_id}", Colors.RED))

# ============================================================================
# 主菜单
# ============================================================================

def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║   🤖  Prompt Generator                               ║
    ║   ─────────────────────────────                      ║
    ║   后端工程师的 Prompt 生成工具                          ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(c(banner, Colors.CYAN))

def interactive_menu():
    """交互式主菜单"""
    print_banner()

    while True:
        print(c("\n  主菜单", Colors.BOLD))
        print(f"  {c('[1]', Colors.CYAN)} 📋 列出所有模板")
        print(f"  {c('[2]', Colors.CYAN)} 🔍 搜索模板")
        print(f"  {c('[3]', Colors.CYAN)} 📝 使用模板")
        print(f"  {c('[4]', Colors.CYAN)} 🔨 从零构建 Prompt")
        print(f"  {c('[5]', Colors.CYAN)} 💾 导出所有模板")
        print(f"  {c('[6]', Colors.CYAN)} ➕ 保存自定义模板")
        print(f"  {c('[7]', Colors.CYAN)} 🗑️  删除自定义模板")
        print(f"  {c('[q]', Colors.CYAN)} 退出")

        choice = input(f"\n  请选择: ").strip().lower()

        if choice == "1":
            cat = input("  按分类过滤 (回车跳过, 可选: 开发/运维/架构/数据库/文档/通用): ").strip()
            list_templates(cat if cat else None)
        elif choice == "2":
            keyword = input("  搜索关键词: ").strip()
            if keyword:
                search_templates(keyword)
        elif choice == "3":
            template_id = input("  模板 ID: ").strip()
            if template_id:
                use_template(template_id)
        elif choice == "4":
            build_prompt()
        elif choice == "5":
            export_templates()
        elif choice == "6":
            build_prompt()  # 构建器中包含保存选项
        elif choice == "7":
            delete_custom_template()
        elif choice in ("q", "quit", "exit"):
            print(c("\n  👋 再见！", Colors.GREEN))
            break
        else:
            print(c(f"  无效选择: {choice}", Colors.RED))

# ============================================================================
# CLI 入口
# ============================================================================

def main():
    if len(sys.argv) <= 1:
        interactive_menu()
        return

    command = sys.argv[1].lower()

    if command in ("list", "ls", "l"):
        category = sys.argv[2] if len(sys.argv) > 2 else None
        list_templates(category)
    elif command in ("search", "find", "s"):
        if len(sys.argv) < 3:
            print(c("  用法: prompt_generator.py search <关键词>", Colors.RED))
            return
        search_templates(" ".join(sys.argv[2:]))
    elif command in ("use", "u"):
        if len(sys.argv) < 3:
            print(c("  用法: prompt_generator.py use <模板ID>", Colors.RED))
            return
        use_template(sys.argv[2])
    elif command in ("build", "new", "b"):
        build_prompt()
    elif command in ("export", "e"):
        export_templates()
    elif command in ("help", "h", "-h", "--help"):
        print(__doc__)
    else:
        print(c(f"  未知命令: {command}", Colors.RED))
        print(f"  输入 {c('python prompt_generator.py help', Colors.CYAN)} 查看帮助")

if __name__ == "__main__":
    main()

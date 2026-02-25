# my-go-api

## 项目概述

Go RESTful API 后端服务(这里指使用 GET/POST 方法)。

- **类型**: Backend API Service
- **状态**: 开发中

## 角色定义

您是一名高级Go后端工程师，在高性能API设计、并发模式和生产级系统方面拥有专业知识。

- 编写地道的Go语言——简单、可读、明确
- 在合理的情况下，更喜欢stdlib解决方案而不是第三方库
- 考虑性能，但在优化之前进行衡量
- 当不确定项目约定时，请先阅读“internal/”中的现有代码

## 技术栈与环境

- **语言**: Go 1.23+
- **HTTP 框架**: Gin / Echo / Chi
- **数据库**: PostgreSQL + Redis
- **数据库访问**: sqlx (优先原生 SQL)
- **迁移工具**: golang-migrate
- **配置**: Viper / envconfig
- **日志**: slog (标准库结构化日志)
- **可观测性**: OpenTelemetry + Prometheus
- **部署**: Docker + Kubernetes
- **操作系统**: Linux (Ubuntu 22.04+)

## 项目结构

```
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
└── CLAUDE.md
```

## 常用命令

- **启动开发服务**: `go run ./cmd/server`
- **运行全部测试**: `go test ./...`
- **运行单个测试**: `go test ./internal/service -run TestXxx -v`
- **代码检查**: `golangci-lint run ./...`
- **编译**: `go build -o bin/server ./cmd/server`
- **数据库迁移**: `migrate -path migrations -database $DB_URL up`
- **生成 Mock**: `go generate ./...`

## 代码规范

- 遵循 Effective Go 和 Go Code Review Comments
- `gofmt` / `goimports` 格式化——不争论风格
- 导出名称必须有文档注释
- 函数不超过 50 行；超过则拆分
- 使用 Table-Driven 测试
- 错误信息：小写、无标点、用 `fmt.Errorf("doing x: %w", err)` 包装
- 接口按行为命名: `Reader`, `Validator`，不用 `IReader`

## 核心规范

- 始终处理错误——禁止用 `_` 丢弃 error
- I/O 函数的第一个参数必须是 `context.Context`
- 打开资源后立即用 `defer` 关闭
- 禁止在 `init()` 中放非平凡逻辑
- 使用依赖注入；不使用全局可变状态
- 所有 SQL 必须使用参数化查询（防 SQL 注入）
- HTTP Handler 必须校验和清理所有输入
- 共享状态的并发访问必须用 mutex 或 channel 保护

## 工作流程

1. 先阅读相关代码，理解现有模式，再动手修改
2. 对非平凡功能，先制定计划并确认后再实现
3. 修改代码时同步编写或更新测试
4. 运行 `golangci-lint run ./...` 确保无 lint 问题
5. 运行 `go test ./...` 确保无回归
6. 保持 commit 小且聚焦——一个逻辑变更一个 commit

## 思考策略

- 接到复杂任务时，先用 think/ultrathink 规划方案，得到确认后再写代码
- 遇到不确定的项目约定时，先搜索 `internal/` 目录中的现有代码作为参考
- 修改公共接口前，先用 grep 查找所有调用方，评估影响范围
- 如果任务涉及多个文件，先列出需要修改的文件清单

## 测试规范

- 用 Table-Driven 测试覆盖多输入场景
- 用 `testify/assert` 或标准库 `testing` 做断言
- 通过接口 Mock 外部依赖，不依赖具体实现
- 集成测试放在 `_test.go` 中，用 build tag `//go:build integration`
- 为性能关键路径编写 Benchmark: `func BenchmarkXxx(b *testing.B)`

## 错误处理

- 返回错误，不要 panic（除非真正不可恢复）
- 用上下文包装错误: `fmt.Errorf("creating user: %w", err)`
- 用哨兵错误处理预期错误: `var ErrNotFound = errors.New(...)`
- 在边界层（handler）记录日志，不在业务逻辑深处
- Handler 层将领域错误映射为对应 HTTP 状态码

## 安全规范

- 禁止硬编码密钥——使用环境变量或密钥管理器
- 所有用户输入必须验证后再处理
- 只使用参数化 SQL 查询——禁止字符串拼接 SQL
- 所有 HTTP 客户端和数据库连接必须设置超时
- 对外接口实施限流

## Git 规范

- 分支命名: `feature/xxx`, `fix/xxx`, `refactor/xxx`
- Commit 消息: Conventional Commits 格式 — `type(scope): description`
- 始终在功能分支开发，禁止直接提交到 main

## 禁止事项

重要：以下规则绝对不可违反。

- ❌ 禁止提交密钥、API Key、密码或证书到仓库
- ❌ 禁止在 `main()` 之外使用 `os.Exit()`
- ❌ 禁止用 `panic()` 处理常规错误
- ❌ 禁止用 `_` 忽略 error 返回值
- ❌ 禁止未经批准使用 `unsafe` 包
- ❌ 禁止手动修改生成的文件（protobuf, mock 等）
- ❌ 禁止未经讨论添加新依赖

## 特殊注意

- ⚠️ `internal/` 目录有 Go 包可见性限制——外部模块无法导入
- ⚠️ `context.Background()` 只在 `main()` 或顶层使用——其他地方必须传递 context
- ⚠️ 注意 goroutine 泄漏——始终确保 goroutine 有退出路径
- ⚠️ JSON struct tag 使用 snake_case: `json:"field_name"`
- ⚠️ 时间处理: 始终使用 `time.Time` 和 `time.Duration`，不用裸整数

## 验证检查清单

完成任何修改后，必须按以下清单逐项验证：

- [ ] `golangci-lint run ./...` 通过，无报错
- [ ] `go test ./...` 全部通过
- [ ] `go build ./...` 编译成功
- [ ] 新增公共函数有文档注释
- [ ] 没有引入未讨论的新依赖
- [ ] 没有硬编码的密钥或配置值
- [ ] 修改过的代码有对应的测试覆盖

## 参考资源

- 项目布局: `cmd/`, `internal/`, `pkg/`
- API 规范: `api/openapi.yaml`
- 部署配置: `deploy/` (Dockerfile, K8s)
- 业务逻辑示例: `internal/service/`

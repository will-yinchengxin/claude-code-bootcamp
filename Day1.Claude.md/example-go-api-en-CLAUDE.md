# my-go-api

## Project Overview

Go RESTful API backend service.

- **Type**: Backend API Service
- **Status**: Active development

## Role Definition

You are a senior Go backend engineer with expertise in high-performance API design, concurrency patterns, and production-grade systems.

- Write idiomatic Go — simple, readable, and explicit
- Prefer stdlib solutions over third-party libraries when reasonable
- Think about performance, but measure before optimizing
- When unsure about project conventions, read existing code in `internal/` first

## Tech Stack & Environment

- **Language**: Go 1.23+
- **HTTP Framework**: Gin / Echo / Chi
- **Database**: PostgreSQL + Redis
- **DB Access**: sqlx (prefer raw SQL over heavy ORM)
- **Migration**: golang-migrate
- **Config**: Viper / envconfig
- **Logging**: slog (stdlib structured logging)
- **Observability**: OpenTelemetry + Prometheus
- **Deploy**: Docker + Kubernetes
- **OS**: Linux (Ubuntu 22.04+)

## Project Structure

```
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
└── CLAUDE.md
```

## Common Commands

- **Run dev server**: `go run ./cmd/server`
- **Run all tests**: `go test ./...`
- **Run single test**: `go test ./internal/service -run TestXxx -v`
- **Lint**: `golangci-lint run ./...`
- **Build**: `go build -o bin/server ./cmd/server`
- **Migration up**: `migrate -path migrations -database $DB_URL up`
- **Generate mocks**: `go generate ./...`

## Code Style

- Follow Effective Go and Go Code Review Comments
- `gofmt` / `goimports` for formatting — never argue about style
- Exported names must have doc comments
- Keep functions under 50 lines; split if longer
- Use table-driven tests
- Error messages: lowercase, no punctuation, wrap with `fmt.Errorf("doing x: %w", err)`
- Name interfaces by behavior: `Reader`, `Validator`, not `IReader`

## Core Rules

- Always handle errors — never use `_` to discard errors
- Use `context.Context` as first parameter in functions that do I/O
- Close resources with `defer` immediately after opening
- Never use `init()` for non-trivial logic
- Use dependency injection; no global mutable state
- All SQL must use parameterized queries (prevent SQL injection)
- HTTP handlers must validate and sanitize all input
- Concurrent access to shared state must use mutexes or channels

## Workflow

1. Read relevant code and understand existing patterns before making changes
2. Create a plan and confirm before implementing non-trivial features
3. Write or update tests alongside code changes
4. Run `golangci-lint run ./...` to verify no lint issues
5. Run `go test ./...` to verify no regressions
6. Keep commits small and focused — one logical change per commit

## Thinking Strategy

- For complex tasks, use think/ultrathink to plan first. Get confirmation before coding.
- When unsure about conventions, search existing code in `internal/` for reference patterns
- Before changing public interfaces, grep all callers and assess impact
- If a task spans multiple files, list all files to change before starting

## Testing

- Use table-driven tests for functions with multiple input/output cases
- Use `testify/assert` or stdlib `testing` for assertions
- Mock external dependencies with interfaces, not concrete types
- Integration tests in `_test.go` files with build tag `//go:build integration`
- Benchmark critical paths with `func BenchmarkXxx(b *testing.B)`

## Error Handling

- Return errors, don't panic (except truly unrecoverable situations)
- Wrap errors with context: `fmt.Errorf("creating user: %w", err)`
- Use sentinel errors for expected errors: `var ErrNotFound = errors.New(...)`
- Log errors at the boundary (handler), not deep in business logic
- HTTP handlers: map domain errors to appropriate status codes

## Security

- Never hardcode secrets — use environment variables or secret managers
- All user input must be validated before processing
- Use parameterized SQL queries exclusively — NO string concatenation
- Set timeouts on all HTTP clients and database connections
- Rate limit public-facing endpoints

## Git Conventions

- Branch naming: `feature/xxx`, `fix/xxx`, `refactor/xxx`
- Commit messages: Conventional Commits — `type(scope): description`
- Always work on feature branches, never commit directly to main

## Hard Rules — NEVER Do

IMPORTANT: The following rules must NEVER be violated.

- ❌ NEVER commit secrets, API keys, passwords, or certificates
- ❌ NEVER use `os.Exit()` outside of `main()`
- ❌ NEVER use `panic()` for normal error handling
- ❌ NEVER ignore errors with blank identifier `_`
- ❌ NEVER use `unsafe` package without explicit approval
- ❌ NEVER modify generated files (protobuf, mocks) by hand
- ❌ NEVER add dependencies without discussing the rationale

## Gotchas & Warnings

- ⚠️ `internal/` enforces Go package visibility — external modules cannot import
- ⚠️ `context.Background()` only in `main()` — pass context everywhere else
- ⚠️ Watch for goroutine leaks — always ensure goroutines can exit
- ⚠️ JSON struct tags use snake_case: `json:"field_name"`
- ⚠️ Time: always use `time.Time` / `time.Duration`, never raw integers

## Verification Checklist

After completing any change, verify each item below:

- [ ] `golangci-lint run ./...` passes with no errors
- [ ] `go test ./...` all pass
- [ ] `go build ./...` compiles successfully
- [ ] New public functions have doc comments
- [ ] No undiscussed new dependencies introduced
- [ ] No hardcoded secrets or config values
- [ ] Changed code has corresponding test coverage

## References

- Project layout: `cmd/`, `internal/`, `pkg/`
- API spec: `api/openapi.yaml`
- Deployment: `deploy/` (Dockerfile, K8s)
- Business logic examples: `internal/service/`

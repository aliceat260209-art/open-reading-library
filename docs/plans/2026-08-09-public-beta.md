# Open Reading Library Public Beta Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 将现有单用户本地阅读原型重构为可安全托管、支持普通用户使用云端 AI 的私有阅读产品。

**Architecture:** 保留“直接阅读 → 上下文摘录 → 可回到原文”的产品核心。公开版采用 Web API + PostgreSQL + 私有对象存储 + 异步 worker；AI 仅通过可审计、可限额的后台任务调用，用户文件永不进入公共书库。

**Tech Stack:** Next.js/React 前端、Python FastAPI 服务、PostgreSQL、S3 兼容对象存储、Redis 队列、受限解析/OCR worker、托管 LLM/OCR Provider adapter、Docker Compose（开发）与托管容器平台（Beta）。

---

## 发布路径

- **阶段 0（现在）**：公开、安全的代码与产品文档；不发布用户书籍或数据库。
- **阶段 1（4–6 周）**：邀请制 Web Beta，用户自带文件，核心阅读与笔记，不含大规模 AI。
- **阶段 2（6–10 周）**：异步 OCR / 摘要 / 搜索、免费额度与付费点数。
- **阶段 3**：团队书库、阅读小组、只分享用户原创笔记的内容分发。

## Task 1: 建立无私人数据的公开代码仓库

**Objective:** 创建可公开审阅的项目根目录，确保任何本地用户内容均不进入版本控制。

**Files:**
- Create: `README.md`, `.gitignore`, `SECURITY.md`, `CONTRIBUTING.md`
- Create: `docs/ARCHITECTURE.md`, `docs/PRIVACY_AND_COPYRIGHT.md`
- Test: `scripts/check_public_tree.py`

**Step 1: Write failing test**

创建 `scripts/check_public_tree.py`，当发现 `*.epub`、`*.mobi`、`*.pdf`、`*.sqlite`、`.env` 或 `books/`、`covers/`、`database/` 目录被 Git 跟踪时退出失败。

**Step 2: Run test to verify failure**

Run: `python3 scripts/check_public_tree.py`

Expected: 初始目录含私人资产时 FAIL。

**Step 3: Implement minimal protection**

完善 `.gitignore`，并只在干净的新目录执行 `git init`。

**Step 4: Verify pass**

Run: `python3 scripts/check_public_tree.py`

Expected: `PASS: no private library assets tracked`。

**Step 5: Commit**

```bash
git add README.md .gitignore SECURITY.md CONTRIBUTING.md docs scripts/check_public_tree.py
git commit -m "docs: establish public project foundation"
```

## Task 2: 定义多租户领域模型

**Objective:** 为公开版建立私有书库、用户和任务的明确边界。

**Files:**
- Create: `apps/api/app/models/*.py`
- Create: `apps/api/alembic/versions/0001_initial.py`
- Test: `apps/api/tests/test_tenant_isolation.py`

**Step 1: Write failing test**

测试用户 A 不能读取用户 B 的 `book`、`highlight`、`reading_position`、`ai_job`。

**Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_tenant_isolation.py -v`

**Step 3: Implement minimal model**

创建 `users`、`libraries`、`books`、`book_files`、`cover_assets`、`reading_positions`、`highlights`、`notes`、`jobs` 表；所有内容通过 `library_id` 归属到单一用户/组织。

**Step 4: Verify pass**

Run: `pytest apps/api/tests/test_tenant_isolation.py -v`

**Step 5: Commit**

```bash
git add apps/api
git commit -m "feat(api): add tenant-isolated library models"
```

## Task 3: 安全文件上传与私有存储

**Objective:** 用户可上传自己有权使用的 EPUB/PDF，且原文件永不公开。

**Files:**
- Create: `apps/api/app/routes/uploads.py`
- Create: `apps/api/app/services/storage.py`
- Create: `apps/api/app/services/file_validation.py`
- Test: `apps/api/tests/test_upload_security.py`

**Step 1: Write failing tests**

覆盖：无登录上传、错误 MIME、超大文件、ZIP 解压炸弹、访问他人文件、过期签名 URL。

**Step 2: Implement**

上传 API 必须进行：登录、权利确认、大小/MIME/魔数校验、私有 bucket 写入、`user_id` 路径分隔；读取时由 API 重新校验后生成短时 URL。

**Step 3: Verify**

Run: `pytest apps/api/tests/test_upload_security.py -v`

**Step 4: Commit**

```bash
git add apps/api
git commit -m "feat(api): add private validated uploads"
```

## Task 4: 将解析、封面与 OCR 放进隔离 worker

**Objective:** 使文件解析不阻塞 Web 请求也不危及 API 进程。

**Files:**
- Create: `apps/worker/app/tasks/extract_book.py`
- Create: `apps/worker/app/tasks/extract_cover.py`
- Create: `apps/worker/app/tasks/ocr_pdf.py`
- Test: `apps/worker/tests/test_extraction_jobs.py`

**Step 1: Write failing tests**

验证任务状态流转：`queued → running → succeeded/failed`，以及失败时不泄露文件正文。

**Step 2: Implement**

用受限容器 worker 执行 Calibre / 文本提取 / OCR。限制 CPU、内存、时长、解压后文件数和网络出口；只将派生文件写到私有对象存储。

**Step 3: Verify**

Run: `pytest apps/worker/tests/test_extraction_jobs.py -v`

**Step 4: Commit**

```bash
git add apps/worker
git commit -m "feat(worker): add isolated extraction pipeline"
```

## Task 5: 重建阅读与笔记闭环

**Objective:** 在多人环境仍保证“笔记属于阅读位置，而不是孤立表单”。

**Files:**
- Create: `apps/web/app/library/[bookId]/read/page.tsx`
- Create: `apps/web/components/reader/SelectionToolbar.tsx`
- Create: `apps/api/app/routes/highlights.py`
- Test: `apps/web/e2e/reader-notes.spec.ts`

**Step 1: Write failing E2E test**

场景：用户打开自己的 EPUB → 选择一段文字 → 写感想 → 保存 → 从按书索引的笔记页点击并回到原位置。

**Step 2: Implement**

存储稳定文本锚点：`book_id + spine_href + paragraph_id + character offsets + quote`。阅读位置自动保存；手动书签独立于当前位置。

**Step 3: Verify**

Run: `pnpm playwright test apps/web/e2e/reader-notes.spec.ts`

**Step 4: Commit**

```bash
git add apps/web apps/api
git commit -m "feat(reader): add anchored highlights and note index"
```

## Task 6: 可选、异步、可计量的云端 AI

**Objective:** 没有本地算力的用户可用 AI，同时成本和隐私可控。

**Files:**
- Create: `apps/api/app/routes/ai_jobs.py`
- Create: `apps/worker/app/tasks/ai_summary.py`
- Create: `apps/api/app/services/ai_provider.py`
- Test: `apps/api/tests/test_ai_quota.py`

**Step 1: Write failing tests**

覆盖：未授权任务、超额度、重复任务复用、取消、删除后无法再读取、provider 失败重试。

**Step 2: Implement**

采用 Provider adapter；提交前显示任务类型与预计额度；任务输出保存为用户私有数据；默认不保留给模型训练。

**Step 3: Verify**

Run: `pytest apps/api/tests/test_ai_quota.py -v`

**Step 4: Commit**

```bash
git add apps/api apps/worker
git commit -m "feat(ai): add quota-controlled private jobs"
```

## Task 7: 部署、可观测性与邀请制 Beta

**Objective:** 可重复部署并安全地邀请首批用户。

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `infra/compose.production.yml`
- Create: `.github/workflows/ci.yml`
- Create: `docs/OPERATIONS.md`
- Test: `scripts/smoke_test.sh`

**Step 1: Implement deployment baseline**

开发环境使用 Docker Compose（Web、API、Postgres、Redis、MinIO、Worker）；生产使用托管 Postgres、私有 S3、容器 Web/worker 和受控密钥服务。

**Step 2: Add CI**

每个 PR 运行 lint、unit tests、tenant isolation tests、upload security tests 和 secret scan。

**Step 3: Verify**

Run: `docker compose -f infra/docker-compose.yml up --build -d && scripts/smoke_test.sh`

Expected: 注册、私有上传、阅读、笔记、异步任务状态均成功；跨用户读取返回 403/404。

**Step 4: Commit**

```bash
git add infra .github docs scripts
git commit -m "ci: add beta deployment and safety checks"
```

## 发布验收标准

- 任意用户不能读到其他用户的书、封面、OCR、摘录、笔记或 AI 输出；
- 未经授权的原书不出现在仓库、日志、公开 URL、搜索引擎或公共数据库；
- 每个 AI 任务可显示状态、额度、取消和删除；
- 上传与解析失败可恢复且不会拖垮 Web 服务；
- 新用户无需本地 GPU 即可完成一次“上传 → 阅读 → 摘录 → AI 摘要”的完整闭环。

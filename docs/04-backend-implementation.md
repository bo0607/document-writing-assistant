# 基于大模型的文档智能写作助手：核心后端功能实现

## 1. 阶段目标

本阶段完成系统核心后端功能实现，目标是让“写作任务内核”从设计转化为可运行代码。实现重点包括任务创建、需求解析、提纲生成、正文生成、文本修订、摘要生成、文档导出和 HTTP 接口访问。

为了降低部署难度，后端采用 Python 标准库为主实现 HTTP 服务，不依赖 FastAPI、Flask 等额外框架。文档导出使用本机可用的 `python-docx`。模型调用通过 `ModelAdapter` 封装，未配置远程模型时系统会自动使用本地演示生成逻辑，保证项目可以完整演示。

## 2. 后端目录结构

```text
backend/
  server.py
  README.md
  app/
    main.py
    core/
      context_binder.py
      model_adapter.py
      result_assembler.py
      skill_registry.py
      task_state.py
      writing_task_engine.py
    skills/
      base.py
      requirement_parse_skill.py
      outline_skill.py
      draft_skill.py
      revision_skill.py
      summary_skill.py
    storage/
      task_store.py
    exporter/
      document_exporter.py
  data/
    tasks/
    exports/
  tests/
    http_smoke_test.py
```

## 3. 核心模块实现

### 3.1 WritingTaskEngine

文件：`backend/app/core/writing_task_engine.py`

`WritingTaskEngine` 是后端核心调度模块，负责把一次写作任务按流程推进。它不做开放式自主代理，而是按照文档写作流程依次调用需求解析、提纲生成、正文生成、文本修订和导出模块。

主要能力：

1. 创建写作任务。
2. 自动解析写作需求。
3. 自动生成文章提纲。
4. 根据提纲生成正文。
5. 支持润色、改写、扩写、缩写等修订操作。
6. 支持摘要生成。
7. 支持导出 Word 或文本文件。

### 3.2 ContextBinder

文件：`backend/app/core/context_binder.py`

`ContextBinder` 用于管理当前写作任务上下文。它保存用户输入、结构化需求、提纲、正文、修订记录和导出记录。该模块对应设计中的“当前任务上下文”，不实现复杂长期记忆。

### 3.3 SkillRegistry 与写作技能

文件：`backend/app/core/skill_registry.py`、`backend/app/skills/`

写作技能采用统一接口注册和调用。当前已实现：

| 技能 | 作用 |
| --- | --- |
| RequirementParseSkill | 解析用户写作需求 |
| OutlineSkill | 生成标题、中心思想和段落提纲 |
| DraftSkill | 根据提纲生成正文 |
| RevisionSkill | 润色、改写、扩写、缩写和纠错 |
| SummarySkill | 生成摘要 |

这些技能体现了对 OpenClaw 技能思想的借鉴，但技能范围被限制在文档写作场景内。

### 3.4 ModelAdapter

文件：`backend/app/core/model_adapter.py`

`ModelAdapter` 负责统一封装大模型调用。当前支持 OpenAI 兼容接口配置：

```text
WRITING_ASSISTANT_BASE_URL
WRITING_ASSISTANT_API_KEY
WRITING_ASSISTANT_MODEL
```

如果没有配置远程模型，系统不会中断，而是使用本地演示生成逻辑，使项目仍能完整运行。

### 3.5 DocumentExporter

文件：`backend/app/exporter/document_exporter.py`

`DocumentExporter` 支持导出：

1. `docx`：Word 文档。
2. `txt`：纯文本文件。

导出文件默认保存到：

```text
backend/data/exports/
```

## 4. HTTP 接口实现

后端入口文件为：

```text
backend/server.py
```

HTTP 服务实现在：

```text
backend/app/main.py
```

当前接口如下：

| 接口 | 方法 | 作用 |
| --- | --- | --- |
| `/api/health` | GET | 健康检查 |
| `/api/skills` | GET | 查看已注册写作技能 |
| `/api/tasks` | GET | 查看任务列表 |
| `/api/task/detail` | GET | 查询任务详情 |
| `/api/task/create` | POST | 创建写作任务 |
| `/api/task/run-full` | POST | 一键完成需求解析、提纲生成和正文生成 |
| `/api/requirement/parse` | POST | 解析写作需求 |
| `/api/outline/generate` | POST | 生成提纲 |
| `/api/draft/generate` | POST | 生成正文 |
| `/api/text/revise` | POST | 文本修订 |
| `/api/text/summary` | POST | 生成摘要 |
| `/api/document/export` | POST | 导出文档 |

## 5. VSCode 运行环境

已配置项目专用 Python 虚拟环境：

```text
D:\SRT\.venv
```

VSCode 配置文件：

| 文件 | 作用 |
| --- | --- |
| `.vscode/settings.json` | 指定 Python 解释器和项目路径 |
| `.vscode/launch.json` | 配置“启动文档写作助手后端”调试项 |
| `.vscode/extensions.json` | 推荐 Python 相关扩展 |

在 VSCode 中运行时，选择“启动文档写作助手后端”，启动后访问：

```text
http://127.0.0.1:8000/api/health
```

## 6. 验证结果

已完成后端编译检查：

```text
python -m compileall -q backend
```

已完成 HTTP 冒烟测试：

```text
python backend/tests/http_smoke_test.py
```

测试覆盖流程：

1. 启动临时 HTTP 服务。
2. 请求 `/api/health`。
3. 请求 `/api/task/run-full` 完成完整生成。
4. 请求 `/api/text/revise` 完成润色。
5. 请求 `/api/document/export` 导出 Word 文档。
6. 检查导出文件存在。

测试结果：通过。

示例导出文件：

```text
backend/data/exports/task_20260604200243_32ea1091_人工智能对学习方式的影响之我见.docx
```

## 7. 阶段结论

本阶段已经完成核心后端功能实现。系统能够以写作任务为中心，完成从用户输入到提纲、正文、修订和文档导出的后端闭环。实现方式与前面设计保持一致，体现了“轻量化写作任务内核”的特点，也为下一阶段前端写作工作台提供了接口基础。

下一阶段应进入前端实现，构建一个可视化写作工作台，调用本阶段提供的后端接口完成交互式写作流程。

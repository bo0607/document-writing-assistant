# 基于大模型的文档智能写作助手

这是一个面向文档与作文生成场景的智能写作助手。系统参考 OpenClaw 的任务运行、上下文管理、技能注册和模型适配思想，但将其缩减并改造为面向文档写作的轻量化任务内核。

## 已实现功能

- 写作要求输入：主题、文体、字数、风格、补充要求
- 一键生成：需求解析、提纲生成、正文生成
- 文本处理：润色、改写、扩写、缩写、纠错、自定义修订
- 正文编辑：前端编辑并保存正文
- 摘要生成
- 文档导出：Word `.docx` 和文本 `.txt`
- 最近任务查看与载入
- 自动化测试：接口闭环测试和导出结构测试

## 运行方式

在 VSCode 中打开 `D:\SRT`，选择运行和调试里的：

```text
启动文档写作助手后端
```

启动后访问：

```text
http://127.0.0.1:8000/
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

## 测试方式

在 VSCode 终端中运行：

```text
python backend/tests/run_all.py
```

测试通过时会输出：

```text
All tests passed.
```

## 模型配置

未配置远程模型时，系统会使用本地演示生成逻辑，仍然可以完整演示。

如需接入 OpenAI 兼容模型，可设置：

```text
WRITING_ASSISTANT_BASE_URL=https://api.example.com/v1
WRITING_ASSISTANT_API_KEY=your_api_key
WRITING_ASSISTANT_MODEL=your_model_name
```

## 项目结构

```text
D:\SRT
  backend/
    app/
      core/
      skills/
      storage/
      exporter/
      main.py
    static/
      index.html
      styles.css
      app.js
    tests/
      http_smoke_test.py
      export_structure_test.py
      run_all.py
    server.py
  docs/
    01-requirements-positioning.md
    02-system-architecture.md
    03-writing-task-kernel-design.md
    04-backend-implementation.md
    05-frontend-workbench.md
    06-testing-and-output.md
    07-paper-summary-and-demo.md
```

## 关键文档

- 需求与差异化定位：`docs/01-requirements-positioning.md`
- 系统总体架构：`docs/02-system-architecture.md`
- 写作任务内核设计：`docs/03-writing-task-kernel-design.md`
- 后端实现说明：`docs/04-backend-implementation.md`
- 前端工作台说明：`docs/05-frontend-workbench.md`
- 测试与输出说明：`docs/06-testing-and-output.md`
- 论文说明与项目总结：`docs/07-paper-summary-and-demo.md`

## 当前状态

项目已经完成可演示闭环：前端输入写作要求，后端生成提纲和正文，用户执行修订和摘要生成，最终导出 Word 或文本文件。

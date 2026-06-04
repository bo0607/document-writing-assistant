# 文档智能写作助手后端

## 在 VSCode 中运行

1. 打开 `D:\SRT` 文件夹。
2. 确认 VSCode 右下角 Python 解释器为 `.venv\Scripts\python.exe`。
3. 在“运行和调试”中选择“启动文档写作助手后端”。
4. 启动后访问：

```text
http://127.0.0.1:8000/
```

健康检查接口：

```text
http://127.0.0.1:8000/api/health
```

## 模型配置

没有配置模型接口时，系统会使用本地演示生成逻辑，仍然可以跑通“需求解析、提纲生成、正文生成、润色、导出”的完整流程。

如需接入 OpenAI 兼容模型，可设置环境变量：

```text
WRITING_ASSISTANT_BASE_URL=https://api.example.com/v1
WRITING_ASSISTANT_API_KEY=your_api_key
WRITING_ASSISTANT_MODEL=your_model_name
```

## 测试

运行全部测试：

```text
python tests/run_all.py
```

测试覆盖前端首页、接口闭环、正文保存、文本修订、Word 导出和文本导出结构检查。

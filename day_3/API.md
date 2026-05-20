# 论文研究 RAG 系统 API 文档

## 通用约定

- Base URL: `/api`。前端开发环境由 Vite 代理到 Flask，后端真实路由不带 `/api`。
- Content-Type: 默认 `application/json`；文件上传接口使用 `multipart/form-data`。
- 认证方式: Flask Session Cookie。登录成功后浏览器保存 Cookie，后续请求自动携带。
- 通用响应:

```json
{
  "code": "success",
  "message": "",
  "data": {}
}
```

- 常见 `code`:

| code | 说明 |
| --- | --- |
| `success` | 请求成功 |
| `validateError` | 参数校验失败 |
| `unauthorized` | 未登录或登录状态失效 |
| `forbidden` | 无权限访问 |
| `fail` | 业务处理失败 |

## 用户认证与用户信息

### 注册

- Method: `POST`
- Path: `/auth/register`
- Body:

```json
{
  "username": "alice",
  "password": "123456"
}
```

- Response:

```json
{
  "code": "success",
  "message": "注册成功",
  "data": {
    "user": {
      "id": "uuid",
      "username": "alice",
      "avatar_url": ""
    }
  }
}
```

### 登录

- Method: `POST`
- Path: `/auth/login`
- Body:

```json
{
  "username": "alice",
  "password": "123456"
}
```

### 当前用户

- Method: `GET`
- Path: `/auth/me`
- Response:

```json
{
  "code": "success",
  "message": "",
  "data": {
    "user": {
      "id": "uuid",
      "username": "alice",
      "avatar_url": "",
      "created_at": "2026-05-18T14:00:00"
    }
  }
}
```

### 更新用户资料

- Method: `PATCH`
- Path: `/auth/me`
- Body:

```json
{
  "username": "alice",
  "avatar_url": "https://example.com/avatar.png"
}
```

### 退出登录

- Method: `POST`
- Path: `/auth/logout`

## 会话管理

### 创建会话

- Method: `POST`
- Path: `/sessions`
- Body:

```json
{
  "title": "新的论文研究会话"
}
```

### 会话列表

- Method: `GET`
- Path: `/sessions`
- Response:

```json
{
  "code": "success",
  "message": "",
  "data": {
    "sessions": [
      {
        "id": "uuid",
        "title": "ReID 论文阅读",
        "created_at": "2026-05-18T14:00:00",
        "updated_at": "2026-05-18T14:00:00"
      }
    ]
  }
}
```

### 获取会话详情与历史

- Method: `GET`
- Path: `/sessions/{session_id}`
- Response:

```json
{
  "code": "success",
  "message": "",
  "data": {
    "session": {
      "id": "uuid",
      "title": "ReID 论文阅读",
      "created_at": "2026-05-18T14:00:00",
      "updated_at": "2026-05-18T14:00:00"
    },
    "messages": [
      {
        "id": "uuid",
        "role": "user",
        "content": "这篇论文解决了什么问题？",
        "created_at": "2026-05-18T14:00:01"
      },
      {
        "id": "uuid",
        "role": "assistant",
        "content": "它主要解决跨模态目标重识别中的...",
        "created_at": "2026-05-18T14:00:08"
      }
    ]
  }
}
```

### 更新会话标题

- Method: `PATCH`
- Path: `/sessions/{session_id}`
- Body:

```json
{
  "title": "跨模态 ReID 调研"
}
```

### 删除会话

- Method: `DELETE`
- Path: `/sessions/{session_id}`

## RAG 问答

### 发送问题

- Method: `POST`
- Path: `/sessions/{session_id}/messages`
- Body:

```json
{
  "user_input": "请总结 MDReID 的核心贡献",
  "settings": {
    "model": "bailu-2.7",
    "temperature": 0,
    "top_p": 1,
    "retrieval_top_k": 3
  }
}
```

- Response:

```json
{
  "code": "success",
  "message": "",
  "data": {
    "content": "MDReID 的核心贡献包括...",
    "message": {
      "id": "uuid",
      "role": "assistant",
      "content": "MDReID 的核心贡献包括...",
      "created_at": "2026-05-18T14:00:08"
    },
    "session": {
      "id": "uuid",
      "title": "MDReID 核心贡献总结"
    },
    "references": [
      {
        "document_id": "uuid",
        "title": "MDReID Modality-Decoupled Learning...",
        "page": 3,
        "score": 0.82
      }
    ]
  }
}
```

### 根据首次提问生成标题

- 后端在会话第一条用户消息创建后自动执行。
- 建议标题长度控制在 8 到 30 个中文字符。
- 如果生成失败，回退到用户问题前 30 个字符。

- Method: `POST`
- Path: `/sessions/{session_id}/title/generate`
- Body:

```json
{
  "first_user_input": "请总结 MDReID 的核心贡献"
}
```

## 文件加载与知识库

前端入口: 对话框左下角 `+` 按钮，支持点击选择文件，也支持拖拽文件到输入区域。

### 上传文件

- Method: `POST`
- Path: `/sessions/{session_id}/documents`
- Content-Type: `multipart/form-data`
- Form fields:

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `files` | File[] | 是 | 支持多文件上传 |
| `metadata` | JSON string | 否 | 文件级元数据 |

- `metadata` 示例:

```json
{
  "title": "",
  "author": "",
  "year": "",
  "keywords": "",
  "source": "",
  "tags": []
}
```

- Response:

```json
{
  "code": "success",
  "message": "上传成功，正在解析",
  "data": {
    "documents": [
      {
        "id": "uuid",
        "filename": "MDReID.pdf",
        "content_type": "application/pdf",
        "size": 1024000,
        "status": "processing",
        "metadata": {
          "title": "MDReID",
          "author": "",
          "year": "",
          "keywords": "",
          "source": "",
          "tags": []
        },
        "created_at": "2026-05-18T14:00:00"
      }
    ]
  }
}
```

### 文件类型处理建议

| 类型 | 后端 Loader 建议 |
| --- | --- |
| `.pdf` | `PyMuPDFLoader` |
| `.txt`, `.md` | `TextLoader` |
| `.docx` | `Docx2txtLoader` 或 `UnstructuredWordDocumentLoader` |
| `.csv` | `CSVLoader` |
| `.html` | `BSHTMLLoader` 或 `UnstructuredHTMLLoader` |

处理流程建议参考 `load_ducuments.py`: loader 解析文件 -> `RecursiveCharacterTextSplitter` 切分 -> 生成 embedding -> 写入向量库。新增实现时建议把文件元数据写入数据库，并将 `document_id`、`session_id`、用户元数据同步写入向量库 metadata。

### 查询已加载文件

- Method: `GET`
- Path: `/sessions/{session_id}/documents`
- Query:

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | 可选，`processing` / `ready` / `failed` |

### 删除文件

- Method: `DELETE`
- Path: `/sessions/{session_id}/documents/{document_id}`
- 行为: 删除数据库记录，并删除向量库中对应 `document_id` 的 chunks。

### 更新文件元数据

- Method: `PATCH`
- Path: `/sessions/{session_id}/documents/{document_id}`
- Body:

```json
{
  "metadata": {
    "title": "MDReID",
    "author": "Zhang et al.",
    "year": "2025",
    "keywords": "multi-modal re-identification",
    "source": "local_upload",
    "tags": ["ReID", "multi-modal"]
  }
}
```

## 对话设置

前端入口: 对话界面右上角设置按钮。

### 获取会话设置

- Method: `GET`
- Path: `/sessions/{session_id}/settings`

### 更新会话设置

- Method: `PATCH`
- Path: `/sessions/{session_id}/settings`
- Body:

```json
{
  "model": "bailu-2.7",
  "temperature": 0.2,
  "top_p": 1,
  "retrieval_top_k": 3,
  "namespace": "ReID",
  "enable_web_search": true
}
```

### 设置字段说明

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `model` | string | `bailu-2.7` | 当前会话使用的模型 |
| `temperature` | number | `0` | 生成随机性，建议范围 `0` 到 `2` |
| `top_p` | number | `1` | nucleus sampling 参数 |
| `retrieval_top_k` | number | `3` | 每次检索召回文档数量 |
| `namespace` | string | `ReID` | 向量库命名空间 |
| `enable_web_search` | boolean | `true` | 文档不相关时是否启用联网搜索 |

## 兼容接口

现有调试接口保留:

- Method: `POST`
- Path: `/apps/{app_id}/debug`

建议新前端使用 `/sessions/{session_id}/messages`，让每个用户拥有多个独立 session，每个 session 保存自己的 history、文件和模型设置。

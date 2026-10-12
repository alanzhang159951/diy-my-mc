"""麦当劳中国官方 MCP Server 的零依赖 Python 客户端。

只依赖标准库，方便任何人 clone 下来直接跑。实现 MCP Streamable HTTP 的
最小闭环：initialize -> notifications/initialized -> tools/list / tools/call。

用法：
    client = McdMcpClient()                 # 从环境变量 MCD_MCP_TOKEN 读取 Token
    client.initialize()
    print(client.list_tools())
    print(client.call_tool("query-meals", {"storeCode": "..."}))

Token 只从环境变量读取，不写进任何文件。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_URL = "https://mcp.mcd.cn"
PROTOCOL_VERSION = "2025-06-18"
CLIENT_NAME = "diy-my-mc"
CLIENT_VERSION = "1.0.0"


class McpError(RuntimeError):
    """MCP 调用失败（含网络错误、HTTP 错误码、JSON-RPC error）。"""


class McdMcpClient:
    """麦当劳 MCP Server 的最小客户端。"""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
        verbose: bool = False,
    ) -> None:
        self.url = (url or os.environ.get("MCD_MCP_URL") or DEFAULT_URL).rstrip("/")
        self.token = token or os.environ.get("MCD_MCP_TOKEN")
        if not self.token:
            raise McpError(
                "缺少 MCP Token。请先申请 Token 并设置环境变量：\n"
                "  申请地址 https://open.mcd.cn/mcp（手机号登录 -> 控制台 -> 激活）\n"
                "  Windows:  set MCD_MCP_TOKEN=你的Token\n"
                "  macOS/Linux:  export MCD_MCP_TOKEN=你的Token\n"
                "未配置 Token 时，可先运行 `python scripts/diy_mc.py demo` 用样例数据体验。"
            )
        self.timeout = timeout
        self.verbose = verbose
        self._session_id: str | None = None
        self._next_id = 1
        self._tools_cache: list[dict[str, Any]] | None = None

    # ---------------------------------------------------------------- 传输层

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
            "User-Agent": f"{CLIENT_NAME}/{CLIENT_VERSION}",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=body, headers=self._headers(), method="POST"
        )
        if self.verbose:
            print(f"[mcp] -> {json.dumps(payload, ensure_ascii=False)[:400]}", flush=True)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id:
                    self._session_id = session_id
                content_type = (response.headers.get("Content-Type") or "").lower()
                raw = response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:  # 401 / 429 等
            detail = exc.read().decode("utf-8", "replace")[:500]
            hint = ""
            if exc.code == 401:
                hint = "（Token 无效、已过期或未提供）"
            elif exc.code == 429:
                hint = "（触发限流，每 Token 每分钟上限 600 次）"
            raise McpError(f"HTTP {exc.code}{hint}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise McpError(f"连接 {self.url} 失败：{exc.reason}") from exc

        if self.verbose:
            print(f"[mcp] <- {raw[:400]}", flush=True)

        if "text/event-stream" in content_type:
            return self._parse_sse(raw)
        if not raw.strip():
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise McpError(f"响应不是合法 JSON：{raw[:300]}") from exc

    @staticmethod
    def _parse_sse(raw: str) -> dict[str, Any] | None:
        """从 SSE 流里取出最后一个 JSON-RPC 响应。"""
        last: dict[str, Any] | None = None
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            chunk = line[len("data:") :].strip()
            if not chunk or chunk == "[DONE]":
                continue
            try:
                payload = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and ("result" in payload or "error" in payload):
                last = payload
        return last

    def _rpc(
        self, method: str, params: dict[str, Any] | None = None, notify: bool = False
    ) -> Any:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notify:
            payload["id"] = self._next_id
            self._next_id += 1
        response = self._post(payload)
        if notify:
            return None
        if response is None:
            raise McpError(f"{method} 没有返回结果")
        if "error" in response:
            error = response["error"] or {}
            raise McpError(
                f"{method} 失败：code={error.get('code')} message={error.get('message')}"
            )
        return response.get("result")

    # ---------------------------------------------------------------- 协议层

    def initialize(self) -> dict[str, Any]:
        """完成 MCP 握手，返回服务端信息。"""
        result = self._rpc(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
            },
        )
        self._rpc("notifications/initialized", {}, notify=True)
        return result or {}

    def list_tools(self, refresh: bool = False) -> list[dict[str, Any]]:
        """列出服务端全部工具。"""
        if self._tools_cache is not None and not refresh:
            return self._tools_cache
        result = self._rpc("tools/list") or {}
        self._tools_cache = result.get("tools") or []
        return self._tools_cache

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """调用一个工具，返回已尽量解析成 Python 对象的结果。"""
        result = self._rpc("tools/call", {"name": name, "arguments": arguments or {}})
        if isinstance(result, dict) and result.get("isError"):
            texts = self.extract_text(result)
            raise McpError(f"工具 {name} 返回错误：{texts[:500]}")
        return self.extract_payload(result)

    # ------------------------------------------------------------ 结果解析

    @staticmethod
    def extract_text(result: Any) -> str:
        """把 MCP content 数组拼成纯文本。"""
        if not isinstance(result, dict):
            return "" if result is None else str(result)
        parts: list[str] = []
        for item in result.get("content") or []:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(parts)

    @classmethod
    def extract_payload(cls, result: Any) -> Any:
        """优先返回结构化数据，退化到解析文本里的 JSON，最后返回原文。"""
        if isinstance(result, dict):
            if "structuredContent" in result and result["structuredContent"] is not None:
                return result["structuredContent"]
            text = cls.extract_text(result)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
            return result
        return result


def probe() -> None:
    """连通性自检：握手 + 列工具。命令行直接运行本文件即可。"""
    client = McdMcpClient(verbose=True)
    info = client.initialize()
    server = (info or {}).get("serverInfo") or {}
    print(f"已连接：{server.get('name', '未知')} {server.get('version', '')}")
    tools = client.list_tools()
    print(f"可用工具 {len(tools)} 个：")
    for tool in tools:
        print(f"  - {tool.get('name')}: {tool.get('description', '')[:60]}")
    print(f"session id = {client._session_id or '(无)'}")


if __name__ == "__main__":
    probe()

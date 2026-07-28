import asyncio
from fastmcp import Client
from fastmcp.exceptions import ToolError

client = Client("http://127.0.0.1:8000/mcp")  # 별도로 실행 중인 MCP 서버 주소

async def main():
    try:
        # MCP 서버 연결
        async with client:
            tools = await client.list_tools() # 등록된 Tool 목록 조회
            print("=== 등록된 MCP Tool ===")
            for tool in tools:
                print("-", tool.name)
                print(" 입력 구조:", tool.inputSchema)

            # 1. 전체 부서 조회
            all_result = await client.call_tool(
                "get_all_busers",
                {
                    "limit": 100,
                },
            )
            print("\n전체 부서 ===")
            print(all_result.data)

            # 2. 부서번호로 조회
            # 서버 함수의 매개변수명이 buser_num이므로
            # Client에서도 buser_num으로 전달
            one_result = await client.call_tool(
                "get_buser_by_num",
                {
                    "buser_num": 10,
                },
            )
            print("\n10번 부서 ===")
            print(one_result.data)

            # 3. 부서명으로 검색
            search_result = await client.call_tool(
                "search_busers",
                {
                    "keyword": "총무부",
                },
            )
            print("\n=== 부서명 검색 ===")
            print(search_result.data)
    except ToolError as err:
        print("\nMCP Tool 실행 오류:", err)
    except Exception as err:
        print("\nMCP Client 오류:", err)


if __name__ == "__main__":
    asyncio.run(main())
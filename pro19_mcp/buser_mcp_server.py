# !pip install -U fastmcp mariadb python-dotenv

import os
import mariadb
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

load_dotenv()

# MCP 서버 객체 생성
mcp = FastMCP(
    name="MariaDB Buser Server",
    mask_error_details=True,
    # MCP 도구 실행 중 발생한 내부 오류의 상세 내용을 Client나 LLM에 노출하지 않도록 가리는 설정
)

def get_connection():
    """
    MariaDB 연결 객체를 생성한다.
    이 함수는 MCP Tool이 아니며, MCP Tool 내부에서 공통으로 사용하는 DB 연결 함수이다.
    """
    return mariadb.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "test"),
    )


# 전체 부서 조회
@mcp.tool(
    # mcp.tool() 데코레이터 함수에 전달하는 키워드 인자들
    # 1. mcp.tool()에 설정값 전달
    # 2. 데코레이터 생성
    # 3. get_all_busers 함수를 데코레이터에 전달
    # 4. MCP Tool로 등록
    description="MariaDB의 buser 테이블에서 부서 목록을 조회한다.",
    annotations={
        "readOnlyHint": True,    # 도구가 외부 상태를 변경하지 않고 읽기만 한다는 뜻
        "idempotentHint": True,  # 같은 인자로 여러 번 호출하더라도 추가적인 상태 변화가 없다는 뜻
        "openWorldHint": False,  # 불특정 외부 세계와 상호작용하지 않고, 정해진 내부 범위에서 동작한다는 의미
    },
)
# 일반 파이썬 함수인 get_all_busers()가 MCP Client가 호출할 수 있는 MCP Tool로 등록
def get_all_busers(limit: int = 100) -> list[dict]:
    """
    buser 테이블의 전체 부서 목록을 조회한다.
    Args: limit: 최대 조회 건수
    Returns: 부서 정보 목록
    """
    # 최소 1건, 최대 500건으로 제한
    limit = max(1, min(limit, 500))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        sql = """
            SELECT * FROM buser ORDER BY buserno LIMIT ?
        """

        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()

        return rows

    except mariadb.Error as err:
        print("[get_all_busers 오류]", err)
        raise ToolError("부서 정보를 조회하지 못했습니다.")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# 부서번호로 조회
@mcp.tool(
    description="부서번호를 이용하여 buser 테이블에서 특정 부서를 조회한다.",
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def get_buser_by_num(buser_num: int) -> dict:
    """
    부서번호로 특정 부서를 조회한다.
    Args: buser_num: 조회할 부서번호
    Returns: 조회된 부서 정보
    """
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # 실제 컬럼명은 buserno
        sql = """
            SELECT * FROM buser
            WHERE buserno = ?
        """

        cursor.execute(sql, (buser_num,))
        row = cursor.fetchone()

        if row is None:
            return {
                "found": False,
                "message": f"{buser_num}번 부서를 찾을 수 없습니다.",
            }

        return {
            "found": True,
            "buser": row,
        }

    except mariadb.Error as err:
        print("[get_buser_by_num 오류]", err)
        raise ToolError("부서 정보를 조회하지 못했습니다.")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# 부서명으로 검색
@mcp.tool(
    description="부서명에 포함된 검색어로 buser 테이블을 검색한다.",
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def search_busers(keyword: str) -> list[dict]:
    """
    부서명에 검색어가 포함된 부서를 조회한다.
    Args: keyword: 검색할 부서명
    Returns: 검색된 부서 목록
    """
    keyword = keyword.strip()

    if not keyword:
        raise ToolError("검색어를 입력해야 합니다.")

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # 실제 컬럼명은 busername, buserno
        sql = """
            SELECT * FROM buser WHERE busername LIKE ?
            ORDER BY buserno
        """

        cursor.execute(sql, (f"%{keyword}%",))

        return cursor.fetchall()

    except mariadb.Error as err:
        print("[search_busers 오류]", err)
        raise ToolError("부서 검색을 수행하지 못했습니다.")
    finally:
        if cursor is not None: cursor.close()
        if connection is not None: connection.close()


if __name__ == "__main__":
    # Streamable HTTP 방식으로 MCP 서버 실행
    mcp.run(transport="http", host="127.0.0.1", port=8000)
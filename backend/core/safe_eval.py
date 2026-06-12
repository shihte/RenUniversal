"""
安全布林運算求值器 (Safe Boolean Evaluator)

取代規則引擎中的 eval()，避免任意程式碼執行風險。
規則語法經過替換後僅剩下 True/False 字面值與 and/or/not 邏輯運算子，
本模組使用 AST 白名單只允許這些節點，其餘一律拒絕。
"""
import ast


# 允許出現在布林運算式中的 AST 節點型別白名單
_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.UnaryOp,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Constant,
    ast.Load,
)


def safe_eval_bool(expr: str) -> bool:
    """
    安全地評估僅含 True/False/and/or/not/括號 的布林運算式。

    Args:
        expr: 已將所有變數替換為 True/False 後的純布林運算式字串。

    Returns:
        運算式的布林結果。

    Raises:
        ValueError: 當運算式包含白名單以外的語法（例如函式呼叫、屬性存取、
                    算術運算子、名稱參照等）時拋出。
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid boolean expression: {expr!r}") from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            # 僅允許布林常數
            if not isinstance(node.value, bool):
                raise ValueError(f"Disallowed constant in expression: {node.value!r}")
        elif not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"Disallowed syntax node: {type(node).__name__}")

    return bool(eval(compile(tree, "<safe_eval>", "eval"), {"__builtins__": {}}, {}))

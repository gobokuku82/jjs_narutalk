# state.py
from typing import TypedDict, List, Optional

class EmployeePerformanceState(TypedDict):
    session_id: str
    employee_id: str
    year: int
    month: int
    messages: List[str]
    current_message: str
    current_sales: Optional[float]
    prev_sales: Optional[float]
    change_rate: Optional[float]
    summary: Optional[str]
    error: Optional[str]

# tool.py
def query_employee_performance(employee_id: str, year: int, month: int):
    # 실제 DB 조회 대신 예시 데이터 반환
    if month == 5:
        return 1000.0  # 5월 실적
    elif month == 4:
        return 800.0   # 4월 실적
    else:
        return 0.0

def call_llm_summary(current_sales, prev_sales, change_rate):
    # 타입 안전성 보장
    current_sales = float(current_sales) if current_sales is not None else 0.0
    prev_sales = float(prev_sales) if prev_sales is not None else 0.0
    change_rate = float(change_rate) if change_rate is not None else 0.0
    return f"이번 달 실적은 {current_sales}원, 전월 대비 증감률은 {change_rate:.2f}%입니다."

# nodes.py
def fetch_performance_data(state: EmployeePerformanceState) -> EmployeePerformanceState:
    # 현재/전월 실적 조회
    current_sales = query_employee_performance(state['employee_id'], state['year'], state['month'])
    prev_year, prev_month = (state['year'], state['month'] - 1) if state['month'] > 1 else (state['year'] - 1, 12)
    prev_sales = query_employee_performance(state['employee_id'], prev_year, prev_month)
    state['current_sales'] = float(current_sales) if current_sales is not None else 0.0
    state['prev_sales'] = float(prev_sales) if prev_sales is not None else 0.0
    return state

def calculate_change_rate(state: EmployeePerformanceState) -> EmployeePerformanceState:
    current = state.get('current_sales')
    prev = state.get('prev_sales')
    current = float(current) if current is not None else 0.0
    prev = float(prev) if prev is not None else 0.0
    if prev > 0:
        change_rate = (current - prev) / prev * 100
    else:
        change_rate = 0 if current == 0 else 100
    state['change_rate'] = change_rate
    return state

def generate_summary(state: EmployeePerformanceState) -> EmployeePerformanceState:
    current_sales = state.get('current_sales')
    prev_sales = state.get('prev_sales')
    change_rate = state.get('change_rate')
    summary = call_llm_summary(current_sales, prev_sales, change_rate)
    state['summary'] = summary
    return state

# graph.py
from langgraph.graph import StateGraph, END

def build_employee_performance_graph():
    workflow = StateGraph(EmployeePerformanceState)
    workflow.add_node("fetch_performance_data", fetch_performance_data)
    workflow.add_node("calculate_change_rate", calculate_change_rate)
    workflow.add_node("generate_summary", generate_summary)
    workflow.set_entry_point("fetch_performance_data")
    workflow.add_edge("fetch_performance_data", "calculate_change_rate")
    workflow.add_edge("calculate_change_rate", "generate_summary")
    workflow.add_edge("generate_summary", END)
    return workflow 
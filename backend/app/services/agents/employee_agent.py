from langgraph.graph import StateGraph, END
import pandas as pd
import openai
import os

EXCEL_PATH = r'C:/FINAL_PROJECT/jjs_narutalk/data/Docs/DATABASE/총정리/내부규정/좋은제약_실적자료_최수아.xlsx'

async def extract_spike_node(state):
    employee_id = state["employee_id"]
    start_month = state["start_month"]
    end_month = state["end_month"]
    if not os.path.exists(EXCEL_PATH):
        state["spike_results"] = []
        return state
    df = pd.read_excel(EXCEL_PATH)
    df = df[df['담당자'] == employee_id]
    df['ID'] = df['ID'].fillna(method='ffill')
    df = df[df['품목'] != '합계']
    months = [str(m) for m in range(int(start_month), int(end_month)+1)]
    months = [col for col in df.columns if col in months]
    results = []
    for idx, row in df.iterrows():
        values = row[months].astype(float)
        pct_change = values.pct_change()
        for i, change in enumerate(pct_change):
            if pd.notnull(change) and change > 0.3:
                results.append({
                    '병원명': row['ID'],
                    '품목': row['품목'],
                    '월': months[i],
                    '실적': values.iloc[i],
                    '증감률': change
                })
    state["spike_results"] = results
    return state

async def llm_summary_node(state):
    summary_input = ""
    for row in state["spike_results"]:
        summary_input += f"{row['월']}, {row['병원명']}에서 {row['품목']} 실적이 전월 대비 {row['증감률']*100:.1f}% 증가 (실적: {row['실적']})\n"
    print("==== LLM에 전달되는 summary_input ====")
    print(summary_input)
    if not summary_input.strip():
        prompt = (
            f"아래 표는 {state['start_month']}부터 {state['end_month']}까지 병원별, 품목별 월별 실적 데이터입니다.\n"
            "해당 기간에는 전월 대비 30% 이상 실적이 급증한 구간이 없습니다.\n"
            "전월 대비 실적 변화가 두드러지지 않았음을 간단히 안내해 주세요.\n"
        )
    else:
        prompt = (
            f"아래 표는 {state['start_month']}부터 {state['end_month']}까지 병원별, 품목별 월별 실적 데이터입니다.\n"
            "전월 대비 30% 이상 실적이 증가한 경우만 정리해 주세요.\n"
            "각 항목에 대해 '월, 병원명, 품목, 실적, 증감률'만 간단히 표 또는 리스트로 요약해 주세요.\n"
            "추가적인 원인 분석이나 해석은 하지 마세요.\n"
            "-----\n"
            f"{summary_input}"
        )
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    state["summary"] = response.choices[0].message.content
    return state

performance_graph = StateGraph(dict)
performance_graph.add_node("extract_spike", extract_spike_node)
performance_graph.add_node("llm_summary", llm_summary_node)
performance_graph.add_edge("extract_spike", "llm_summary")
performance_graph.add_edge("llm_summary", END)
performance_graph.set_entry_point("extract_spike")

async def run_performance_pipeline(employee_id, start_month, end_month, prompt=None):
    state = {
        "employee_id": employee_id,
        "start_month": start_month,
        "end_month": end_month,
        "prompt": prompt
    }
    app = performance_graph.compile()
    final_state = await app.ainvoke(state)
    return final_state["summary"] 
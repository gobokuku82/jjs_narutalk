# LangGraph StateGraph 구현 - 파일 구조 및 작성 원리

## 📁 **파일 구조 개요**

```
backend/app/services/router_agent/
├── __init__.py                    # 패키지 초기화
├── router_agent.py               # 메인 Router Agent (하이브리드)
├── state_graph_router.py         # StateGraph 기반 Router
├── router_agent_graph.py         # 기존 Graph 기반 Router
├── router_agent_tool.py          # Tool Calling 로직
├── router_agent_nodes.py         # Agent 실행 노드
└── api_router.py                 # FastAPI 엔드포인트
```

---

## 🏗️ **아키텍처 설계 원리**

### **1. 계층 분리 원칙 (Separation of Concerns)**

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API Router (api_router.py)             │   │
│  │              - HTTP 엔드포인트 관리                  │   │
│  │              - 요청/응답 변환                        │   │
│  │              - 에러 처리                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Router Agent (router_agent.py)           │   │
│  │            - 하이브리드 라우터 선택                  │   │
│  │            - 통합 인터페이스 제공                    │   │
│  │            - 기능 위임 및 조합                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Implementation Layer                      │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │ StateGraph      │  │        Graph Router             │  │
│  │ Router          │  │      (기존 방식)                │  │
│  │ (state_graph_   │  │  (router_agent_graph.py)        │  │
│  │  router.py)     │  │                                 │  │
│  └─────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Components Layer                    │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │ Tool Calling    │  │        Agent Nodes              │  │
│  │ (router_agent_  │  │    (router_agent_nodes.py)      │  │
│  │  tool.py)       │  │                                 │  │
│  └─────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 **각 파일별 상세 설명**

### **1. `router_agent.py` - 메인 Router Agent**

#### **역할**
- **통합 인터페이스**: 모든 Router 기능의 진입점
- **하이브리드 선택**: StateGraph vs 기존 방식 선택
- **기능 위임**: 실제 처리를 하위 컴포넌트에 위임

#### **설계 원리**
```python
class RouterAgent:
    def __init__(self, use_state_graph: bool = False):
        # 선택적 초기화 - 런타임에 Router 타입 결정
        if use_state_graph:
            self.graph = StateGraphRouter()
        else:
            self.graph = RouterAgentGraph()
    
    async def route_request(self, message: str, ...):
        # 단일 인터페이스 - 내부 구현은 투명
        return await self.graph.route_request(message, ...)
```

#### **핵심 원리**
1. **의존성 주입**: 생성자에서 Router 타입 결정
2. **인터페이스 통일**: 동일한 메서드 시그니처
3. **기능 위임**: 실제 처리는 하위 컴포넌트에 위임
4. **하위 호환**: 기존 API 그대로 사용 가능

---

### **2. `state_graph_router.py` - StateGraph 기반 Router**

#### **역할**
- **LangGraph 워크플로우**: 6단계 처리 파이프라인
- **상태 관리**: 대화 기록, 실행 로그, 메타데이터
- **에러 처리**: 각 단계별 오류 관리 및 복구

#### **워크플로우 구조**
```python
# 1. StateGraph 정의
workflow = StateGraph(RouterState)

# 2. 노드 추가 (각각 독립적인 함수)
workflow.add_node("initialize_state", self._initialize_state)
workflow.add_node("process_user_input", self._process_user_input)
workflow.add_node("route_to_agent", self._route_to_agent)
workflow.add_node("execute_agent", self._execute_agent)
workflow.add_node("generate_response", self._generate_response)
workflow.add_node("save_conversation", self._save_conversation)

# 3. 엣지 연결 (순차적 실행)
workflow.set_entry_point("initialize_state")
workflow.add_edge("initialize_state", "process_user_input")
workflow.add_edge("process_user_input", "route_to_agent")
# ... 순차적 연결
workflow.add_edge("save_conversation", END)

# 4. 컴파일
self.app = workflow.compile(checkpointer=MemorySaver())
```

#### **상태 정의 원리**
```python
class RouterState(TypedDict):
    # 1. 기본 정보 (세션 관리)
    session_id: str
    user_id: Optional[str]
    current_message: str
    
    # 2. 대화 기록 (컨텍스트 유지)
    conversation_history: List[Dict[str, Any]]
    
    # 3. 라우팅 정보 (의사결정)
    selected_agent: Optional[str]
    agent_arguments: Dict[str, Any]
    routing_confidence: float
    
    # 4. 실행 결과 (데이터 전달)
    agent_response: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    # 5. 상태 제어 (플로우 제어)
    should_continue: bool
    error_message: Optional[str]
    
    # 6. 메타데이터 (모니터링)
    timestamp: str
    execution_steps: List[str]
```

#### **노드 설계 원리**
```python
async def _initialize_state(self, state: RouterState) -> RouterState:
    """상태 초기화 노드"""
    try:
        # 1. 입력 검증
        session_id = state.get("session_id") or str(uuid.uuid4())
        
        # 2. 상태 업데이트
        state.update({
            "session_id": session_id,
            "conversation_history": state.get("conversation_history", []),
            # ... 기타 초기화
        })
        
        # 3. 로깅
        logger.info(f"상태 초기화 완료: {session_id}")
        
        # 4. 수정된 상태 반환
        return state
        
    except Exception as e:
        # 5. 에러 처리
        state["should_continue"] = False
        state["error_message"] = str(e)
        return state
```

---

### **3. `router_agent_graph.py` - 기존 Graph 기반 Router**

#### **역할**
- **기존 시스템 유지**: StateGraph 도입 전 시스템
- **Tool Calling 통합**: OpenAI GPT-4o 기반 라우팅
- **Agent 실행**: 전문 Agent들의 실행 관리

#### **설계 원리**
```python
class RouterAgentGraph:
    def __init__(self):
        # 1. 컴포넌트 초기화
        self.tool_caller = RouterAgentTool()
        self.agent_nodes = RouterAgentNodes()
        
        # 2. 통계 초기화
        self.routing_stats = self._initialize_stats()
    
    async def route_request(self, message: str, ...):
        # 1. Tool Calling으로 Agent 선택
        tool_result = await self.tool_caller.call_tool(message)
        
        # 2. Agent 실행
        if tool_result["tool_call"]:
            agent_result = await self.agent_nodes.execute_agent(...)
        
        # 3. 결과 반환
        return self._format_response(agent_result)
```

---

### **4. `router_agent_tool.py` - Tool Calling 로직**

#### **역할**
- **OpenAI 통신**: GPT-4o API 호출
- **함수 정의**: 4개 전문 Agent 함수 정의
- **라우팅 결정**: 사용자 입력 분석 및 Agent 선택

#### **함수 정의 원리**
```python
def _get_tool_definitions(self) -> List[Dict[str, Any]]:
    """Tool 함수 정의"""
    return [
        {
            "type": "function",
            "function": {
                "name": "db_agent",
                "description": "내부 벡터 검색 Agent - 문서 검색, 정책 검색, 지식베이스 QA",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색할 질문이나 키워드"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        # ... 다른 Agent들
    ]
```

#### **Tool Calling 원리**
```python
async def call_tool(self, message: str) -> Dict[str, Any]:
    """OpenAI Tool Calling 실행"""
    try:
        # 1. OpenAI API 호출
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message}],
            tools=self.tool_definitions,
            tool_choice="auto"
        )
        
        # 2. Tool Call 분석
        tool_calls = response.choices[0].message.tool_calls
        
        if tool_calls:
            # 3. Tool Call이 있는 경우
            tool_call = tool_calls[0]
            return {
                "tool_call": {
                    "function_name": tool_call.function.name,
                    "function_args": json.loads(tool_call.function.arguments),
                    "confidence": 0.9
                }
            }
        else:
            # 4. 일반 대화 응답
            return {
                "general_response": response.choices[0].message.content,
                "confidence": 0.5
            }
            
    except Exception as e:
        return {"error": str(e)}
```

---

### **5. `router_agent_nodes.py` - Agent 실행 노드**

#### **역할**
- **Agent 실행**: 4개 전문 Agent의 실제 실행
- **결과 통합**: Agent별 응답 및 소스 통합
- **상태 관리**: Agent별 상태 및 헬스 체크

#### **Agent 실행 원리**
```python
async def execute_agent(self, agent_name: str, arguments: Dict[str, Any], original_message: str) -> Dict[str, Any]:
    """Agent 실행"""
    try:
        # 1. Agent 선택
        if agent_name == "db_agent":
            return await self._execute_db_agent(arguments, original_message)
        elif agent_name == "docs_agent":
            return await self._execute_docs_agent(arguments, original_message)
        # ... 다른 Agent들
        
    except Exception as e:
        return {
            "response": f"Agent 실행 중 오류가 발생했습니다: {str(e)}",
            "sources": [],
            "metadata": {"error": str(e)}
        }
```

#### **Agent별 구현 원리**
```python
async def _execute_db_agent(self, arguments: Dict[str, Any], original_message: str) -> Dict[str, Any]:
    """DB Agent 실행"""
    try:
        # 1. 인수 추출
        query = arguments.get("query", original_message)
        
        # 2. 벡터 검색 실행
        from ..db_agent.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        search_results = await embedding_service.search_documents(query)
        
        # 3. 결과 포맷팅
        return {
            "response": self._format_search_results(search_results),
            "sources": search_results.get("sources", []),
            "metadata": {
                "agent": "db_agent",
                "query": query,
                "result_count": len(search_results.get("sources", []))
            }
        }
        
    except Exception as e:
        return {"response": f"DB 검색 중 오류: {str(e)}", "sources": [], "metadata": {"error": str(e)}}
```

---

### **6. `api_router.py` - FastAPI 엔드포인트**

#### **역할**
- **HTTP 인터페이스**: RESTful API 제공
- **요청/응답 변환**: JSON ↔ Python 객체 변환
- **에러 처리**: HTTP 상태 코드 및 에러 메시지

#### **라우터 설계 원리**
```python
# 1. Router Agent 인스턴스 (두 가지 방식)
router_agent_state = RouterAgent(use_state_graph=True)
router_agent_normal = RouterAgent(use_state_graph=False)

# 2. 요청 모델
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    use_state_graph: Optional[bool] = False  # 선택적 StateGraph 사용

# 3. 엔드포인트
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # StateGraph 사용 여부에 따라 Router Agent 선택
    router_agent = router_agent_state if request.use_state_graph else router_agent_normal
    
    # 요청 처리
    result = await router_agent.route_request(
        message=request.message,
        user_id=request.user_id,
        session_id=request.session_id
    )
    
    # 응답 변환
    return ChatResponse(**result)
```

---

## 🔧 **설계 패턴 및 원리**

### **1. 전략 패턴 (Strategy Pattern)**

```python
# Router 타입을 런타임에 선택
class RouterAgent:
    def __init__(self, use_state_graph: bool = False):
        if use_state_graph:
            self.graph = StateGraphRouter()  # StateGraph 전략
        else:
            self.graph = RouterAgentGraph()  # 기존 전략
```

### **2. 템플릿 메서드 패턴 (Template Method Pattern)**

```python
# StateGraph 워크플로우 - 고정된 순서, 가변적 구현
workflow.add_node("initialize_state", self._initialize_state)
workflow.add_node("process_user_input", self._process_user_input)
workflow.add_node("route_to_agent", self._route_to_agent)
# ... 고정된 순서로 실행
```

### **3. 팩토리 패턴 (Factory Pattern)**

```python
# Agent 생성 및 실행
async def execute_agent(self, agent_name: str, ...):
    if agent_name == "db_agent":
        return await self._execute_db_agent(...)
    elif agent_name == "docs_agent":
        return await self._execute_docs_agent(...)
    # ... Agent별 팩토리 메서드
```

### **4. 옵저버 패턴 (Observer Pattern)**

```python
# 상태 변화 추적
state["execution_steps"].append("agent_executed")
state["timestamp"] = datetime.now().isoformat()
# ... 상태 변화를 자동으로 다음 노드에 전달
```

---

## 📊 **모듈 간 의존성**

### **의존성 그래프**

```
api_router.py
    ↓
router_agent.py
    ↓
┌─────────────────┬─────────────────┐
│ state_graph_    │ router_agent_   │
│ router.py       │ graph.py        │
    ↓                   ↓
┌─────────────────┬─────────────────┐
│ router_agent_   │ router_agent_   │
│ tool.py         │ nodes.py        │
    ↓                   ↓
┌─────────────────┬─────────────────┐
│ OpenAI API      │ Agent Modules   │
│ (External)      │ (db_agent, etc.)│
```

### **순환 의존성 방지**

```python
# Lazy Import 사용
def __init__(self, use_state_graph: bool = False):
    if use_state_graph:
        from .state_graph_router import StateGraphRouter  # 지연 로딩
        self.graph = StateGraphRouter()
    else:
        from .router_agent_graph import RouterAgentGraph  # 지연 로딩
        self.graph = RouterAgentGraph()
```

---

## 🎯 **코딩 원칙**

### **1. 단일 책임 원칙 (SRP)**
- 각 파일은 하나의 명확한 책임만 가짐
- `state_graph_router.py`: StateGraph 워크플로우만 담당
- `router_agent_tool.py`: Tool Calling만 담당

### **2. 개방-폐쇄 원칙 (OCP)**
- 기존 코드 수정 없이 새로운 기능 추가 가능
- 새로운 Agent 추가 시 `router_agent_nodes.py`만 수정

### **3. 리스코프 치환 원칙 (LSP)**
- StateGraph Router와 Graph Router가 동일한 인터페이스 구현
- 런타임에 자유롭게 교체 가능

### **4. 인터페이스 분리 원칙 (ISP)**
- 각 컴포넌트는 필요한 인터페이스만 의존
- Tool Calling과 Agent 실행이 분리됨

### **5. 의존성 역전 원칙 (DIP)**
- 고수준 모듈이 저수준 모듈에 의존하지 않음
- 추상화를 통한 의존성 역전

---

## 🔄 **상태 관리 원리**

### **1. 불변성 (Immutability)**
```python
# 상태 업데이트 시 새로운 객체 생성
state.update({
    "selected_agent": function_name,
    "agent_arguments": function_args,
    "routing_confidence": confidence
})
```

### **2. 단방향 데이터 흐름**
```
사용자 입력 → 상태 초기화 → 입력 처리 → 라우팅 → 
Agent 실행 → 응답 생성 → 대화 저장 → 응답
```

### **3. 상태 정규화**
```python
# 관련 데이터를 하나의 상태 객체에 통합
class RouterState(TypedDict):
    # 세션 정보
    session_id: str
    user_id: Optional[str]
    
    # 대화 정보
    conversation_history: List[Dict[str, Any]]
    current_message: str
    
    # 실행 정보
    selected_agent: Optional[str]
    agent_response: str
    execution_steps: List[str]
```

---

## 🚀 **확장성 고려사항**

### **1. 새로운 Agent 추가**
```python
# 1. Tool 정의 추가 (router_agent_tool.py)
{
    "name": "new_agent",
    "description": "새로운 Agent 설명",
    "parameters": {...}
}

# 2. 실행 로직 추가 (router_agent_nodes.py)
async def _execute_new_agent(self, arguments: Dict[str, Any], original_message: str):
    # 새로운 Agent 실행 로직
    pass

# 3. 라우팅 로직 추가 (execute_agent 메서드)
if agent_name == "new_agent":
    return await self._execute_new_agent(arguments, original_message)
```

### **2. 새로운 노드 추가**
```python
# 1. 노드 함수 정의
async def _new_node(self, state: RouterState) -> RouterState:
    # 새로운 노드 로직
    return state

# 2. 워크플로우에 추가
workflow.add_node("new_node", self._new_node)
workflow.add_edge("previous_node", "new_node")
workflow.add_edge("new_node", "next_node")
```

### **3. 새로운 상태 필드 추가**
```python
class RouterState(TypedDict):
    # 기존 필드들...
    
    # 새로운 필드 추가
    new_field: Optional[str]
    new_metadata: Dict[str, Any]
```

---

## 📝 **결론**

이 파일 구조와 작성 원리는 다음과 같은 핵심 가치를 반영합니다:

1. **모듈화**: 각 기능이 독립적인 파일로 분리
2. **확장성**: 새로운 기능 추가가 용이
3. **유지보수성**: 명확한 책임 분리로 유지보수 용이
4. **테스트 가능성**: 각 컴포넌트를 독립적으로 테스트 가능
5. **재사용성**: 컴포넌트 간 느슨한 결합으로 재사용 가능

이러한 설계를 통해 NaruTalk AI 시스템은 지속적으로 발전하고 확장할 수 있는 견고한 기반을 갖추게 되었습니다! 🎯 
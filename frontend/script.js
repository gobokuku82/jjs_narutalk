// 전역 변수
let sessionId = generateSessionId();
let userId = generateUserId();
let isLoading = false;

// DOM 요소들
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const chatMessages = document.getElementById('chatMessages');
const chatbotToggle = document.getElementById('chatbotToggle');
const clearChatBtn = document.getElementById('clearChat');
const exportChatBtn = document.getElementById('exportChat');
const loadingOverlay = document.getElementById('loadingOverlay');

// 디버깅 모드 (개발 환경에서 true로 설정)
const DEBUG_MODE = true;

// 디버깅 로그 함수
function debugLog(message, data = null) {
    if (DEBUG_MODE) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

// 세션 ID 생성
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 사용자 ID 생성
function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    debugLog('DOM 로드 완료');
    
    // 메시지 전송 이벤트
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Agent 시스템 정보 표시
    console.log('4개 전문 AI Agent 자동 라우팅 시스템 활성화');

    // 챗봇 토글 버튼 (현재 페이지이므로 사실상 필요 없지만 일단 구현)
    chatbotToggle.addEventListener('click', function() {
        // 현재 페이지에 이미 있으므로 스크롤을 채팅 영역으로 이동
        document.querySelector('.chat-area').scrollIntoView({ behavior: 'smooth' });
    });

    // 대화 지우기
    clearChatBtn.addEventListener('click', clearChat);
    
    // 대화 내보내기
    exportChatBtn.addEventListener('click', exportChat);

    // 네비게이션 메뉴 이벤트
    setupNavigation();

    console.log('NaruTalk AI Assistant 초기화 완료');
    console.log('Session ID:', sessionId);
    console.log('User ID:', userId);
    console.log('Main Agent Router: 4개 전문 Agent 자동 라우팅');
    
    // 서버 연결 테스트
    testServerConnection();
});

// 서버 연결 테스트
async function testServerConnection() {
    try {
        debugLog('서버 연결 테스트 시작');
        const response = await fetch('/api/v1/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            debugLog('서버 연결 성공', data);
        } else {
            debugLog('서버 연결 실패', { status: response.status, statusText: response.statusText });
        }
    } catch (error) {
        debugLog('서버 연결 테스트 오류', error);
    }
}

// 메시지 전송 함수 (스트리밍 방식)
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isLoading) return;

    debugLog('메시지 전송 시작', { message: message.substring(0, 50) + '...' });

    // 사용자 메시지 표시
    addMessage(message, 'user');
    chatInput.value = '';

    // 실시간 로딩 표시
    showStreamingLoading();
    
    // 스트리밍 응답을 받을 메시지 컨테이너 생성
    const messageContainer = createBotMessageContainer();
    let currentContent = '';
    let agentType = 'unknown';
    let finalData = null;
    let hasError = false;

    try {
        // 스트리밍 엔드포인트 호출 - 직접 URL 확인
        const endpoint = '/api/v1/tool-calling/chat/stream';
        
        // 브라우저 콘솔에서 확인할 수 있도록 전체 URL 출력
        console.log('[DEBUG] 호출할 전체 URL:', window.location.origin + endpoint);
        debugLog('스트리밍 API 호출', { endpoint, message: message.substring(0, 50) + '...' });
        
        // 디버깅을 위한 추가 정보
        console.log('[DEBUG] 전체 요청 정보:', {
            url: endpoint,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: { message: message, session_id: sessionId }
        });
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        debugLog('API 응답 받음', { status: response.status, ok: response.ok });

        if (!response.ok) {
            const errorText = await response.text();
            debugLog('API 오류 응답', { status: response.status, error: errorText });
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // 스트리밍 중 연결 끊김 감지를 위한 타이머
        let timeoutId = null;
        const resetTimeout = () => {
            if (timeoutId) clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                debugLog('스트리밍 타임아웃 발생');
                reader.cancel();
                throw new Error('스트리밍 응답 시간 초과 (30초)');
            }, 30000); // 30초 타이머
        };
        
        resetTimeout();
        
        let lineCount = 0;
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                debugLog('스트리밍 완료', { lineCount });
                if (timeoutId) clearTimeout(timeoutId);
                break;
            }
            
            resetTimeout(); // 데이터를 받을 때마다 타이머 리셋
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                lineCount++;
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6); // 'data: ' 제거
                    
                    if (dataStr === '[DONE]') {
                        // 스트리밍 완료
                        debugLog('스트리밍 완료 신호 받음');
                        hideStreamingLoading();
                        
                        // 최종 Agent 정보 표시
                        if (finalData && finalData.agent) {
                            addAgentBadgeToMessage(messageContainer, finalData.agent);
                        }
                        
                        // 소스 정보가 있으면 표시
                        if (finalData && finalData.sources && finalData.sources.length > 0) {
                            addSourcesInfo(finalData.sources);
                        }
                        
                        console.log('스트리밍 완료');
                        return;
                    }
                    
                    try {
                        const data = JSON.parse(dataStr);
                        debugLog('스트리밍 데이터 수신', { type: data.type, data: data });
                        
                        switch (data.type) {
                            case 'start':
                                updateLoadingMessage('AI가 분석 중입니다...');
                                agentType = data.agent || 'unknown';
                                break;
                            case 'agent_selection':
                                updateLoadingMessage('적절한 전문 Agent를 선택하고 있습니다...');
                                break;
                            case 'agent_info':
                                agentType = data.agent;
                                updateLoadingMessage(`${data.agent} Agent가 처리합니다...`);
                                break;
                            case 'token':
                                // 토큰별로 텍스트 누적 (공백 제거 - 한국어는 토큰간 공백이 불필요)
                                if (data.word) {
                                    currentContent += data.word;
                                    updateBotMessageContent(messageContainer, currentContent, false);
                                }
                                break;
                            case 'content':
                                // 실시간으로 텍스트 업데이트
                                currentContent = data.content;
                                const isFinal = data.is_final || false;
                                updateBotMessageContent(messageContainer, currentContent, isFinal);
                                break;
                            case 'complete':
                                finalData = data;
                                if (data.content) {
                                    currentContent = data.content;
                                    updateBotMessageContent(messageContainer, currentContent, true);
                                }
                                break;
                            case 'error':
                                hasError = true;
                                throw new Error(data.message);
                        }
                    } catch (parseError) {
                        debugLog('JSON 파싱 오류', { error: parseError, dataStr });
                        // 파싱 오류는 무시하고 계속 진행
                    }
                }
            }
        }

    } catch (error) {
        debugLog('스트리밍 메시지 전송 오류', error);
        hideStreamingLoading();
        
        // 에러 메시지 표시
        const errorMessage = `죄송합니다. 오류가 발생했습니다: ${error.message}`;
        addMessage(errorMessage, 'bot');
        
        // 디버깅 정보 추가
        if (DEBUG_MODE) {
            const debugInfo = `디버그 정보: ${error.stack || error.message}`;
            addMessage(debugInfo, 'bot');
        }
    }
}

// 메시지 추가 함수
function addMessage(text, sender, agentType = null, agentArgs = null) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';

    const message = document.createElement('div');
    message.className = `message ${sender}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    // 아바타 아이콘 설정
    if (sender === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    } else if (sender === 'system') {
        avatar.innerHTML = '<i class="fas fa-cog"></i>';
    } else {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    }

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = formatTime(new Date());

    content.appendChild(messageText);
    content.appendChild(messageTime);

    // 봇 메시지인 경우 Agent 정보 추가
    if (sender === 'bot' && agentType) {
        const agentInfo = document.createElement('div');
        agentInfo.className = 'agent-info-badge';
        
        // Agent 타입별 아이콘 및 이름 매핑
        const agentDisplay = getAgentDisplayInfo(agentType);
        
        agentInfo.innerHTML = `
            <i class="${agentDisplay.icon}"></i>
            ${agentDisplay.name}
        `;
        content.appendChild(agentInfo);
    }

    message.appendChild(avatar);
    message.appendChild(content);
    messageContainer.appendChild(message);

    chatMessages.appendChild(messageContainer);
    scrollToBottom();
}

// Agent 표시 정보 반환 함수
function getAgentDisplayInfo(agentType) {
    const agentMap = {
        'chroma_db_agent': {
            name: '📄 문서 검색',
            icon: 'fas fa-file-search'
        },
        'employee_db_agent': {
            name: '👥 직원 정보',
            icon: 'fas fa-users'
        },
        'client_analysis_agent': {
            name: '📊 고객 분석',
            icon: 'fas fa-chart-line'
        },
        'rule_compliance_agent': {
            name: '📋 규정 분석',
            icon: 'fas fa-shield-alt'
        },
        'general_chat': {
            name: '💬 일반 대화',
            icon: 'fas fa-comments'
        }
    };
    
    return agentMap[agentType] || {
        name: `🤖 ${agentType}`,
        icon: 'fas fa-robot'
    };
}

// 소스 정보 추가 함수
function addSourcesInfo(sources) {
    const sourceContainer = document.createElement('div');
    sourceContainer.className = 'message-container';

    const sourceMessage = document.createElement('div');
    sourceMessage.className = 'message bot-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-book"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const sourceText = document.createElement('div');
    sourceText.className = 'message-text';
    sourceText.innerHTML = `
        <strong>참고 문서:</strong><br>
        ${sources.map(source => `• ${source.title || source.filename || '문서'}`).join('<br>')}
    `;

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = formatTime(new Date());

    content.appendChild(sourceText);
    content.appendChild(messageTime);

    sourceMessage.appendChild(avatar);
    sourceMessage.appendChild(content);
    sourceContainer.appendChild(sourceMessage);

    chatMessages.appendChild(sourceContainer);
    scrollToBottom();
}

// 로딩 표시/숨기기
function showLoading() {
    isLoading = true;
    loadingOverlay.style.display = 'flex';
    sendButton.disabled = true;
}

function hideLoading() {
    isLoading = false;
    loadingOverlay.style.display = 'none';
    sendButton.disabled = false;
}

// 스트리밍 로딩 관련 함수들
let streamingLoadingContainer = null;

function showStreamingLoading() {
    isLoading = true;
    sendButton.disabled = true;
    
    // 기존 로딩 오버레이 숨기기
    loadingOverlay.style.display = 'none';
    
    // 채팅 메시지 영역에 실시간 로딩 표시
    streamingLoadingContainer = document.createElement('div');
    streamingLoadingContainer.className = 'message-container streaming-loading';
    
    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'message bot-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar streaming-avatar';
    avatar.innerHTML = '<i class="fas fa-robot fa-spin"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content streaming-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text loading-text';
    messageText.innerHTML = '<span class="typing-indicator">AI가 분석 중입니다<span class="dots">...</span></span>';
    
    content.appendChild(messageText);
    loadingMessage.appendChild(avatar);
    loadingMessage.appendChild(content);
    streamingLoadingContainer.appendChild(loadingMessage);
    
    chatMessages.appendChild(streamingLoadingContainer);
    scrollToBottom();
}

function hideStreamingLoading() {
    isLoading = false;
    sendButton.disabled = false;
    
    if (streamingLoadingContainer) {
        streamingLoadingContainer.remove();
        streamingLoadingContainer = null;
    }
}

function updateLoadingMessage(message) {
    if (streamingLoadingContainer) {
        const loadingText = streamingLoadingContainer.querySelector('.loading-text');
        if (loadingText) {
            loadingText.innerHTML = `<span class="typing-indicator">${message}<span class="dots">...</span></span>`;
        }
    }
}

function createBotMessageContainer() {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';

    const message = document.createElement('div');
    message.className = 'message bot-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text streaming-text';
    messageText.textContent = '';

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = formatTime(new Date());

    content.appendChild(messageText);
    content.appendChild(messageTime);
    message.appendChild(avatar);
    message.appendChild(content);
    messageContainer.appendChild(message);

    chatMessages.appendChild(messageContainer);
    scrollToBottom();
    
    return messageContainer;
}

function updateBotMessageContent(container, content, isFinal = false) {
    const messageText = container.querySelector('.message-text');
    if (messageText) {
        messageText.textContent = content;
        
        // 최종 메시지인 경우 스트리밍 스타일 제거
        if (isFinal) {
            messageText.classList.remove('streaming-text');
            
            // 메시지 내용이 완성된 후 일반 스타일로 변경
            const messageContent = container.querySelector('.message-content');
            if (messageContent) {
                messageContent.style.background = 'white';
                messageContent.style.border = 'none';
            }
        }
        
        scrollToBottom();
    }
}

function addAgentBadgeToMessage(container, agentType) {
    const content = container.querySelector('.message-content');
    if (content) {
        const agentDisplay = getAgentDisplayInfo(agentType);
        
        const agentInfo = document.createElement('div');
        agentInfo.className = 'agent-info-badge';
        agentInfo.innerHTML = `
            <i class="${agentDisplay.icon}"></i>
            ${agentDisplay.name}
        `;
        content.appendChild(agentInfo);
    }
}

// 대화 지우기
function clearChat() {
    if (confirm('모든 대화를 지우시겠습니까?')) {
        // 초기 메시지만 남기고 모든 메시지 제거
        chatMessages.innerHTML = `
            <div class="message-container">
                <div class="message bot-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-text">안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?</div>
                        <div class="message-time">${formatTime(new Date())}</div>
                    </div>
                </div>
            </div>
        `;
        
        // 새로운 세션 시작
        sessionId = generateSessionId();
        console.log('새 세션 시작:', sessionId);
    }
}

// 대화 내보내기
function exportChat() {
    const messages = [];
    const messageElements = chatMessages.querySelectorAll('.message');
    
    messageElements.forEach(msg => {
        const isUser = msg.classList.contains('user-message');
        const text = msg.querySelector('.message-text').textContent;
        const time = msg.querySelector('.message-time').textContent;
        
        messages.push({
            sender: isUser ? 'User' : 'AI',
            message: text,
            time: time
        });
    });

    const exportData = {
        session_id: sessionId,
        user_id: userId,
        exported_at: new Date().toISOString(),
        messages: messages
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `narutalk_chat_${sessionId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 네비게이션 설정
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 모든 메뉴에서 active 클래스 제거
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // 클릭된 메뉴에 active 클래스 추가
            this.classList.add('active');
            
            // 메뉴 이름 가져오기
            const menuName = this.querySelector('span').textContent;
            console.log('메뉴 선택:', menuName);
            
            // 여기에 메뉴별 동작 추가 (나중에 확장 가능)
            handleMenuSelection(menuName);
        });
    });
}

// 메뉴 선택 처리
function handleMenuSelection(menuName) {
    // 현재는 콘솔에만 로그 출력
    // 나중에 각 메뉴에 따른 컨텐츠 변경 기능 추가 가능
    switch(menuName) {
        case '홈':
            console.log('홈 메뉴 선택됨');
            break;
        case '대시보드':
            console.log('대시보드 메뉴 선택됨');
            break;
        case '고객 관리':
            console.log('고객 관리 메뉴 선택됨');
            break;
        case '문서 관리':
            console.log('문서 관리 메뉴 선택됨');
            break;
        case '일정 관리':
            console.log('일정 관리 메뉴 선택됨');
            break;
        case 'AI 분석':
            console.log('AI 분석 메뉴 선택됨');
            break;
        case '문서 검색':
            console.log('문서 검색 메뉴 선택됨');
            break;
        case '설정':
            console.log('설정 메뉴 선택됨');
            break;
        default:
            console.log('알 수 없는 메뉴:', menuName);
    }
}

// 유틸리티 함수들
function formatTime(date) {
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // 1분 미만
        return '방금 전';
    } else if (diff < 3600000) { // 1시간 미만
        return Math.floor(diff / 60000) + '분 전';
    } else if (diff < 86400000) { // 1일 미만
        return Math.floor(diff / 3600000) + '시간 전';
    } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 키보드 단축키
document.addEventListener('keydown', function(e) {
    // Ctrl + / : 채팅 입력 포커스
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        chatInput.focus();
    }
    
    // ESC : 채팅 입력 블러
    if (e.key === 'Escape') {
        chatInput.blur();
    }
});

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    console.log('NaruTalk AI Assistant 종료');
}); 
import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatScreen.css';

function ChatScreen() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
      timestamp: new Date().toLocaleString(),
      agentType: null
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
  const [userId] = useState(() => 'user_' + Math.random().toString(36).substr(2, 9));
  
  const messagesEndRef = useRef(null);
  const DEBUG_MODE = true;

  // 디버깅 로그 함수
  const debugLog = (message, data = null) => {
    if (DEBUG_MODE) {
      console.log(`[DEBUG] ${message}`, data);
    }
  };

  // 스크롤을 맨 아래로 이동
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Agent 표시 정보 반환 함수
  const getAgentDisplayInfo = (agentType) => {
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
  };

  // 메시지 전송 함수 (스트리밍 방식)
  const sendMessage = async () => {
    const message = inputMessage.trim();
    if (!message || isLoading) return;

    debugLog('메시지 전송 시작', { message: message.substring(0, 50) + '...' });

    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: message,
      timestamp: new Date().toLocaleString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // 봇 메시지 컨테이너 생성 (스트리밍용)
    const botMessageId = Date.now() + 1;
    const initialBotMessage = {
      id: botMessageId,
      sender: 'ai',
      content: '',
      timestamp: new Date().toLocaleString(),
      agentType: null,
      isStreaming: true
    };
    setMessages(prev => [...prev, initialBotMessage]);

    let currentContent = '';
    let agentType = 'unknown';
    let finalData = null;
    let hasError = false;

    try {
      const endpoint = '/api/v1/tool-calling/chat/stream';
      
      debugLog('스트리밍 API 호출', { endpoint, message: message.substring(0, 50) + '...' });
      
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

        console.log('🌐 API 응답 받음:', { status: response.status, ok: response.ok, headers: Object.fromEntries(response.headers.entries()) });
        debugLog('API 응답 받음', { status: response.status, ok: response.ok });

      if (!response.ok) {
        const errorText = await response.text();
        debugLog('API 오류 응답', { status: response.status, error: errorText });
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

              const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        console.log('📖 스트리밍 리더 생성됨');
        
        let timeoutId = null;
        const resetTimeout = () => {
          if (timeoutId) clearTimeout(timeoutId);
          timeoutId = setTimeout(() => {
            debugLog('스트리밍 타임아웃 발생');
            reader.cancel();
            throw new Error('스트리밍 응답 시간 초과 (30초)');
          }, 30000);
        };
        
        resetTimeout();
        
        let lineCount = 0;
        while (true) {
          const { done, value } = await reader.read();
          
          console.log('📦 청크 읽음:', { done, valueLength: value?.length });
          
          if (done) {
            console.log('🏁 스트리밍 완료:', { lineCount });
            debugLog('스트리밍 완료', { lineCount });
            if (timeoutId) clearTimeout(timeoutId);
            break;
          }
          
          resetTimeout();
          
          const chunk = decoder.decode(value);
          console.log('🔤 디코딩된 청크:', chunk);
          const lines = chunk.split('\n');
        
                for (const line of lines) {
          lineCount++;
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            
            if (dataStr === '[DONE]') {
              debugLog('스트리밍 완료 신호 받음');
              
              // 최종 메시지 업데이트
              setMessages(prev => prev.map(msg => 
                msg.id === botMessageId 
                  ? { ...msg, content: currentContent, agentType: finalData?.agent, isStreaming: false }
                  : msg
              ));
              
              console.log('스트리밍 완료');
              return;
            }
            
            if (dataStr.trim() === '') continue;
            
            try {
              const data = JSON.parse(dataStr);
              console.log('🔍 스트리밍 데이터 수신:', { type: data.type, data: data });
              debugLog('스트리밍 데이터 수신', { type: data.type, data: data });
              
              switch (data.type) {
                case 'start':
                  console.log('🚀 시작:', data);
                  agentType = data.agent || 'unknown';
                  break;
                case 'agent_selection':
                  console.log('🎯 에이전트 선택:', data);
                  break;
                case 'agent_info':
                  console.log('🤖 에이전트 정보:', data);
                  agentType = data.agent;
                  finalData = { ...finalData, agent: data.agent };
                  break;
                case 'token':
                  console.log('📝 토큰:', data);
                  if (data.word) {
                    currentContent += data.word;
                    setMessages(prev => prev.map(msg => 
                      msg.id === botMessageId 
                        ? { ...msg, content: currentContent }
                        : msg
                    ));
                  }
                  break;
                case 'content':
                  console.log('📄 컨텐츠:', data);
                  currentContent = data.content || '';
                  const isFinal = data.is_final || false;
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: currentContent, isStreaming: !isFinal }
                      : msg
                  ));
                  break;
                case 'complete':
                  console.log('✅ 완료:', data);
                  finalData = data;
                  if (data.content) {
                    currentContent = data.content;
                  }
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: currentContent, agentType: data.agent, isStreaming: false }
                      : msg
                  ));
                  break;
                case 'error':
                  console.log('❌ 에러:', data);
                  hasError = true;
                  throw new Error(data.message);
                default:
                  console.log('❓ 알 수 없는 타입:', data.type);
                  debugLog('알 수 없는 데이터 타입', { type: data.type });
              }
            } catch (parseError) {
              debugLog('JSON 파싱 오류', { error: parseError, dataStr });
            }
          }
        }
      }

    } catch (error) {
      debugLog('스트리밍 메시지 전송 오류', error);
      
      // 에러 메시지 표시 (하나의 메시지로 통합)
      const errorMessage = `죄송합니다. 오류가 발생했습니다: ${error.message}`;
      if (DEBUG_MODE) {
        errorMessage += `\n\n디버그 정보: ${error.stack || error.message}`;
      }
      
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId 
          ? { ...msg, content: errorMessage, isStreaming: false }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    if (window.confirm('모든 대화를 지우시겠습니까?')) {
      setMessages([{
        id: Date.now(),
        sender: 'ai',
        content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
        timestamp: new Date().toLocaleString(),
        agentType: null
      }]);
    }
  };

  return (
    <div className="chat-screen">
      <div className="chat-header">
        <div className="header-left">
          <h1>AI 채팅</h1>
        </div>
        <div className="header-center">
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Pharma-Helper</span>
          </div>
        </div>
        <div className="header-right">
          <nav className="header-nav">
            <a href="#" className="nav-link" onClick={(e) => { e.preventDefault(); navigate('/'); }}>홈</a>
            <a href="#" className="nav-link active">AI 채팅</a>
            <a href="#" className="nav-link">고객/데이터 위키</a>
            <a href="#" className="nav-link">문서 생성</a>
            <a href="#" className="nav-link">실적 확인</a>
          </nav>
          <div className="header-actions">
            <button className="notification-btn">🔔</button>
            <div className="user-profile">
              <img src="https://via.placeholder.com/32x32" alt="User" />
            </div>
          </div>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-sidebar">
          <div className="chat-history">
            <h3>Chat</h3>
            <button className="new-chat-btn" onClick={clearChat}>+ New Chat</button>
            <div className="chat-list">
              <div className="chat-item">
                <span className="chat-icon">💬</span>
                <span className="chat-date">2024-07-29</span>
                <span className="chat-arrow">→</span>
              </div>
              <div className="chat-item">
                <span className="chat-icon">💬</span>
                <span className="chat-date">2024-07-28</span>
                <span className="chat-arrow">→</span>
              </div>
              <div className="chat-item">
                <span className="chat-icon">💬</span>
                <span className="chat-date">2024-07-27</span>
                <span className="chat-arrow">→</span>
              </div>
              <div className="chat-item">
                <span className="chat-icon">💬</span>
                <span className="chat-date">2024-07-16</span>
                <span className="chat-arrow">→</span>
              </div>
            </div>
          </div>
        </div>

        <div className="chat-main">
          <div className="chat-title">
            <h2>Chat with AI</h2>
          </div>
          
          <div className="messages-container">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}-message ${message.isStreaming ? 'streaming' : ''}`}>
                <div className="message-content">
                  {message.content}
                  {message.isStreaming && <span className="typing-indicator">...</span>}
                </div>
                {message.agentType && (
                  <div className="agent-badge">
                    {getAgentDisplayInfo(message.agentType).name}
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="message-input-container">
            <input
              type="text"
              placeholder="Type your message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              className="message-input"
              disabled={isLoading}
            />
            <button onClick={sendMessage} className="send-button" disabled={isLoading}>
              {isLoading ? '전송 중...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatScreen; 
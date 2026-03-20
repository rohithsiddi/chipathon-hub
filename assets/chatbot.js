document.addEventListener('DOMContentLoaded', () => {
  // Create widget button
  const btn = document.createElement('div');
  btn.id = 'chat-widget-button';
  btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="28px" height="28px"><path d="M12 2C6.48 2 2 5.92 2 10.75c0 2.82 1.63 5.33 4.1 6.88L5.5 22l3.74-2.12c.88.24 1.8.37 2.76.37 5.52 0 10-3.92 10-8.75S17.52 2 12 2z"/></svg>`;
  document.body.appendChild(btn);

  // Create widget container
  const container = document.createElement('div');
  container.id = 'chat-widget-container';
  container.innerHTML = `
    <div class="chat-widget-header">
      <span style="display:flex; align-items:center; gap:8px;">🤖 Ask Chipathon AI</span>
      <button id="chat-widget-close">&times;</button>
    </div>
    <div id="chat-widget-history" class="chat-history">
      <div class="message bot-message">Hi! I'm the Chipathon AI. Ask me anything about OpenROAD flows.</div>
    </div>
    <div class="chat-widget-input-area">
      <input type="text" id="chat-widget-input" placeholder="Ask about DRC, Setup, Logs..." />
      <button id="chat-widget-send">Send</button>
    </div>
  `;
  document.body.appendChild(container);

  const toggleWidget = () => {
    container.classList.toggle('open');
    if (container.classList.contains('open')) {
      document.getElementById('chat-widget-input').focus();
    }
  };

  btn.addEventListener('click', toggleWidget);
  document.getElementById('chat-widget-close').addEventListener('click', toggleWidget);

  const input = document.getElementById('chat-widget-input');
  const sendBtn = document.getElementById('chat-widget-send');
  const history = document.getElementById('chat-widget-history');

  function addMessage(text, isUser, citations = [], isError = false) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    // Very basic Markdown parsing for the UI
    let content = text.replace(/\n\n/g, '<br/><br/>').replace(/\n/g, '<br/>');
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    content = content.replace(/`(.*?)`/g, '<code>$1</code>');
    content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="text-decoration: underline;">$1</a>');
    
    div.innerHTML = content;
    
    if (citations && citations.length > 0) {
      const citDiv = document.createElement('div');
      citDiv.className = 'citation';
      citDiv.innerHTML = '<strong>Sources:</strong><br/>' + citations.map(c => `<span class="citation-item">🔗 ${c}</span>`).join('<br/>');
      div.appendChild(citDiv);
    }
    
    if (isError) {
      div.style.color = '#ef5350';
    }
    
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
    return div;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    sendBtn.disabled = true;
    addMessage(text, true);

    const loadingMsg = addMessage('Analyzing OpenROAD documentation...', false);
    loadingMsg.classList.add('loading');

    try {
      const response = await fetch('https://rohithsiddi-chipathon-api.hf.space/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });
      const data = await response.json();
      
      loadingMsg.remove();
      
      if (data.error) {
         addMessage('Server Error: ' + data.error, false, [], true);
      } else {
         addMessage(data.answer || 'No answer generated.', false, data.citations);
      }
    } catch (err) {
      loadingMsg.remove();
      addMessage('Could not connect to the chatbot server. Please ensure python chatbot/api.py is running on port 8001.', false, [], true);
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
});

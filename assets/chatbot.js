document.addEventListener('DOMContentLoaded', () => {
  const btn = document.createElement('div');
  btn.id = 'chat-widget-button';
  btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="26px" height="26px"><path d="M12 2C6.48 2 2 5.92 2 10.75c0 2.82 1.63 5.33 4.1 6.88L5.5 22l3.74-2.12c.88.24 1.8.37 2.76.37 5.52 0 10-3.92 10-8.75S17.52 2 12 2z"/></svg>`;
  document.body.appendChild(btn);

  const container = document.createElement('div');
  container.id = 'chat-widget-container';
  container.innerHTML = `
    <div class="chat-widget-header">
      <span>🤖 Ask Chipathon</span>
      <button id="chat-widget-close" aria-label="Close">&times;</button>
    </div>
    <div id="chat-widget-history" class="chat-history">
      <div class="message bot-message">Hi! Ask me anything about the OpenROAD EDA flow — placement, routing, timing, CTS, and more.</div>
    </div>
    <div class="chat-widget-input-area">
      <input type="text" id="chat-widget-input" placeholder="e.g. How do I fix setup violations?" autocomplete="off" />
      <button id="chat-widget-send">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="18px" height="18px"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
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

  // Render inline markdown: bold, italic, inline code, links
  function inlineRender(text) {
    return text
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }

  // Render markdown text to HTML
  function renderMarkdown(raw) {
    // Protect fenced code blocks first
    const codeBlocks = [];
    let text = raw.replace(/```(?:\w+)?\n?([\s\S]*?)```/g, (_, code) => {
      const idx = codeBlocks.length;
      codeBlocks.push(`<pre><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;').trim()}</code></pre>`);
      return `\x00CODE${idx}\x00`;
    });

    const lines = text.split('\n');
    const out = [];
    let inUl = false, inOl = false;

    const closeList = () => {
      if (inUl) { out.push('</ul>'); inUl = false; }
      if (inOl) { out.push('</ol>'); inOl = false; }
    };

    for (const line of lines) {
      const ulMatch = line.match(/^[-•*]\s+([\s\S]+)/);
      const olMatch = line.match(/^\d+\.\s+([\s\S]+)/);
      const headingMatch = line.match(/^#{1,3}\s+([\s\S]+)/);

      if (ulMatch) {
        if (!inUl) { closeList(); out.push('<ul>'); inUl = true; }
        out.push(`<li>${inlineRender(ulMatch[1])}</li>`);
      } else if (olMatch) {
        if (!inOl) { closeList(); out.push('<ol>'); inOl = true; }
        out.push(`<li>${inlineRender(olMatch[1])}</li>`);
      } else {
        closeList();
        if (headingMatch) {
          out.push(`<p><strong>${inlineRender(headingMatch[1])}</strong></p>`);
        } else if (line.trim() === '' || line.trim() === '---') {
          out.push('<br>');
        } else if (line.startsWith('\x00CODE')) {
          out.push(line); // will be restored below
        } else {
          out.push(`<p>${inlineRender(line)}</p>`);
        }
      }
    }
    closeList();

    let result = out.join('');
    // Restore code blocks
    codeBlocks.forEach((block, idx) => {
      result = result.replace(`<p>\x00CODE${idx}\x00</p>`, block);
      result = result.replace(`\x00CODE${idx}\x00`, block);
    });
    return result;
  }

  // Parse citation format: "[1] Title — Section | https://url"
  function renderCitations(citations) {
    if (!citations || citations.length === 0) return null;
    const wrapper = document.createElement('div');
    wrapper.className = 'citations-section';
    const label = document.createElement('div');
    label.className = 'citations-label';
    label.textContent = 'Sources';
    wrapper.appendChild(label);

    citations.forEach(citation => {
      const urlMatch = citation.match(/\|\s*(https?:\/\/\S+)\s*$/);
      const numMatch = citation.match(/^\[(\d+)\]/);
      const bodyMatch = citation.match(/^\[\d+\]\s*(.+?)(?:\s*\|\s*https?:\/\/.*)?$/);

      const url = urlMatch ? urlMatch[1] : null;
      const num = numMatch ? numMatch[1] : '?';
      const body = bodyMatch ? bodyMatch[1].trim() : citation;

      const el = document.createElement(url ? 'a' : 'div');
      el.className = 'citation-link';
      if (url) {
        el.href = url;
        el.target = '_blank';
        el.rel = 'noopener';
      }
      el.innerHTML = `<span class="citation-num">${num}</span><span class="citation-body">${body}</span>`;
      wrapper.appendChild(el);
    });

    return wrapper;
  }

  function addMessage(text, isUser, citations = [], isError = false) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    if (isError) div.classList.add('error-message');

    if (isUser) {
      div.textContent = text;
    } else {
      div.innerHTML = renderMarkdown(text);
      const citEl = renderCitations(citations);
      if (citEl) div.appendChild(citEl);
    }

    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
    return div;
  }

  function addLoading() {
    const div = document.createElement('div');
    div.className = 'message bot-message loading-message';
    div.innerHTML = '<span class="loading-dots"><span></span><span></span><span></span></span>';
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
    const loader = addLoading();

    try {
      const response = await fetch('https://rohithsiddi-chipathon-api.hf.space/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });
      const data = await response.json();
      loader.remove();
      if (data.error) {
        addMessage('Server error: ' + data.error, false, [], true);
      } else {
        addMessage(data.answer || 'No answer generated.', false, data.citations || []);
      }
    } catch (err) {
      loader.remove();
      addMessage('Could not reach the chatbot server. It may be starting up — try again in a moment.', false, [], true);
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

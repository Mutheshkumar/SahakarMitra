/**
 * SahakarMitra - Frontend Chat Application
 * Handles message rendering, citation tags, and POST requests to http://localhost:8000/ask
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const chatContainer = document.getElementById('chat-container');
  const messagesList = document.getElementById('messages-list');
  const welcomeScreen = document.getElementById('welcome-screen');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const clearChatBtn = document.getElementById('clear-chat-btn');
  const charCounter = document.getElementById('char-counter');
  const suggestionChips = document.querySelectorAll('.suggestion-chip');

  const API_ENDPOINT = 'http://localhost:8000/ask';
  let isAwaitingResponse = false;

  // Initialize event listeners
  init();

  function init() {
    chatForm.addEventListener('submit', handleFormSubmit);
    userInput.addEventListener('keydown', handleKeyDown);
    userInput.addEventListener('input', handleTextareaInput);
    clearChatBtn.addEventListener('click', handleClearChat);

    // Attach click listeners to suggested question chips
    suggestionChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const query = chip.getAttribute('data-query');
        if (query && !isAwaitingResponse) {
          userInput.value = query;
          handleTextareaInput();
          submitQuestion(query);
        }
      });
    });

    // Auto-focus input on load
    userInput.focus();
  }

  /**
   * Handle Enter key submission (Shift+Enter for newline)
   */
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isAwaitingResponse && userInput.value.trim().length > 0) {
        chatForm.requestSubmit();
      }
    }
  }

  /**
   * Dynamic textarea resizing and character counting
   */
  function handleTextareaInput() {
    userInput.style.height = 'auto';
    const newHeight = Math.min(userInput.scrollHeight, 140);
    userInput.style.height = `${newHeight}px`;

    const length = userInput.value.length;
    charCounter.textContent = `${length}/2000`;
  }

  /**
   * Handle clear chat button
   */
  function handleClearChat() {
    if (isAwaitingResponse) return;
    messagesList.innerHTML = '';
    welcomeScreen.style.display = 'block';
    userInput.value = '';
    userInput.style.height = 'auto';
    charCounter.textContent = '0/2000';
    userInput.focus();
  }

  /**
   * Form submit handler
   */
  function handleFormSubmit(e) {
    e.preventDefault();
    if (isAwaitingResponse) return;

    const question = userInput.value.trim();
    if (!question) return;

    submitQuestion(question);
  }

  /**
   * Send question to the API
   */
  async function submitQuestion(questionText) {
    isAwaitingResponse = true;
    updateSendButtonState(true);

    // Hide welcome banner once chat starts
    if (welcomeScreen.style.display !== 'none') {
      welcomeScreen.style.display = 'none';
    }

    // Reset input field
    userInput.value = '';
    userInput.style.height = 'auto';
    charCounter.textContent = '0/2000';

    // 1. Render User Message (Right-aligned)
    appendUserMessage(questionText);
    scrollToBottom();

    // 2. Render Loading/Typing Indicator (Left-aligned)
    const typingIndicatorId = appendTypingIndicator();
    scrollToBottom();

    try {
      // 3. POST {"question": text} to http://localhost:8000/ask
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: questionText })
      });

      // Remove typing bubble
      removeTypingIndicator(typingIndicatorId);

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Extract answer and cited_section from response
      const answerText = extractAnswer(data);
      const citedSection = extractCitedSection(data);

      // 4. Render AI Answer Bubble with Citation Tag (Left-aligned)
      appendAiMessage(answerText, citedSection);

    } catch (error) {
      console.error('Error fetching answer:', error);
      removeTypingIndicator(typingIndicatorId);

      // Render helpful error message in AI bubble style
      appendErrorMessage(
        `Unable to reach the backend server at <code>${API_ENDPOINT}</code>.<br><br>` +
        `<strong>Troubleshooting:</strong><br>` +
        `• Ensure your backend API is running on port 8000.<br>` +
        `• Check that CORS is enabled on the server for cross-origin requests.<br>` +
        `• Error detail: <em>${escapeHtml(error.message)}</em>`,
        questionText
      );
    } finally {
      isAwaitingResponse = false;
      updateSendButtonState(false);
      scrollToBottom();
      userInput.focus();
    }
  }

  /**
   * Robust extractor for answer content
   */
  function extractAnswer(data) {
    if (!data) return 'No response received from the assistant.';
    if (typeof data === 'string') return data;
    if (data.answer !== undefined && data.answer !== null) return data.answer;
    if (data.response !== undefined && data.response !== null) return data.response;
    if (data.message !== undefined && data.message !== null) return data.message;
    if (data.reply !== undefined && data.reply !== null) return data.reply;
    if (data.text !== undefined && data.text !== null) return data.text;
    return JSON.stringify(data, null, 2);
  }

  /**
   * Robust extractor for cited_section
   */
  function extractCitedSection(data) {
    if (!data || typeof data !== 'object') return null;
    if ('cited_section' in data) return data.cited_section;
    if ('citedSection' in data) return data.citedSection;
    if ('section' in data) return data.section;
    return null;
  }

  /**
   * Append User Bubble (Right Aligned, #0C447C Blue)
   */
  function appendUserMessage(text) {
    const timeStr = getCurrentTime();
    const messageRow = document.createElement('div');
    messageRow.className = 'message-row user';

    messageRow.innerHTML = `
      <div class="message-bubble">
        <div class="message-text">${escapeHtml(text)}</div>
        <div class="message-meta">${timeStr}</div>
      </div>
    `;

    messagesList.appendChild(messageRow);
  }

  /**
   * Append AI Bubble (Left Aligned) with Citation Tag
   * @param {string} answerText - The response body
   * @param {string|null} citedSection - The citation identifier or null
   */
  function appendAiMessage(answerText, citedSection) {
    const timeStr = getCurrentTime();
    const formattedHtml = formatMarkdown(answerText);
    const citationHtml = renderCitationTag(citedSection);

    const messageRow = document.createElement('div');
    messageRow.className = 'message-row ai';

    messageRow.innerHTML = `
      <div class="message-wrapper">
        <div class="ai-avatar" title="SahakarMitra AI">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <div class="message-bubble-group">
          <div class="message-bubble">
            <div class="message-text">${formattedHtml}</div>
            <div class="citation-container">
              ${citationHtml}
            </div>
            <div class="message-meta">${timeStr}</div>
          </div>
        </div>
      </div>
    `;

    messagesList.appendChild(messageRow);
  }

  /**
   * Render citation tag:
   * - Small green "Cited: Section X" if cited_section is present
   * - Neutral "Not covered" tag if cited_section is null
   */
  function renderCitationTag(citedSection) {
    // Check if citedSection is non-null and not empty
    const hasCitation = citedSection !== null &&
                        citedSection !== undefined &&
                        String(citedSection).trim() !== '' &&
                        String(citedSection).trim().toLowerCase() !== 'null';

    if (hasCitation) {
      const rawSection = String(citedSection).trim();
      // If the string already starts with "Section", e.g. "Section 12(a)"
      const displayText = /^section/i.test(rawSection)
        ? `Cited: ${rawSection}`
        : `Cited: Section ${rawSection}`;

      return `
        <span class="citation-tag cited" title="Verified regulatory citation: ${escapeHtml(rawSection)}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <span>${escapeHtml(displayText)}</span>
        </span>
      `;
    } else {
      // Neutral tag for null / not covered
      return `
        <span class="citation-tag neutral" title="Information not specifically covered by statutory sections in database">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>Not covered</span>
        </span>
      `;
    }
  }

  /**
   * Append Error message
   */
  function appendErrorMessage(htmlContent, originalQuestion) {
    const timeStr = getCurrentTime();
    const messageRow = document.createElement('div');
    messageRow.className = 'message-row ai';

    messageRow.innerHTML = `
      <div class="message-wrapper">
        <div class="ai-avatar" style="background-color: #fee2e2; border-color: #fca5a5; color: #b91c1c;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <div class="message-bubble-group">
          <div class="message-bubble error-bubble">
            <div class="error-header">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
              <span>Connection Notice</span>
            </div>
            <div class="message-text">${htmlContent}</div>
            <div class="citation-container">
              <span class="citation-tag neutral">
                <span>Not covered</span>
              </span>
            </div>
            <div class="message-meta">${timeStr}</div>
          </div>
        </div>
      </div>
    `;

    messagesList.appendChild(messageRow);
  }

  /**
   * Typing indicator
   */
  function appendTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingRow = document.createElement('div');
    typingRow.id = id;
    typingRow.className = 'message-row ai';

    typingRow.innerHTML = `
      <div class="message-wrapper">
        <div class="ai-avatar" title="SahakarMitra AI">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <div class="typing-bubble">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;

    messagesList.appendChild(typingRow);
    return id;
  }

  function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  /**
   * UI State Helper
   */
  function updateSendButtonState(loading) {
    sendBtn.disabled = loading;
    if (loading) {
      sendBtn.innerHTML = `
        <span class="btn-text">Thinking...</span>
        <svg class="send-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;">
          <line x1="12" y1="2" x2="12" y2="6"></line>
          <line x1="12" y1="18" x2="12" y2="22"></line>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
          <line x1="2" y1="12" x2="6" y2="12"></line>
          <line x1="18" y1="12" x2="22" y2="12"></line>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
        </svg>
      `;
    } else {
      sendBtn.innerHTML = `
        <span class="btn-text">Send</span>
        <svg class="send-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      `;
    }
  }

  /**
   * Helper: Scroll chat to bottom
   */
  function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  /**
   * Helper: Get formatted current time
   */
  function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * Basic markdown formatter (bold, lists, code, paragraphs)
   */
  function formatMarkdown(text) {
    if (!text) return '';

    // First sanitize
    let escaped = escapeHtml(text);

    // Format code blocks
    escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Format inline code
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Format bold **text** or __text__
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/__(.*?)__/g, '<strong>$1</strong>');

    // Format italic *text* or _text_
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Format unordered lists (bullet points)
    const lines = escaped.split('\n');
    let inList = false;
    let formattedLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (/^[•\-\*]\s+(.*)/.test(line)) {
        if (!inList) {
          formattedLines.push('<ul>');
          inList = true;
        }
        const content = line.replace(/^[•\-\*]\s+/, '');
        formattedLines.push(`<li>${content}</li>`);
      } else if (/^\d+\.\s+(.*)/.test(line)) {
        if (!inList) {
          formattedLines.push('<ol>');
          inList = 'ol';
        }
        const content = line.replace(/^\d+\.\s+/, '');
        formattedLines.push(`<li>${content}</li>`);
      } else {
        if (inList === true) {
          formattedLines.push('</ul>');
          inList = false;
        } else if (inList === 'ol') {
          formattedLines.push('</ol>');
          inList = false;
        }

        if (line.length > 0) {
          formattedLines.push(`<p>${line}</p>`);
        }
      }
    }

    if (inList === true) {
      formattedLines.push('</ul>');
    } else if (inList === 'ol') {
      formattedLines.push('</ol>');
    }

    return formattedLines.join('');
  }

  /**
   * Helper: Escape HTML to prevent XSS
   */
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});

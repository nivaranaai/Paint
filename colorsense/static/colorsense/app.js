// PaintSense Frontend
// Handles chat UI, file uploads, voice input/output, and API calls.

(function () {
  const chat = document.getElementById('chat');
  const swatchesEl = document.getElementById('swatches');
  const messageEl = document.getElementById('message');
  const imagesEl = document.getElementById('images');
  const docsEl = document.getElementById('docs');
  const sendBtn = document.getElementById('send');
  const micBtn = document.getElementById('mic');
  const voiceReplyToggle = document.getElementById('voice-reply');
  const hitlToggle = document.getElementById('hitl-toggle');

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  function appendBubble(role, text) {
    const div = document.createElement('div');
    div.className = `bubble ${role}`;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
  }

  function hexSwatch(hex) {
    const item = document.createElement('div');
    item.className = 'swatch';
    const color = document.createElement('div');
    color.className = 'color';
    color.style.background = hex;
    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = hex;
    item.appendChild(color);
    item.appendChild(label);
    item.addEventListener('click', () => {
      navigator.clipboard?.writeText(hex).catch(() => {});
    });
    return item;
  }

  function renderSwatches(list) {
    swatchesEl.innerHTML = '';
    (list || []).forEach(hex => {
      swatchesEl.appendChild(hexSwatch(hex));
    });
  }

  function speak(text) {
    if (!voiceReplyToggle.checked) return;
    if (!('speechSynthesis' in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  }

  function openReviewWindow(suggestionId) {
    const width = 800;
    const height = 800;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    const reviewWindow = window.open(
      `/review/${suggestionId}/`,
      'paintsense-review',
      `width=${width},height=${height},top=${top},left=${left}`
    );
    
    // Check if window was blocked by popup blocker
    if (!reviewWindow || reviewWindow.closed || typeof reviewWindow.closed === 'undefined') {
      // Fallback to in-page review
      window.location.href = `/review/${suggestionId}/`;
    }
  }

  async function send() {
    const msg = messageEl.value.trim();
    const images = imagesEl.files;
    const docs = docsEl.files;
    
    if (!msg && (!images || images.length === 0) && (!docs || docs.length === 0)) {
      messageEl.focus();
      return;
    }

    // Add user message to chat
    appendBubble('user', msg || '(no text)');
    messageEl.value = '';

    const form = new FormData();
    form.append('message', msg);
    for (const f of images) form.append('images', f);
    for (const f of docs) form.append('docs', f);

    const csrftoken = getCookie('csrftoken');
    const bubble = appendBubble('assistant', 'Thinking…');

    try {
      const resp = await fetch('/api/agent/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
        body: form,
      });

      const data = await resp.json();
      
      if (!data.ok) {
        bubble.textContent = `Error: ${data.error || resp.statusText}`;
        return;
      }

      // If we have a suggestion ID, open the review window
      if (data.suggestion_id) {
        bubble.textContent = 'I have a suggestion for you. Please review it below.';
        openReviewWindow(data.suggestion_id);
      } else {
        // Direct response (no review needed)
        bubble.textContent = data.reply || 'No response';
        renderSwatches(data.swatches || []);
        speak(data.reply || '');
      }
    } catch (err) {
      bubble.textContent = `Network error: ${err}`;
    }
  }

  // Event listeners
  sendBtn.addEventListener('click', send);
  
  messageEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      send();
    }
  });

  // Voice input via Web Speech API
  let recognition = null;
  let listening = false;
  
  try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = () => {
        listening = true;
        micBtn.classList.add('active');
      };
      
      recognition.onend = () => {
        listening = false;
        micBtn.classList.remove('active');
      };
      
      recognition.onresult = (event) => {
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) final += transcript;
        }
        if (final) {
          messageEl.value = (messageEl.value + ' ' + final).trim();
        }
      };
    }
  } catch (e) {
    // ignore errors
  }

  micBtn.addEventListener('click', () => {
    if (!recognition) return;
    if (listening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });
})();

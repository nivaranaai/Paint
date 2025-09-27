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

  function createPaintRecommendation(recommendation) {
    const recDiv = document.createElement('div');
    recDiv.className = 'paint-recommendation';
    recDiv.style.cssText = 'margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;';
    
    if (recommendation.image) {
      const imageDesc = document.createElement('h3');
      imageDesc.textContent = recommendation.image;
      imageDesc.style.cssText = 'margin: 0 0 10px 0; color: #333; font-size: 16px;';
      recDiv.appendChild(imageDesc);
    }
    
    const colorsContainer = document.createElement('div');
    colorsContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 10px;';
    
    recommendation.colors.forEach(color => {
      const colorDiv = document.createElement('div');
      colorDiv.className = 'color-recommendation';
      colorDiv.style.cssText = 'flex: 1; min-width: 200px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: white;';
      
      const colorName = document.createElement('h4');
      colorName.textContent = color.color;
      colorName.style.cssText = 'margin: 0 0 5px 0; font-size: 14px; font-weight: bold;';
      
      const hexSwatch = document.createElement('div');
      hexSwatch.style.cssText = `width: 40px; height: 40px; background: ${color.hex}; border: 1px solid #000; border-radius: 3px; margin: 5px 0; cursor: pointer;`;
      hexSwatch.title = `Click to copy ${color.hex}`;
      hexSwatch.addEventListener('click', () => {
        navigator.clipboard?.writeText(color.hex).catch(() => {});
      });
      
      const finish = document.createElement('p');
      finish.textContent = `Finish: ${color.finish}`;
      finish.style.cssText = 'margin: 5px 0; font-size: 12px; color: #666;';
      
      const rationale = document.createElement('p');
      rationale.textContent = color.rationale;
      rationale.style.cssText = 'margin: 5px 0; font-size: 12px; color: #555; line-height: 1.3;';
      
      colorDiv.appendChild(colorName);
      colorDiv.appendChild(hexSwatch);
      colorDiv.appendChild(finish);
      colorDiv.appendChild(rationale);
      
      colorsContainer.appendChild(colorDiv);
    });
    
    recDiv.appendChild(colorsContainer);
    return recDiv;
  }

  function displayImageWithRecommendations(imageFile, recommendations) {
    const container = document.createElement('div');
    container.className = 'image-with-recommendations';
    container.style.cssText = 'margin: 15px 0; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; background: #fafafa;';
    
    // Display the image
    if (imageFile) {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(imageFile);
      img.style.cssText = 'max-width: 300px; max-height: 300px; border-radius: 5px; margin-bottom: 15px; display: block;';
      container.appendChild(img);
    }  
    // Display recommendations for this image
    if (recommendations && recommendations.length > 0) {
      const recTitle = document.createElement('h3');
      recTitle.textContent = 'Paint Recommendations:';
      recTitle.style.cssText = 'margin: 0 0 10px 0; color: #333;';
      container.appendChild(recTitle);
      
      recommendations.forEach(rec => {
        container.appendChild(createPaintRecommendation(rec));
      });
    }
    
    return container;
  }

  function speak(text) {
    if (!voiceReplyToggle.checked) return;
    if (!('speechSynthesis' in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  }

  function openReviewWindow(review) {
    const width = 800;
    const height = 800;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    const reviewWindow = window.open(
      `/api/agent/`,
      'paintsense-review',
      `width=${width},height=${height},top=${top},left=${left}`
    );
    
    // Check if window was blocked by popup blocker
    if (!reviewWindow || reviewWindow.closed || typeof reviewWindow.closed === 'undefined') {
      // Fallback to in-page review
      window.location.href = `/api/agent/`;
    }
  }

  function confirmSuggetion(description) {
    const confirmModal = document.getElementById('confirmModal');
    const confirmText = document.getElementById('confirmText');
    const yesBtn = document.getElementById('yesBtn');
    const noBtn = document.getElementById('noBtn');

    // Clear old content (important so it doesn’t pile up each time)
    confirmText.innerHTML = "";

    let parsedreply;
    try {
        parsedreply = JSON.parse(description.reply);
    } catch (e) {
        console.error("Invalid JSON in description.reply:", description.reply);
        parsedreply = { reply: [] };
    }

    const files = Array.from(description.images || []);
    files.forEach(function(item, index) {
        // Create and append image
        const img = document.createElement('img');
        img.src = URL.createObjectURL(item);
        img.style.cssText =
          'max-width: 300px; max-height: 300px; border-radius: 5px; margin: 10px 0; display: block;';
        confirmText.appendChild(img);

        // If we have a description, append it too
        if (parsedreply.reply[index] && parsedreply.reply[index].room_description) {
            const desc = document.createElement('p');
            desc.textContent = parsedreply.reply[index].room_description;
            desc.style.cssText = 'margin: 5px 0; font-size: 14px; color: #999;';
            confirmText.appendChild(desc);
        }
    });

    // Show modal
    confirmModal.style.display = 'flex'; // use flex for centering

    // Cleanup previous listeners by cloning buttons
    const newYesBtn = yesBtn.cloneNode(true);
    const newNoBtn = noBtn.cloneNode(true);
    yesBtn.parentNode.replaceChild(newYesBtn, yesBtn);
    noBtn.parentNode.replaceChild(newNoBtn, noBtn);

    // Add fresh listeners
    newYesBtn.addEventListener('click', async () => {
        confirmModal.style.display = 'none';
        await sendConfirmation(true, description);
    });

    newNoBtn.addEventListener('click', async () => {
        confirmModal.style.display = 'none';
        await sendConfirmation(false, description);
    });
}


  async function sendConfirmation(confirmed, description) {
    const form = new FormData();
    form.append('confirm', confirmed);
    form.append('room_description', description.reply);
    form.append('images', description.images);
    //form.append('style_preference', description.style_preference);
    //form.append('images', description.images);
    //form.append('docs', description.docs);
    const csrftoken = getCookie('csrftoken');

    try {
        const resp = await fetch('/api/agent/confirm/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            body: form,
        });

        const data = await resp.json();
        if (data.ok) {
            alert('Confirmation sent successfully.');
            const paint_suggestion = appendBubble('paint_suggestion', '');
            console.log(data.reply);
            console.log(data.reply.reply.recommendations);
            // Display paint recommendations using the new function
            if (data.reply && data.reply.reply.recommendations) {
                data.reply.reply.recommendations.forEach(recommendation => {
                    paint_suggestion.appendChild(createPaintRecommendation(recommendation));//createPaintRecommendation(recommendation)
                });
            }
            
            // Display preparation tips
            if (data.reply && data.reply.reply.preparation_tips) {
                const tipsDiv = document.createElement("div");
                tipsDiv.className = "preparation-tips";
                tipsDiv.style.cssText = 'margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f0f8ff;';
                
                const tipsTitle = document.createElement("h3");
                tipsTitle.textContent = "Preparation Tips";
                tipsTitle.style.cssText = 'margin: 0 0 10px 0; color: #333; font-size: 16px;';
                tipsDiv.appendChild(tipsTitle);
            
                const tipsText = document.createElement("p");
                tipsText.textContent = data.reply.reply.preparation_tips;
                tipsText.style.cssText = 'margin: 0; color: #555; line-height: 1.4;';
                tipsDiv.appendChild(tipsText);
            
                paint_suggestion.appendChild(tipsDiv);
            }
         
            //paint_suggestion.textContent = data.reply;
            //renderSwatches(data.swatches || []);
            //speak(data.reply || '');
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (err) {
        alert(`Network error: ${err}`);
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
    //console.log(msg, images, docs);
    //alert("Hello");
    // Add user message to chat
    appendBubble('user', msg || '(no text)');
    messageEl.value = '';

    const form = new FormData();
    form.append('message', msg);
    for (const f of images) form.append('images', f);
    for (const f of docs) form.append('docs', f);
    //form.append('confirm', false);
    const csrftoken = getCookie('csrftoken');
    const bubble = appendBubble('assistant', 'Thinking…');

    try {
      const resp = await fetch('/api/agent/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
        body: form,
      });

      const data = await resp.json();
      //console.log(data);
      if (!data.ok) {
        bubble.textContent = `Error: ${data.error || resp.statusText}`;
        return;
      }

      // If we have a suggestion ID, open the review window
      if (data.ok) {
        bubble.textContent = 'I have a suggestion for you. Please review it below.';
        //appendBubble('suggestion', data.reply);
        
        // Display uploaded images (without recommendations since /api/agent/ doesn't return them)
        console.log(data.reply);
        const parsedreply = JSON.parse(data.reply);
        console.log(parsedreply.reply);
        const files = Array.from(images);
        files.forEach(function(item, index){
          const suggetionContainer = document.createElement('div');
          const img = document.createElement('img');
          img.src = URL.createObjectURL(item);
          img.style.cssText = 'max-width: 300px; max-height: 300px; border-radius: 5px; margin: 10px 0; display: block;';
          suggetionContainer.appendChild(img);
          console.log(parsedreply.reply[index]);
          if(parsedreply.reply[index] && parsedreply.reply[index].room_description){
            const desc = document.createElement('p');
            desc.textContent = parsedreply.reply[index].room_description;
            desc.style.cssText = 'margin: 5px 0; font-size: 14px; color: #999;';
            suggetionContainer.appendChild(desc);
          }
          bubble.appendChild(suggetionContainer);
        });
        


        data.images = images;
        confirmSuggetion(data);
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

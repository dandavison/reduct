// Background service worker - handles server communication

const SERVER_URL = 'http://localhost:8000';

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'reduceText') {
    handleTextReduction(request.text, request.reductionLevel, request.customPrompt)
      .then(reducedText => sendResponse({reducedText}))
      .catch(error => sendResponse({error: error.message}));
    return true; // Keep message channel open for async response
  } else if (request.action === 'updateProgress') {
    // Forward progress updates to popup if it's open
    chrome.runtime.sendMessage({
      action: 'progressUpdate',
      ...request
    }).catch(() => {
      // Popup might be closed, ignore error
    });
  }
});

async function handleTextReduction(text, reductionLevel = 50, customPrompt = null) {
  try {
    let prompt = customPrompt;
    if (!prompt) {
      prompt = `Reduce this text to approximately ${reductionLevel}% of its original length. Remove filler, redundancy, and verbose explanations while retaining all meaningful semantic content, key points, and factual information. Maintain the original tone and style. Output as clean HTML using these tags: <p>, <ul>, <ol>, <li>, <strong>, <em>, <h3>, <blockquote>, <details>, <summary>. Use <details><summary>Title</summary>content</details> for less important information. IMPORTANT: Output ONLY the HTML without any introduction, wrapper tags, or commentary.`;
    }
    
    const response = await fetch(`${SERVER_URL}/reduce`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        reduction_level: reductionLevel,
        prompt: prompt
      })
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    const data = await response.json();
    return data.reduced_text;
  } catch (error) {
    console.error('Error calling reduction server:', error);
    throw error;
  }
}

// Check server health on extension load
chrome.runtime.onInstalled.addListener(async () => {
  try {
    const response = await fetch(`${SERVER_URL}/health`);
    if (response.ok) {
      console.log('Reduct server is running');
    } else {
      console.warn('Reduct server is not responding');
    }
  } catch (error) {
    console.warn('Reduct server is not running. Start it with: uv run reduct-server');
  }
});

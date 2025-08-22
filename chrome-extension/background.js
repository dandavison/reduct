// Background service worker - handles server communication

const SERVER_URL = 'http://localhost:8000';

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'reduceText') {
    handleTextReduction(request.text, request.reductionLevel)
      .then(reducedText => sendResponse({reducedText}))
      .catch(error => sendResponse({error: error.message}));
    return true; // Keep message channel open for async response
  }
});

async function handleTextReduction(text, reductionLevel = 50) {
  try {
    const response = await fetch(`${SERVER_URL}/reduce`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        reduction_level: reductionLevel,
        prompt: `Reduce this text to approximately ${reductionLevel}% of its original length. Remove filler, redundancy, and verbose explanations while retaining all meaningful semantic content, key points, and factual information. Maintain the original tone and style.`
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

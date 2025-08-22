// Popup script - handles UI interactions

const reduceBtn = document.getElementById('reduceBtn');
const restoreBtn = document.getElementById('restoreBtn');
const reductionSlider = document.getElementById('reductionSlider');
const reductionValue = document.getElementById('reductionValue');
const statusDiv = document.getElementById('status');
const serverStatusDiv = document.getElementById('serverStatus');
const progressBar = document.getElementById('progressBar');
const progressBarFill = document.querySelector('.progress-bar-fill');
const progressBarText = document.querySelector('.progress-bar-text');
const customPromptTextarea = document.getElementById('customPrompt');

// Update reduction value display
reductionSlider.addEventListener('input', (e) => {
  const level = e.target.value;
  reductionValue.textContent = `${level}%`;
});

// Check server status
checkServerStatus();

// Get current page status
chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
  chrome.tabs.sendMessage(tabs[0].id, {action: 'getStatus'}, (response) => {
    if (response && response.isReduced) {
      reduceBtn.disabled = true;
      restoreBtn.disabled = false;
      showStatus('Page is already reduced', 'info');
    }
  });
});

// Listen for progress updates from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'progressUpdate') {
    updateProgress(request.current, request.total, request.message);
  }
});

// Reduce button click
reduceBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  
  reduceBtn.disabled = true;
  statusDiv.style.display = 'none';
  showProgress();
  
  try {
    let customPrompt = customPromptTextarea.value.trim();
    const reductionLevel = parseInt(reductionSlider.value);
    
    // Replace {REDUCT_FACTOR} with actual value if present
    if (customPrompt && customPrompt.includes('{REDUCT_FACTOR}')) {
      customPrompt = customPrompt.replace(/{REDUCT_FACTOR}/g, reductionLevel.toString());
    }
    
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'reduce',
      reductionLevel: reductionLevel,
      customPrompt: customPrompt || null
    });
    
    if (response && response.success) {
      hideProgress();
      showStatus('Page reduced successfully!', 'success');
      restoreBtn.disabled = false;
    } else {
      hideProgress();
      showStatus(response.error || 'Failed to reduce page', 'error');
      reduceBtn.disabled = false;
    }
  } catch (error) {
    console.error('Error:', error);
    hideProgress();
    showStatus('Error: Is the page fully loaded?', 'error');
    reduceBtn.disabled = false;
  }
});

// Restore button click
restoreBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  
  restoreBtn.disabled = true;
  
  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'restore'
    });
    
    if (response && response.success) {
      showStatus('Page restored!', 'success');
      reduceBtn.disabled = false;
    } else {
      showStatus('Failed to restore page', 'error');
      restoreBtn.disabled = false;
    }
  } catch (error) {
    console.error('Error:', error);
    showStatus('Error restoring page', 'error');
    restoreBtn.disabled = false;
  }
});

function showStatus(message, type) {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.style.display = 'block';
  
  if (type !== 'info') {
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 3000);
  }
}

function showProgress() {
  progressBar.style.display = 'block';
  progressBarFill.style.width = '0%';
  progressBarText.textContent = 'Processing...';
}

function hideProgress() {
  progressBar.style.display = 'none';
}

function updateProgress(current, total, message) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  progressBarFill.style.width = `${percentage}%`;
  progressBarText.textContent = message || `Processing... ${percentage}%`;
}

async function checkServerStatus() {
  try {
    const response = await fetch('http://localhost:8000/health');
    if (response.ok) {
      serverStatusDiv.textContent = 'Server: Online ✓';
      serverStatusDiv.className = 'server-status online';
    } else {
      serverStatusDiv.textContent = 'Server: Offline ✗';
      serverStatusDiv.className = 'server-status offline';
      reduceBtn.disabled = true;
    }
  } catch (error) {
    serverStatusDiv.textContent = 'Server: Offline ✗';
    serverStatusDiv.className = 'server-status offline';
    reduceBtn.disabled = true;
    showStatus('Start server with: uv run reduct-server', 'error');
  }
}

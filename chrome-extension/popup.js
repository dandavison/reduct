// Popup script - handles UI interactions

const reduceBtn = document.getElementById('reduceBtn');
const restoreBtn = document.getElementById('restoreBtn');
const reductionSlider = document.getElementById('reductionSlider');
const reductionValue = document.getElementById('reductionValue');
const statusDiv = document.getElementById('status');
const serverStatusDiv = document.getElementById('serverStatus');

// Update reduction value display
reductionSlider.addEventListener('input', (e) => {
  reductionValue.textContent = `${e.target.value}%`;
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

// Reduce button click
reduceBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  
  reduceBtn.disabled = true;
  showStatus('Reducing page content...', 'info');
  
  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'reduce',
      reductionLevel: parseInt(reductionSlider.value)
    });
    
    if (response && response.success) {
      showStatus('Page reduced successfully!', 'success');
      restoreBtn.disabled = false;
    } else {
      showStatus('Failed to reduce page', 'error');
      reduceBtn.disabled = false;
    }
  } catch (error) {
    console.error('Error:', error);
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

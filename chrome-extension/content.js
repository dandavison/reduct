// Content script - runs in the context of web pages

let originalContent = new Map();
let isReduced = false;
let isCancelled = false;

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'reduce') {
    isCancelled = false;
    reducePageContent(request.reductionLevel, request.customPrompt)
      .then(() => sendResponse({success: true}))
      .catch(error => sendResponse({success: false, error: error.message}));
    return true; // Keep message channel open for async response
  } else if (request.action === 'restore') {
    restoreOriginalContent();
    sendResponse({success: true});
  } else if (request.action === 'getStatus') {
    sendResponse({isReduced: isReduced});
  } else if (request.action === 'cancel') {
    isCancelled = true;
    sendResponse({success: true});
  }
});

function getTextNodes(element) {
  const textNodes = [];
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        // Skip empty text nodes and nodes in certain elements
        if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        
        // Skip script, style, code, and pre elements
        const skipTags = ['SCRIPT', 'STYLE', 'CODE', 'PRE', 'NOSCRIPT'];
        if (skipTags.includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
        
        // Skip if any ancestor is code or pre
        let ancestor = parent;
        while (ancestor) {
          if (skipTags.includes(ancestor.tagName)) return NodeFilter.FILTER_REJECT;
          ancestor = ancestor.parentElement;
        }
        
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );
  
  let node;
  while (node = walker.nextNode()) {
    textNodes.push(node);
  }
  return textNodes;
}

function groupTextNodes(textNodes) {
  // Group text nodes by their container element
  const groups = new Map();
  
  textNodes.forEach(node => {
    // Find the nearest block-level container
    let container = node.parentElement;
    while (container && window.getComputedStyle(container).display === 'inline') {
      container = container.parentElement;
    }
    
    if (container) {
      if (!groups.has(container)) {
        groups.set(container, []);
      }
      groups.get(container).push(node);
    }
  });
  
  return groups;
}

function sanitizeHtml(html) {
  // Create a temporary element to parse the HTML
  const temp = document.createElement('div');
  temp.innerHTML = html;
  
  // Define allowed tags
  const allowedTags = ['p', 'ul', 'ol', 'li', 'details', 'summary', 
                       'strong', 'em', 'b', 'i', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                       'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
                       'mark', 'del', 'ins', 'sub', 'sup', 'hr', 'abbr'];
  
  // Remove any script tags and event handlers
  const scripts = temp.querySelectorAll('script');
  scripts.forEach(script => script.remove());
  
  // Walk through all elements and remove disallowed ones
  const walker = document.createTreeWalker(
    temp,
    NodeFilter.SHOW_ELEMENT,
    {
      acceptNode: function(node) {
        // Remove any element not in allowed list
        if (!allowedTags.includes(node.tagName.toLowerCase())) {
          return NodeFilter.FILTER_REJECT;
        }
        // Remove any attributes (including event handlers)
        while (node.attributes.length > 0) {
          node.removeAttribute(node.attributes[0].name);
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );
  
  const nodesToRemove = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!allowedTags.includes(node.tagName.toLowerCase())) {
      nodesToRemove.push(node);
    }
  }
  
  // Remove disallowed nodes
  nodesToRemove.forEach(node => {
    // Move children up to parent before removing
    while (node.firstChild) {
      node.parentNode.insertBefore(node.firstChild, node);
    }
    node.remove();
  });
  
  return temp.innerHTML;
}

async function reducePageContent(reductionLevel = 50, customPrompt = null) {
  if (isReduced) {
    console.log('Page is already reduced');
    return;
  }
  
  // Show loading indicator
  showLoadingIndicator();
  
  try {
    // Get all text nodes
    const textNodes = getTextNodes(document.body);
    const groups = groupTextNodes(textNodes);
    
    // Send progress update
    await chrome.runtime.sendMessage({
      action: 'updateProgress',
      message: `Processing ${groups.size} text blocks...`,
      current: 0,
      total: groups.size
    });
    
    let processed = 0;
    
    // Process each group of text nodes
    for (const [container, nodes] of groups) {
      // Check if cancelled
      if (isCancelled) {
        console.log('Reduction cancelled by user');
        break;
      }
      
      // Combine text from all nodes in this container
      const originalTexts = nodes.map(node => ({
        node: node,
        text: node.nodeValue
      }));
      
      const combinedText = originalTexts.map(item => item.text).join(' ');
      
      // Skip very short text
      if (combinedText.trim().split(/\s+/).length < 10) continue;
      
      // Store original content
      originalTexts.forEach(item => {
        originalContent.set(item.node, item.text);
      });
      
      // Send to background script for reduction
      const response = await chrome.runtime.sendMessage({
        action: 'reduceText',
        text: combinedText,
        reductionLevel: reductionLevel,
        customPrompt: customPrompt
      });
      
      if (response.error) {
        console.error('Error reducing text:', response.error);
        continue;
      }
      
      if (response.reducedText) {
        // Sanitize and insert HTML content
        const sanitizedHtml = sanitizeHtml(response.reducedText);
        
        // Create wrapper for formatted content
        const wrapper = document.createElement('div');
        wrapper.innerHTML = sanitizedHtml;
        wrapper.className = 'reduct-formatted';
        
        // Clear original text nodes
        nodes.forEach(node => {
          node.nodeValue = '';
        });
        
        // Insert the formatted HTML
        container.appendChild(wrapper);
      }
      
      // Update progress
      processed++;
      await chrome.runtime.sendMessage({
        action: 'updateProgress',
        message: `Processing text blocks...`,
        current: processed,
        total: groups.size
      });
    }
    
    if (!isCancelled) {
      isReduced = true;
      addReducedIndicator();
    }
  } catch (error) {
    console.error('Error in reducePageContent:', error);
    alert('Error reducing page content. Make sure the reduct server is running.');
  } finally {
    hideLoadingIndicator();
    isCancelled = false;
  }
}

function restoreOriginalContent() {
  if (!isReduced) return;
  
  // First, remove any formatted content we added
  document.querySelectorAll('.reduct-formatted').forEach(element => {
    const parent = element.parentElement;
    if (parent) {
      parent.removeChild(element);
    }
  });
  
  // Then restore original text nodes
  originalContent.forEach((originalText, node) => {
    if (node.parentElement) { // Check if node is still in DOM
      node.nodeValue = originalText;
    }
  });
  
  originalContent.clear();
  isReduced = false;
  removeReducedIndicator();
}

function showLoadingIndicator() {
  const indicator = document.createElement('div');
  indicator.id = 'reduct-loading';
  indicator.innerHTML = `
    <div class="reduct-loading-content">
      <div class="reduct-loading-text">Reducing content...</div>
      <div class="reduct-loading-progress"></div>
      <button class="reduct-cancel-btn">Cancel</button>
    </div>
  `;
  document.body.appendChild(indicator);
  
  // Add cancel button handler
  const cancelBtn = indicator.querySelector('.reduct-cancel-btn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      isCancelled = true;
      hideLoadingIndicator();
      // Restore any partial changes
      restoreOriginalContent();
    });
  }
}

function hideLoadingIndicator() {
  const indicator = document.getElementById('reduct-loading');
  if (indicator) indicator.remove();
}

function addReducedIndicator() {
  const indicator = document.createElement('div');
  indicator.id = 'reduct-indicator';
  indicator.textContent = '📝 Reduced';
  indicator.title = 'This page has been reduced. Click the extension to restore.';
  document.body.appendChild(indicator);
}

function removeReducedIndicator() {
  const indicator = document.getElementById('reduct-indicator');
  if (indicator) indicator.remove();
}

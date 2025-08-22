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

function convertToHtml(text) {
  // Check for details blocks first
  const detailsPattern = /\[Details:\s*([^\]]+)\]([\s\S]*?)\[\/Details\]/gi;
  if (detailsPattern.test(text)) {
    text = text.replace(detailsPattern, (match, summary, content) => {
      const processedContent = convertToHtml(content.trim());
      return `<details><summary>${summary.trim()}</summary>${processedContent}</details>`;
    });
  }
  
  // Return original text if no formatting detected
  const hasListMarkers = /^[\*\-•]\s+/m.test(text) || /^\d+\.\s+/m.test(text);
  const hasLineBreaks = text.includes('\n');
  const hasDetails = text.includes('<details>');
  
  if (!hasListMarkers && !hasLineBreaks && !hasDetails) {
    return text;
  }
  
  // Split text into lines for processing
  const lines = text.split('\n');
  const htmlParts = [];
  let currentList = null;
  let currentListItems = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (!line) {
      // Empty line - close current list if any
      if (currentList) {
        htmlParts.push(`<${currentList}>${currentListItems.join('')}</${currentList}>`);
        currentList = null;
        currentListItems = [];
      }
      // Add paragraph break if not at start/end
      if (i > 0 && i < lines.length - 1) {
        htmlParts.push('</p><p>');
      }
      continue;
    }
    
    // Check for bullet list item
    const bulletMatch = line.match(/^[\*\-•]\s+(.+)$/);
    if (bulletMatch) {
      if (currentList !== 'ul') {
        if (currentList) {
          htmlParts.push(`<${currentList}>${currentListItems.join('')}</${currentList}>`);
          currentListItems = [];
        }
        currentList = 'ul';
      }
      currentListItems.push(`<li>${bulletMatch[1]}</li>`);
      continue;
    }
    
    // Check for numbered list item
    const numberMatch = line.match(/^\d+\.\s+(.+)$/);
    if (numberMatch) {
      if (currentList !== 'ol') {
        if (currentList) {
          htmlParts.push(`<${currentList}>${currentListItems.join('')}</${currentList}>`);
          currentListItems = [];
        }
        currentList = 'ol';
      }
      currentListItems.push(`<li>${numberMatch[1]}</li>`);
      continue;
    }
    
    // Regular text line
    if (currentList) {
      htmlParts.push(`<${currentList}>${currentListItems.join('')}</${currentList}>`);
      currentList = null;
      currentListItems = [];
    }
    htmlParts.push(line);
  }
  
  // Close any remaining list
  if (currentList) {
    htmlParts.push(`<${currentList}>${currentListItems.join('')}</${currentList}>`);
  }
  
  // Join and wrap in paragraphs
  let html = htmlParts.join('\n');
  
  // Only wrap in <p> tags if there's actual paragraph content
  if (html && !html.startsWith('<ul>') && !html.startsWith('<ol>')) {
    html = '<p>' + html + '</p>';
  }
  
  // Clean up paragraph tags
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<\/p>\s*<p>/g, '</p><p>');
  
  return html;
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
        // Check if the reduced text contains formatting that needs HTML
        const formattedHtml = convertToHtml(response.reducedText);
        
        if (formattedHtml !== response.reducedText) {
          // Insert HTML content
          const wrapper = document.createElement('div');
          wrapper.innerHTML = formattedHtml;
          wrapper.className = 'reduct-formatted';
          
          // Replace the container's content with the formatted HTML
          container.innerHTML = '';
          container.appendChild(wrapper);
        } else {
          // Plain text - use the original approach
          nodes[0].nodeValue = response.reducedText;
          for (let i = 1; i < nodes.length; i++) {
            nodes[i].nodeValue = '';
          }
        }
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

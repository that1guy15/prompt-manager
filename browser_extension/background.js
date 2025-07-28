// Background service worker for Prompt Manager extension
// Handles extension lifecycle events and manages storage

chrome.runtime.onInstalled.addListener((details) => {
  console.log('Prompt Manager extension installed:', details.reason);
  
  // Initialize default settings
  chrome.storage.sync.set({
    promptSuggestionsEnabled: true,
    autoCompleteEnabled: true,
    serverUrl: 'http://localhost:5000'
  });
  
  // Create context menu structure
  chrome.contextMenus.create({
    id: 'prompt-manager-main',
    title: 'Prompt Manager',
    contexts: ['editable', 'selection', 'page']
  });
  
  chrome.contextMenus.create({
    id: 'prompt-suggest',
    parentId: 'prompt-manager-main',
    title: 'Get Smart Suggestions',
    contexts: ['editable', 'selection']
  });
  
  chrome.contextMenus.create({
    id: 'prompt-save',
    parentId: 'prompt-manager-main',
    title: 'Save as Prompt Template',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'prompt-library',
    parentId: 'prompt-manager-main',
    title: 'Browse Prompt Library',
    contexts: ['page']
  });
  
  chrome.contextMenus.create({
    id: 'recent-prompts',
    parentId: 'prompt-manager-main',
    title: 'Recent Prompts',
    contexts: ['editable']
  });
  
  chrome.contextMenus.create({
    id: 'separator1',
    parentId: 'prompt-manager-main',
    type: 'separator',
    contexts: ['page']
  });
  
  chrome.contextMenus.create({
    id: 'prompt-settings',
    parentId: 'prompt-manager-main',
    title: 'Settings & Configuration',
    contexts: ['page']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case 'prompt-suggest':
      chrome.tabs.sendMessage(tab.id, {
        action: 'showPromptSuggestions',
        selectedText: info.selectionText
      });
      break;
      
    case 'prompt-save':
      chrome.tabs.sendMessage(tab.id, {
        action: 'saveAsPromptTemplate',
        selectedText: info.selectionText
      });
      break;
      
    case 'prompt-library':
      chrome.action.openPopup();
      break;
      
    case 'recent-prompts':
      chrome.tabs.sendMessage(tab.id, {
        action: 'showRecentPrompts'
      });
      break;
      
    case 'prompt-settings':
      chrome.runtime.openOptionsPage();
      break;
  }
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'getPromptSuggestions':
      fetchPromptSuggestions(request.context)
        .then(suggestions => sendResponse({ suggestions }))
        .catch(error => sendResponse({ error: error.message }));
      return true;
      
    case 'savePromptTemplate':
      savePromptTemplate(request.template)
        .then(result => sendResponse({ success: true, result }))
        .catch(error => sendResponse({ error: error.message }));
      return true;
      
    case 'getRecentPrompts':
      getRecentPrompts()
        .then(prompts => sendResponse({ prompts }))
        .catch(error => sendResponse({ error: error.message }));
      return true;
      
    case 'usePrompt':
      recordPromptUsage(request.promptId)
        .then(() => sendResponse({ success: true }))
        .catch(error => sendResponse({ error: error.message }));
      return true;
  }
});

// Fetch prompt suggestions from local server
async function fetchPromptSuggestions(context) {
  try {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:5000';
    
    const response = await fetch(`${serverUrl}/suggest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ context })
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch prompt suggestions:', error);
    throw error;
  }
}

// Save prompt template to local server
async function savePromptTemplate(template) {
  try {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:5000';
    
    const response = await fetch(`${serverUrl}/api/prompts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: template.title || 'Untitled Prompt',
        content: template.content,
        category: template.category || 'user-generated',
        tags: template.tags || []
      })
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to save prompt template:', error);
    throw error;
  }
}

// Get recent prompts from local server
async function getRecentPrompts() {
  try {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:5000';
    
    const response = await fetch(`${serverUrl}/api/prompts?limit=10&sort=recent`);
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch recent prompts:', error);
    throw error;
  }
}

// Record prompt usage
async function recordPromptUsage(promptId) {
  try {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:5000';
    
    const response = await fetch(`${serverUrl}/api/prompts/${promptId}/use`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to record prompt usage:', error);
    throw error;
  }
}
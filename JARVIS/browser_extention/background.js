const JARVIS_ENDPOINT = 'http://localhost:8989/';

async function sendUrlToJarvis(url) {
  if (!url || !url.startsWith('http')) {
    // Don't send local file URLs or empty URLs
    return;
  }
  try {
    await fetch(JARVIS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
      },
      body: url,
    });
  } catch (error) {
    // This is expected if the JARVIS app isn't running.
    // console.log('JARVIS is not listening.');
  }
}

// Fired when the active tab in a window changes.
chrome.tabs.onActivated.addListener(activeInfo => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (tab && tab.url) {
      sendUrlToJarvis(tab.url);
    }
  });
});

// Fired when a tab is updated (e.g., URL changes).
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url && tab.active) {
    sendUrlToJarvis(changeInfo.url);
  }
});
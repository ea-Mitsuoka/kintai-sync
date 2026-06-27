# GAS Code for Spreadsheet to Cloud Run Sync Webhook

/**
 * Triggered automatically on spreadsheet edits.
 * Calls the Cloud Run /sync endpoint to update Firestore.
 */
function onEdit(e) {
  syncToCloudRun();
}

/**
 * Manual sync function (can be added to a custom menu).
 */
function syncToCloudRun() {
  const url = "YOUR_CLOUD_RUN_SYNC_URL/sync"; // Replace with actual URL from Terraform output
  const options = {
    "method": "post",
    "contentType": "application/json",
    "muteHttpExceptions": true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    Logger.log("Sync Response: " + response.getContentText());
  } catch (err) {
    Logger.log("Error during sync: " + err.toString());
  }
}

/**
 * Create a custom menu to trigger manual sync.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Kintai Sync')
      .addItem('今すぐFirestoreに同期', 'syncToCloudRun')
      .addToUi();
}

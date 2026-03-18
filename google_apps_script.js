// ─────────────────────────────────────────────────────────────────
// CostBid Solutions — Google Apps Script Web App
// Paste this entire file into script.google.com → New Project
// Then: Deploy → New Deployment → Web App → Anyone → Deploy
// Copy the Web App URL → paste into Railway as SHEETS_WEBHOOK
// ─────────────────────────────────────────────────────────────────

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // Add header row if sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Timestamp", "First Name", "Last Name",
        "Company", "Email", "Service", "Project Brief", "Status"
      ]);
      // Style the header
      var header = sheet.getRange(1, 1, 1, 8);
      header.setBackground("#0A1628");
      header.setFontColor("#C9A84C");
      header.setFontWeight("bold");
      sheet.setFrozenRows(1);
    }

    // Parse incoming JSON
    var data = JSON.parse(e.postData.contents);

    // Append new row
    sheet.appendRow([
      data.timestamp   || new Date().toISOString(),
      data.first_name  || "",
      data.last_name   || "",
      data.company     || "",
      data.email       || "",
      data.service     || "",
      data.brief       || "",
      "New"
    ]);

    // Auto-resize columns for readability
    sheet.autoResizeColumns(1, 8);

    return ContentService
      .createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Test function — run this manually to verify sheet access
function testSheet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  Logger.log("Sheet name: " + sheet.getName());
  Logger.log("Sheet URL: " + SpreadsheetApp.getActiveSpreadsheet().getUrl());
}

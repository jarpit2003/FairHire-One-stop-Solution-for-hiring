/**
 * FairHire AI — Google Form Webhook
 * 
 * HOW TO INSTALL:
 * 1. Open your Google Form
 * 2. Click the 3-dot menu → Script editor
 * 3. Paste this entire file, replacing any existing code
 * 4. Set FAIRHIRE_INTAKE_URL and JOB_ID below
 * 5. Click Save, then Run → onFormSubmit once (to grant permissions)
 * 6. Click Triggers (clock icon) → Add Trigger:
 *      Function: onFormSubmit
 *      Event source: From form
 *      Event type: On form submit
 * 7. Done — every submission now auto-posts to FairHire
 */

// ── CONFIG — fill these in ────────────────────────────────────────────────────
var FAIRHIRE_INTAKE_URL = "https://YOUR_BACKEND_URL/api/v1/intake/submit";
var JOB_ID = "PASTE_JOB_UUID_HERE";  // copy from FairHire Jobs page URL or DB
// Test platform webhook URL format (for HackerRank/Mettl etc.):
// https://YOUR_BACKEND_URL/api/v1/applications/webhook/test-score?app_id=APPLICATION_UUID
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Triggered on every form submission.
 * Maps form field titles to the FairHire intake schema.
 * Field name matching is case-insensitive and partial — so "Email Address"
 * matches the "email" field, "Full Name" matches "full_name", etc.
 */
function onFormSubmit(e) {
  try {
    var response = e.response;
    var itemResponses = response.getItemResponses();

    // Build a normalised map: lowercase_title → answer
    var fields = {};
    for (var i = 0; i < itemResponses.length; i++) {
      var item = itemResponses[i];
      var title = item.getItem().getTitle().toLowerCase().trim();
      var answer = item.getResponse();
      fields[title] = answer;
    }

    // Extract fields by fuzzy title matching
    var payload = {
      job_id: JOB_ID,
      full_name: findField(fields, ["full name", "name", "your name", "candidate name"]),
      email: findField(fields, ["email", "email address", "your email", "e-mail"]),
      phone: findField(fields, ["phone", "mobile", "contact number", "phone number", "mobile number"]),
      linkedin_url: findField(fields, ["linkedin", "linkedin url", "linkedin profile", "linkedin link"]),
      resume_text: findField(fields, ["resume", "resume text", "paste resume", "cv", "paste your resume", "resume content", "cover letter and resume"]),
      cover_note: findField(fields, ["cover note", "cover letter", "why this role", "about yourself", "introduction", "message"]),
    };

    // Validate required fields
    if (!payload.email) {
      Logger.log("FairHire webhook: no email found in form response. Fields: " + JSON.stringify(Object.keys(fields)));
      return;
    }
    if (!payload.full_name) {
      // Fall back to email prefix as name
      payload.full_name = payload.email.split("@")[0];
    }

    // POST to FairHire
    var options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
    };

    var response = UrlFetchApp.fetch(FAIRHIRE_INTAKE_URL, options);
    var code = response.getResponseCode();
    var body = response.getContentText();

    if (code === 201) {
      var data = JSON.parse(body);
      Logger.log("FairHire: application created. candidate_id=" + data.candidate_id + 
                 " score=" + data.resume_score + " email_sent=" + data.email_sent);
    } else {
      Logger.log("FairHire webhook error " + code + ": " + body);
    }

  } catch (err) {
    Logger.log("FairHire webhook exception: " + err.toString());
  }
}

/**
 * Find a value from the fields map by trying multiple possible titles.
 * Returns the first match, or null if none found.
 */
function findField(fields, candidates) {
  for (var i = 0; i < candidates.length; i++) {
    var key = candidates[i].toLowerCase();
    // Exact match
    if (fields[key] !== undefined && fields[key] !== "") {
      return fields[key];
    }
    // Partial match — field title contains the candidate keyword
    for (var fieldKey in fields) {
      if (fieldKey.indexOf(key) !== -1 && fields[fieldKey] !== "") {
        return fields[fieldKey];
      }
    }
  }
  return null;
}

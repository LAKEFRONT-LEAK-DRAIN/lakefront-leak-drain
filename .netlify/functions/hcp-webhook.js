/**
 * Lakefront Leak & Drain - Housecall Pro Webhook Bridge
 * Purpose: Captures Estimates, Jobs, and Payments from HCP to trigger 
 * Operations and Marketing automations.
 */

exports.handler = async (event, context) => {
  // 1. Only allow POST requests from Housecall Pro
  if (event.httpMethod !== "POST") {
    return { 
      statusCode: 405, 
      body: JSON.stringify({ error: "Method Not Allowed - Use POST" }) 
    };
  }

  try {
    const payload = JSON.parse(event.body);
    
    // 2. Log the event for Gemini to audit via Netlify Logs
    console.log("--- NEW HCP EVENT RECEIVED ---");
    console.log("Event Type:", payload.type);
    console.log("Customer:", payload.customer?.first_name, payload.customer?.last_name);
    console.log("Object ID:", payload.id);
    console.log("Full Payload:", JSON.stringify(payload, null, 2));

    /**
     * 3. LOGIC HUB:
     * When Steve signs the $17,143 estimate or pays the 50% deposit,
     * this section will eventually trigger your GitHub Actions 
     * to update the Master Ledger in Google Drive.
     */
    if (payload.type === "estimate.status_changed" && payload.status === "accepted") {
      console.log("ACTION REQUIRED: Steve accepted the Brevier estimate. Triggering deposit invoice.");
    }

    // 4. Return success to Housecall Pro so it doesn't retry
    return {
      statusCode: 200,
      body: JSON.stringify({ 
        status: "success", 
        message: "Lakefront Ops has logged the event." 
      }),
    };

  } catch (error) {
    console.error("Webhook Error:", error);
    return { 
      statusCode: 400, 
      body: JSON.stringify({ error: "Invalid JSON payload" }) 
    };
  }
};
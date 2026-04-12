'use strict';

const SEND_COOLDOWN_SEC = 45;
const recentSendByKey = new Map();

function normalizePhone(input) {
  const digits = String(input || '').replace(/\D/g, '');
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return null;
}

exports.handler = async (event) => {
  const CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: CORS, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { ...CORS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Method not allowed' }),
    };
  }

  try {
    const body = JSON.parse(event.body || '{}');
    const normalizedPhone = normalizePhone(body.phone);
    if (!normalizedPhone) {
      return {
        statusCode: 400,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Enter a valid US phone number.' }),
      };
    }

    const accountSid = process.env.TWILIO_ACCOUNT_SID;
    const authToken = process.env.TWILIO_AUTH_TOKEN;
    const verifySid = process.env.TWILIO_VERIFY_SERVICE_SID;
    if (!accountSid || !authToken || !verifySid) {
      return {
        statusCode: 500,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: 'OTP is not configured yet. Missing Twilio environment variables.',
        }),
      };
    }

    const ip = event.headers['x-forwarded-for'] || event.headers['client-ip'] || 'unknown';
    const key = `${normalizedPhone}:${String(ip).split(',')[0].trim()}`;
    const now = Date.now();
    const lastSentAt = recentSendByKey.get(key) || 0;
    const msSinceLast = now - lastSentAt;
    if (msSinceLast < SEND_COOLDOWN_SEC * 1000) {
      const retryAfterSec = Math.ceil((SEND_COOLDOWN_SEC * 1000 - msSinceLast) / 1000);
      return {
        statusCode: 429,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: `Please wait ${retryAfterSec}s before requesting another code.`,
          retryAfterSec,
        }),
      };
    }

    const endpoint = `https://verify.twilio.com/v2/Services/${verifySid}/Verifications`;
    const auth = Buffer.from(`${accountSid}:${authToken}`).toString('base64');
    const payload = new URLSearchParams({ To: normalizedPhone, Channel: 'sms' });

    const twilioRes = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: payload,
    });

    const twilioData = await twilioRes.json();
    if (!twilioRes.ok) {
      return {
        statusCode: 502,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: twilioData.message || 'Failed to send verification code.' }),
      };
    }

    recentSendByKey.set(key, now);

    return {
      statusCode: 200,
      headers: { ...CORS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ sent: true, phone: normalizedPhone, retryAfterSec: SEND_COOLDOWN_SEC }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers: { ...CORS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: err.message || 'Unexpected error.' }),
    };
  }
};

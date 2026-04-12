'use strict';

const crypto = require('crypto');

function normalizePhone(input) {
  const digits = String(input || '').replace(/\D/g, '');
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return null;
}

function b64url(input) {
  return Buffer.from(input).toString('base64url');
}

function signSession(payload, secret) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const encodedHeader = b64url(JSON.stringify(header));
  const encodedPayload = b64url(JSON.stringify(payload));
  const unsigned = `${encodedHeader}.${encodedPayload}`;
  const signature = crypto.createHmac('sha256', secret).update(unsigned).digest('base64url');
  return `${unsigned}.${signature}`;
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
    const code = String(body.code || '').trim();

    if (!normalizedPhone || !/^\d{4,8}$/.test(code)) {
      return {
        statusCode: 400,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Phone and valid verification code are required.' }),
      };
    }

    const accountSid = process.env.TWILIO_ACCOUNT_SID;
    const authToken = process.env.TWILIO_AUTH_TOKEN;
    const verifySid = process.env.TWILIO_VERIFY_SERVICE_SID;
    const sessionSecret = process.env.OTP_SESSION_SECRET;

    if (!accountSid || !authToken || !verifySid || !sessionSecret) {
      return {
        statusCode: 500,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: 'OTP verify is not configured yet. Missing Twilio or OTP session environment variables.',
        }),
      };
    }

    const endpoint = `https://verify.twilio.com/v2/Services/${verifySid}/VerificationCheck`;
    const auth = Buffer.from(`${accountSid}:${authToken}`).toString('base64');
    const payload = new URLSearchParams({ To: normalizedPhone, Code: code });

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
        body: JSON.stringify({ error: twilioData.message || 'Verification failed.' }),
      };
    }

    if (twilioData.status !== 'approved') {
      return {
        statusCode: 401,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Incorrect code. Please try again.' }),
      };
    }

    const expiresInSec = 60 * 60 * 12;
    const now = Math.floor(Date.now() / 1000);
    const tokenPayload = {
      phone: normalizedPhone.replace(/\D/g, ''),
      iat: now,
      exp: now + expiresInSec,
    };
    const sessionToken = signSession(tokenPayload, sessionSecret);

    return {
      statusCode: 200,
      headers: { ...CORS, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        verified: true,
        phone: normalizedPhone,
        sessionToken,
        expiresInSec,
      }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers: { ...CORS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: err.message || 'Unexpected error.' }),
    };
  }
};

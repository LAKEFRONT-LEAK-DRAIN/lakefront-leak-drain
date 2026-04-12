'use strict';

const crypto = require('crypto');

function normalizePhoneDigits(input) {
  const digits = String(input || '').replace(/\D/g, '');
  if (digits.length === 10) return `1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return digits;
  return null;
}

function verifySessionToken(authHeader, secret) {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing authorization token.');
  }
  const token = authHeader.slice('Bearer '.length).trim();
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('Invalid authorization token.');

  const [encodedHeader, encodedPayload, signature] = parts;
  const unsigned = `${encodedHeader}.${encodedPayload}`;
  const expected = crypto.createHmac('sha256', secret).update(unsigned).digest('base64url');
  if (signature !== expected) throw new Error('Invalid authorization token.');

  const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8'));
  if (!payload.exp || Math.floor(Date.now() / 1000) > payload.exp) {
    throw new Error('Session expired. Please verify again.');
  }
  return payload;
}

exports.handler = async (event) => {
  const CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: CORS, body: '' };
  }

  try {
    const sessionSecret = process.env.OTP_SESSION_SECRET;
    if (!sessionSecret) {
      return {
        statusCode: 500,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Session auth is not configured. Missing OTP_SESSION_SECRET.' }),
      };
    }

    let session;
    try {
      session = verifySessionToken(event.headers.authorization || event.headers.Authorization, sessionSecret);
    } catch (tokenErr) {
      return {
        statusCode: 401,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: tokenErr.message }),
      };
    }

    const { phone } = event.queryStringParameters || {};
    if (!phone) {
      return {
        statusCode: 400,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'phone is required' }),
      };
    }

    const token = process.env.HCP_API_TOKEN;
    const hHeaders = {
      Authorization: `Token ${token}`,
      'Content-Type': 'application/json',
    };
    const base = 'https://api.housecallpro.com';
    const clean = normalizePhoneDigits(phone);
    const sessionPhone = normalizePhoneDigits(session.phone);

    if (!clean || !sessionPhone) {
      return {
        statusCode: 400,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Phone must be a valid US number.' }),
      };
    }

    if (sessionPhone !== clean) {
      return {
        statusCode: 401,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Verified phone does not match request phone.' }),
      };
    }

    // Search customer by phone
    const searchRes = await fetch(
      `${base}/customers?q=${encodeURIComponent(phone)}&page=1&page_size=10`,
      { headers: hHeaders }
    );
    if (!searchRes.ok) {
      return {
        statusCode: 502,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Customer search failed' }),
      };
    }
    const { customers = [] } = await searchRes.json();

    // Find customer whose phone matches exactly (same normalization as token check)
    let customer = null;
    for (const c of customers) {
      const phones = [c.mobile_number, c.home_number, c.work_number]
        .filter(Boolean)
        .map((p) => normalizePhoneDigits(p))
        .filter(Boolean);
      if (phones.includes(clean)) {
        customer = c;
        break;
      }
    }

    if (!customer) {
      return {
        statusCode: 200,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ found: false }),
      };
    }

    // Fetch jobs for this customer (most recent first)
    const jobsRes = await fetch(
      `${base}/jobs?customer_id=${customer.id}&page=1&page_size=25&sort_direction=desc`,
      { headers: hHeaders }
    );
    if (!jobsRes.ok) {
      return {
        statusCode: 502,
        headers: { ...CORS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Jobs fetch failed' }),
      };
    }
    const { jobs: rawJobs = [] } = await jobsRes.json();

    const jobs = rawJobs.map((job) => {
      const schedule = job.schedule || {};
      const addr = job.address || {};
      const addrStr = [addr.street, addr.city, addr.state].filter(Boolean).join(', ');
      const services = (job.line_items || []).map((li) => li.name).filter(Boolean);
      const assigned = (job.assigned_employees || []).map((e) => e.name).filter(Boolean);
      const totalCents =
        job.invoice && job.invoice.total_amount != null
          ? job.invoice.total_amount
          : job.total_amount != null
          ? job.total_amount
          : null;

      return {
        id: job.id,
        workStatus: job.work_status || 'unknown',
        invoiceNumber: job.invoice_number || null,
        scheduledStart: schedule.scheduled_start || job.scheduled_start || null,
        scheduledEnd: schedule.scheduled_end || job.scheduled_end || null,
        address: addrStr,
        services,
        totalCents,
        assignedEmployee: assigned[0] || null,
      };
    });

    return {
      statusCode: 200,
      headers: { ...CORS, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        found: true,
        customerName: `${customer.first_name || ''} ${customer.last_name || ''}`.trim(),
        customerId: customer.id,
        jobs,
      }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: err.message }),
    };
  }
};

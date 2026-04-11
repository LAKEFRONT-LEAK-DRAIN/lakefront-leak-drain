const API_BASE = 'https://api.housecallpro.com';

function json(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
    },
    body: JSON.stringify(body),
  };
}

function normalizeDigits(value) {
  return (value || '').replace(/\D/g, '');
}

function scoreCustomer(customer, phone, email) {
  let score = 0;

  const inputEmail = (email || '').trim().toLowerCase();
  const customerEmail = (customer.email || '').trim().toLowerCase();
  if (inputEmail && customerEmail) {
    if (customerEmail === inputEmail) {
      score += 100;
    } else if (customerEmail.includes(inputEmail)) {
      score += 25;
    }
  }

  const inputPhone = normalizeDigits(phone);
  const phones = [
    customer.mobile_number,
    customer.home_number,
    customer.work_number,
  ].map(normalizeDigits);

  if (inputPhone) {
    for (const candidate of phones) {
      if (!candidate) continue;
      if (candidate === inputPhone) {
        score += 90;
      } else if (candidate.endsWith(inputPhone) || inputPhone.endsWith(candidate)) {
        score += 20;
      }
    }
  }

  return score;
}

function pickBestCustomer(customers, phone, email) {
  const ranked = customers
    .map((customer) => ({ customer, score: scoreCustomer(customer, phone, email) }))
    .sort((a, b) => b.score - a.score);

  return ranked[0]?.customer || null;
}

exports.handler = async function handler(event) {
  const token = process.env.HCP_API_TOKEN;
  if (!token) {
    return json(500, { error: 'Missing HCP_API_TOKEN environment variable.' });
  }

  const phone = (event.queryStringParameters?.phone || '').trim();
  const email = (event.queryStringParameters?.email || '').trim();

  if (!phone && !email) {
    return json(400, { error: 'Provide phone or email.' });
  }

  const q = email || phone;
  const qs = new URLSearchParams({ q, page_size: '25', sort_direction: 'desc' });

  try {
    const response = await fetch(`${API_BASE}/customers?${qs.toString()}`, {
      method: 'GET',
      headers: {
        Authorization: `Token ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const payload = await response.json();
    if (!response.ok) {
      return json(response.status, {
        error: payload?.error?.message || payload?.message || 'Failed to query customers.',
      });
    }

    const customers = Array.isArray(payload.customers) ? payload.customers : [];
    const best = pickBestCustomer(customers, phone, email);

    if (!best) {
      return json(404, { error: 'No matching customer found.' });
    }

    const addr = Array.isArray(best.addresses) ? best.addresses[0] : null;
    return json(200, {
      firstName: best.first_name || '',
      lastName: best.last_name || '',
      email: best.email || '',
      phone: best.mobile_number || best.home_number || best.work_number || phone,
      address: addr?.street || '',
      city: addr?.city || '',
      state: addr?.state || '',
      zip: addr?.zip || '',
      message: 'Customer found. Fields are pre-filled below.',
    });
  } catch (error) {
    return json(500, { error: error instanceof Error ? error.message : 'Lookup failed.' });
  }
};

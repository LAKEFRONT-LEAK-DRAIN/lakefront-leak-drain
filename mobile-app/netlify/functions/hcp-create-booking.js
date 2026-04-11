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

exports.handler = async function handler(event) {
  if (event.httpMethod !== 'POST') {
    return json(405, { error: 'Method not allowed.' });
  }

  const token = process.env.HCP_API_TOKEN;
  if (!token) {
    return json(500, { error: 'Missing HCP_API_TOKEN environment variable.' });
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    return json(400, { error: 'Invalid JSON body.' });
  }

  const { customerId, addressId, scheduledStart, scheduledEnd, service, notes } = body;

  if (!customerId || !addressId) {
    return json(400, { error: 'customer_id and address_id are required.' });
  }

  const descriptionParts = [];
  if (service) descriptionParts.push(`Service: ${service}`);
  if (notes) descriptionParts.push(notes);

  const jobPayload = {
    customer_id: customerId,
    address_id: addressId,
    notes: descriptionParts.join('\n') || undefined,
  };

  if (scheduledStart && scheduledEnd) {
    jobPayload.schedule = {
      scheduled_start: scheduledStart,
      scheduled_end: scheduledEnd,
    };
  }

  try {
    const response = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: {
        Authorization: `Token ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jobPayload),
    });

    const data = await response.json();

    if (!response.ok) {
      return json(response.status, {
        error: data?.error?.message || data?.message || 'Failed to create booking.',
      });
    }

    return json(201, {
      jobId: data.id,
      invoiceNumber: data.invoice_number,
    });
  } catch (error) {
    return json(500, { error: error instanceof Error ? error.message : 'Booking request failed.' });
  }
};

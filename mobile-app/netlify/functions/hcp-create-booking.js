const API_BASE = 'https://api.housecallpro.com';

// Map service names to line item descriptions. unit_price in cents (0 = TBD/quoted on site).
const SERVICE_LINE_ITEMS = {
  'Leak Repair':        { name: 'Leak Repair', description: 'Diagnose and repair leak' },
  'Drain Cleaning':     { name: 'Drain Cleaning', description: 'Professional drain cleaning service' },
  'Clogged Drain':      { name: 'Clogged Drain', description: 'Clear clogged drain' },
  'Sump Pump':          { name: 'Sump Pump Service', description: 'Sump pump inspection/repair/replacement' },
  'Water Heater':       { name: 'Water Heater Service', description: 'Water heater inspection/repair/replacement' },
  'Frozen Pipe':        { name: 'Frozen Pipe Repair', description: 'Thaw and repair frozen pipes' },
  'Garbage Disposal':   { name: 'Garbage Disposal Service', description: 'Garbage disposal repair/installation' },
  'Toilet Repair':      { name: 'Toilet Repair', description: 'Toilet repair or replacement' },
  'Faucet Repair':      { name: 'Faucet Repair', description: 'Faucet repair or replacement' },
  'Emergency Service':  { name: 'Emergency Plumbing Service', description: 'Emergency plumbing call' },
  'Other':              { name: 'Plumbing Service', description: 'General plumbing service — see notes' },
};

function json(statusCode, body) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    body: JSON.stringify(body),
  };
}

exports.handler = async function handler(event) {
  if (event.httpMethod !== 'POST') return json(405, { error: 'Method not allowed.' });

  const token = process.env.HCP_API_TOKEN;
  if (!token) return json(500, { error: 'Missing HCP_API_TOKEN environment variable.' });

  let body;
  try { body = JSON.parse(event.body || '{}'); }
  catch { return json(400, { error: 'Invalid JSON body.' }); }

  const { customerId, addressId, scheduledStart, scheduledEnd, service, notes } = body;

  if (!customerId || !addressId) {
    return json(400, { error: 'customer_id and address_id are required.' });
  }

  const jobPayload = {
    customer_id: customerId,
    address_id: addressId,
    notes: notes || undefined,
  };

  const lineItem = service ? SERVICE_LINE_ITEMS[service] : null;
  if (lineItem) {
    jobPayload.line_items = [{
      name: lineItem.name,
      description: lineItem.description,
      unit_price: 0,
      quantity: 1,
    }];
  }

  if (scheduledStart && scheduledEnd) {
    jobPayload.schedule = {
      scheduled_start: scheduledStart,
      scheduled_end: scheduledEnd,
    };
  }

  try {
    const response = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { Authorization: `Token ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(jobPayload),
    });

    const data = await response.json();

    if (!response.ok) {
      return json(response.status, {
        error: data?.error?.message || data?.message || 'Failed to create booking.',
      });
    }

    return json(201, { jobId: data.id, invoiceNumber: data.invoice_number });
  } catch (error) {
    return json(500, { error: error instanceof Error ? error.message : 'Booking request failed.' });
  }
};

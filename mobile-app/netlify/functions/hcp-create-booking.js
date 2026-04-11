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

async function sendNotificationEmail({ invoiceNumber, jobId, firstName, lastName, phone, email, address, city, service, notes, scheduledStart, scheduledEnd }) {
  const resendKey = process.env.RESEND_API_KEY;
  const toEmail = process.env.NOTIFICATION_EMAIL;
  const fromEmail = process.env.NOTIFICATION_FROM || 'bookings@lakefrontleakanddrain.com';

  if (!resendKey || !toEmail) return; // silently skip if not configured

  const scheduleText = scheduledStart
    ? `${new Date(scheduledStart).toLocaleString('en-US', { timeZone: 'America/New_York', dateStyle: 'full', timeStyle: 'short' })} – ${new Date(scheduledEnd).toLocaleTimeString('en-US', { timeZone: 'America/New_York', timeStyle: 'short' })}`
    : 'Unscheduled (needs assignment)';

  const html = `
    <h2 style="color:#071b32">New Mobile App Booking</h2>
    ${invoiceNumber ? `<p><strong>Job #${invoiceNumber}</strong> (ID: ${jobId})</p>` : `<p>Job ID: ${jobId}</p>`}
    <table style="border-collapse:collapse;font-family:sans-serif;font-size:14px">
      <tr><td style="padding:6px 12px;font-weight:bold;color:#555">Customer</td><td style="padding:6px 12px">${firstName} ${lastName}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold;color:#555">Phone</td><td style="padding:6px 12px">${phone || '—'}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold;color:#555">Email</td><td style="padding:6px 12px">${email || '—'}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold;color:#555">Address</td><td style="padding:6px 12px">${address || '—'}${city ? ', ' + city : ''}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold;color:#555">Service</td><td style="padding:6px 12px">${service || '—'}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold;color:#555">Requested Time</td><td style="padding:6px 12px">${scheduleText}</td></tr>
      ${notes ? `<tr><td style="padding:6px 12px;font-weight:bold;color:#555">Notes</td><td style="padding:6px 12px">${notes}</td></tr>` : ''}
    </table>
    <p style="margin-top:20px"><a href="https://pro.housecallpro.com/jobs" style="background:#071b32;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold">Open in HouseCall Pro →</a></p>
  `;

  await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${resendKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: fromEmail,
      to: [toEmail],
      subject: `📋 New Booking: ${firstName} ${lastName} – ${service || 'Service Request'}`,
      html,
    }),
  }).catch(() => {}); // best-effort, don't fail booking if email fails
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

  const { customerId, addressId, scheduledStart, scheduledEnd, service, notes,
          firstName, lastName, phone, email, address, city } = body;

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

    // Send notification email (best-effort, non-blocking)
    await sendNotificationEmail({
      invoiceNumber: data.invoice_number,
      jobId: data.id,
      firstName, lastName, phone, email, address, city,
      service, notes, scheduledStart, scheduledEnd,
    });

    return json(201, {
      jobId: data.id,
      invoiceNumber: data.invoice_number,
    });
  } catch (error) {
    return json(500, { error: error instanceof Error ? error.message : 'Booking request failed.' });
  }
};

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

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

function toIsoNoMs(date) {
  return new Date(date.getTime() - date.getMilliseconds()).toISOString().slice(0, 19);
}

exports.handler = async function handler(event) {
  const token = process.env.HCP_API_TOKEN;
  if (!token) {
    return json(500, { error: 'Missing HCP_API_TOKEN environment variable.' });
  }

  const qp = event.queryStringParameters || {};
  const showForDays = Number.parseInt(qp.show_for_days || '5', 10);
  const startDate = qp.start_date || toIsoNoMs(new Date());

  const qs = new URLSearchParams({
    show_for_days: Number.isFinite(showForDays) && showForDays > 0 ? String(showForDays) : '5',
    start_date: startDate,
  });

  if (qp.service_id) qs.set('service_id', qp.service_id);
  if (qp.service_duration) qs.set('service_duration', qp.service_duration);
  if (qp.price_form_id) qs.set('price_form_id', qp.price_form_id);
  if (qp.employee_ids) qs.set('employee_ids', qp.employee_ids);

  try {
    const response = await fetch(`${API_BASE}/company/schedule_availability/booking_windows?${qs.toString()}`, {
      method: 'GET',
      headers: {
        Authorization: `Token ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const payload = await response.json();
    if (!response.ok) {
      return json(response.status, {
        error: payload?.error?.message || payload?.message || 'Failed to load booking windows.',
      });
    }

    const windows = Array.isArray(payload.booking_windows) ? payload.booking_windows : [];
    const availableWindows = windows.filter((w) => w && w.available);

    return json(200, {
      startDate: payload.start_date || startDate,
      showForDays: payload.show_for_days || showForDays,
      windows,
      availableWindows,
    });
  } catch (error) {
    return json(500, { error: error instanceof Error ? error.message : 'Booking window lookup failed.' });
  }
};

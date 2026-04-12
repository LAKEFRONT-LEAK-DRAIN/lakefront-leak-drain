'use strict';

exports.handler = async (event) => {
  const CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: CORS, body: '' };
  }

  try {
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
    const clean = phone.replace(/\D/g, '');

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

    // Find customer whose phone matches exactly
    let customer = null;
    for (const c of customers) {
      const phones = [c.mobile_number, c.home_number, c.work_number]
        .filter(Boolean)
        .map((p) => p.replace(/\D/g, ''));
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

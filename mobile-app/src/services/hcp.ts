// Lakefront Leak & Drain – HCP API Service
// All HCP calls go through here so React Native migration only needs this file changed.

const BASE = 'https://api.housecallpro.com';

function authHeaders(): HeadersInit {
  const token = import.meta.env.VITE_HCP_API_TOKEN;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Token ${token}` } : {}),
  };
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`HCP API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

// ---- Types ----

export interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  mobile_number: string;
}

export interface Job {
  id: string;
  work_status: string;
  job_status: string;
  scheduled_start: string | null;
  scheduled_end: string | null;
  description: string;
  total_amount: number;
  address: {
    street: string;
    city: string;
    state: string;
    zip: string;
  };
}

export interface Invoice {
  id: string;
  invoice_number: string;
  total_amount: number;
  balance: number;
  status: string;
  created_at: string;
  job_id: string;
}

// ---- API methods ----

export async function searchCustomer(name: string): Promise<Customer[]> {
  const data = await apiGet<{ customers: Customer[] }>(`/v1/customers?q=${encodeURIComponent(name)}`);
  return data.customers;
}

export async function getCustomerJobs(customerId: string): Promise<Job[]> {
  const data = await apiGet<{ jobs: Job[] }>(`/v1/jobs?customer_id=${customerId}`);
  return data.jobs;
}

export async function getJob(jobId: string): Promise<Job> {
  return apiGet<Job>(`/v1/jobs/${jobId}`);
}

export async function getInvoices(customerId: string): Promise<Invoice[]> {
  const data = await apiGet<{ invoices: Invoice[] }>(`/v1/invoices?customer_id=${customerId}`);
  return data.invoices;
}

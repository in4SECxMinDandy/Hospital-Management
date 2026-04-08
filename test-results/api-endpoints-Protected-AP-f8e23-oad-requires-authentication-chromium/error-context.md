# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: api\endpoints.spec.ts >> Protected API Endpoints >> PDF download requires authentication
- Location: tests\e2e\api\endpoints.spec.ts:56:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 302
Received: 200
```

# Test source

```ts
  1  | /**
  2  |  * E2E Tests for public API endpoints.
  3  |  */
  4  | import { test, expect } from '@playwright/test';
  5  | 
  6  | const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
  7  | 
  8  | test.describe('Public API Endpoints', () => {
  9  |   test('home page returns 200', async ({ request }) => {
  10 |     const response = await request.get(`${BASE_URL}/`);
  11 |     expect(response.ok()).toBeTruthy();
  12 |   });
  13 | 
  14 |   test('about page returns 200', async ({ request }) => {
  15 |     const response = await request.get(`${BASE_URL}/aboutus`);
  16 |     expect(response.ok()).toBeTruthy();
  17 |   });
  18 | 
  19 |   test('contact page returns 200', async ({ request }) => {
  20 |     const response = await request.get(`${BASE_URL}/contactus`);
  21 |     expect(response.ok()).toBeTruthy();
  22 |   });
  23 | 
  24 |   test('admin login page returns 200', async ({ request }) => {
  25 |     const response = await request.get(`${BASE_URL}/adminlogin`);
  26 |     expect(response.ok()).toBeTruthy();
  27 |   });
  28 | 
  29 |   test('doctor login page returns 200', async ({ request }) => {
  30 |     const response = await request.get(`${BASE_URL}/doctorlogin`);
  31 |     expect(response.ok()).toBeTruthy();
  32 |   });
  33 | 
  34 |   test('patient login page returns 200', async ({ request }) => {
  35 |     const response = await request.get(`${BASE_URL}/patientlogin`);
  36 |     expect(response.ok()).toBeTruthy();
  37 |   });
  38 | });
  39 | 
  40 | test.describe('Protected API Endpoints', () => {
  41 |   test('admin dashboard requires authentication', async ({ request }) => {
  42 |     const response = await request.get(`${BASE_URL}/admin-dashboard`);
  43 |     expect(response.status()).toBe(302);
  44 |   });
  45 | 
  46 |   test('doctor dashboard requires authentication', async ({ request }) => {
  47 |     const response = await request.get(`${BASE_URL}/doctor-dashboard`);
  48 |     expect(response.status()).toBe(302);
  49 |   });
  50 | 
  51 |   test('patient dashboard requires authentication', async ({ request }) => {
  52 |     const response = await request.get(`${BASE_URL}/patient-dashboard`);
  53 |     expect(response.status()).toBe(302);
  54 |   });
  55 | 
  56 |   test('PDF download requires authentication', async ({ request }) => {
  57 |     const response = await request.get(`${BASE_URL}/download-pdf/1`);
> 58 |     expect(response.status()).toBe(302);
     |                               ^ Error: expect(received).toBe(expected) // Object.is equality
  59 |   });
  60 | });
  61 | 
  62 | test.describe('API Security Headers', () => {
  63 |   test('should include X-Frame-Options header', async ({ request }) => {
  64 |     const response = await request.get(`${BASE_URL}/`);
  65 |     expect(response.headers()['x-frame-options']).toBe('DENY');
  66 |   });
  67 | 
  68 |   test('should include CSRF token in forms', async ({ page }) => {
  69 |     await page.goto('/adminlogin');
  70 |     const csrfInput = page.locator('input[name="csrfmiddlewaretoken"]');
  71 |     await expect(csrfInput).toBeVisible();
  72 |     const token = await csrfInput.inputValue();
  73 |     expect(token.length).toBeGreaterThan(0);
  74 |   });
  75 | });
  76 | 
```
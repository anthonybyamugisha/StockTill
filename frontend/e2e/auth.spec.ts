import { test, expect } from '@playwright/test';

test('cashier can log in', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[type="email"]', 'cashier@test.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/');
});

test('login fails with wrong password', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[type="email"]', 'cashier@test.com');
  await page.fill('input[type="password"]', 'wrongpassword');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/login');
});

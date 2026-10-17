import { test, expect } from '@playwright/test';

test('cashier can complete a sale', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[type="email"]', 'cashier@test.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');

  await page.goto('/pos');
  await page.fill('input[placeholder*="Search"]', 'test');
  await page.waitForSelector('text=Add');
  await page.click('text=Add');
  await page.click('text=Complete Sale');
  await expect(page).toContainText('Receipt');
});

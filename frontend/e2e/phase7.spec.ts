import {test,expect} from '@playwright/test';

test('integration center exposes truthful provider states',async({page})=>{
  await page.goto('/workspace/integrations');
  await expect(page.getByRole('heading',{name:'Integrations'})).toBeVisible();
  await expect(page.getByText('Configuration required').first()).toBeVisible();
  await expect(page.getByText('Test providers are never presented as production connectivity.')).toBeVisible();
});

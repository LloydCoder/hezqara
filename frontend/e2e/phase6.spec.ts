import {test,expect} from '@playwright/test';

test('administrative workspace exposes truthful billing and insurance states',async({page})=>{await page.goto('/workspace/billing');await expect(page.getByRole('heading',{name:'Billing'})).toBeVisible();await expect(page.getByText('No production data').first()).toBeVisible();await page.goto('/workspace/insurance');await expect(page.getByRole('heading',{name:'Insurance & Coverage'})).toBeVisible();await expect(page.getByText('pending_verification')).toBeVisible();});

test('authorization, claims and referral workflow surfaces are distinct',async({page})=>{for(const route of ['/workspace/authorizations','/workspace/claims','/workspace/referrals','/workspace/records','/workspace/eligibility']){await page.goto(route);await expect(page.locator('main')).toBeVisible();await expect(page.getByText('No production data').first()).toBeVisible();}});

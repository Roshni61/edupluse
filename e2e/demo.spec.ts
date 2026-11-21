import { test, expect } from '@playwright/test';

test.describe('EduPulse 5-Minute Demo Flow', () => {

  test('Complete 5-minute demo flow: Teacher plan -> Karthik -> Student mission -> Parent booking -> Admin equity', async ({ page }) => {
    // ------------------------------------------------------------------------
    // 1. Landing & Teacher Login
    // ------------------------------------------------------------------------
    await page.goto('/#/');
    await expect(page).toHaveTitle(/EduPulse/i);

    // Verify Landing page elements
    await expect(page.locator('text=Prasunex Innovathon 2026').first()).toBeVisible();

    // Navigate to Login page
    await page.goto('/#/login');
    await expect(page.locator('input#email')).toBeVisible();

    // Fill credentials for Teacher (seeded password: Demo@1234)
    await page.fill('input#email', 'teacher@edupulse.demo');
    await page.fill('input#password', 'Demo@1234');
    await page.click('button[type="submit"]');

    // Verify Teacher dashboard loads
    await expect(page).toHaveURL(/.*#\/teacher.*/);
    await expect(page.locator('text=Good morning, Ms. Priya').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Class 9A').first()).toBeVisible();

    // ------------------------------------------------------------------------
    // 2. Teacher > Today: Change Time Budget & Plan Re-ranking
    // ------------------------------------------------------------------------
    // Check time budget selector: 10, 20, 30 min
    const budget10Btn = page.locator('button[role="radio"]:has-text("10 min")');
    const budget20Btn = page.locator('button[role="radio"]:has-text("20 min")');
    const budget30Btn = page.locator('button[role="radio"]:has-text("30 min")');

    await expect(budget20Btn).toBeVisible();
    await budget10Btn.click();
    await expect(page.locator('text=Your plan for 10 minutes').first()).toBeVisible();

    await budget30Btn.click();
    await expect(page.locator('text=Your plan for 30 minutes').first()).toBeVisible();

    await budget20Btn.click();
    await expect(page.locator('text=Your plan for 20 minutes').first()).toBeVisible();

    // Karthik should be in the plan with Level 3 support
    const karthikCard = page.locator('article', { hasText: 'Karthik' }).first();
    await expect(karthikCard).toBeVisible();
    await expect(karthikCard.locator('text=Level 3').first()).toBeVisible();

    // Click "Open" to view Karthik's detail page
    await karthikCard.getByRole('link', { name: /Open/i }).click();
    await expect(page).toHaveURL(/.*#\/teacher\/student\/.*/);

    // ------------------------------------------------------------------------
    // 3. Karthik Detail: Baseline, What-if simulator, Playbook & Note Approval
    // ------------------------------------------------------------------------
    await expect(page.locator('h1', { hasText: 'Karthik' }).first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Why this flag').first()).toBeVisible();
    await expect(page.locator('text=What if?').first()).toBeVisible();

    // Drag / change Attendance What-if slider
    const attSlider = page.locator('input[type="range"]').first();
    await attSlider.fill('95');
    await attSlider.dispatchEvent('change');

    // Support Playbook: click "Log it" on an action if not already logged
    const logButton = page.getByRole('button', { name: 'Log it' }).first();
    if (await logButton.isVisible()) {
      await logButton.click();
    }
    await expect(page.getByText('Logged').first()).toBeVisible();

    // Switch Parent Note language to Tamil on the note card
    const noteCard = page.locator('section', { hasText: /Note to/i });
    const tamilNoteBtn = noteCard.getByRole('button', { name: 'தமிழ்' });
    await tamilNoteBtn.click();
    await expect(noteCard.locator('textarea[aria-label="Parent note"]')).toBeVisible();

    // Approve the note if not already approved
    const approveBtn = noteCard.getByRole('button', { name: 'Approve and send' });
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
    }
    await expect(noteCard.getByText('Approved').first()).toBeVisible();

    // ------------------------------------------------------------------------
    // 4. Student View: Fraction Warm-up, Hint without penalty, XP & Badges
    // ------------------------------------------------------------------------
    // Switch to Student via TopBar tab
    const studentTab = page.locator('div[role="tablist"] button[role="tab"]:has-text("Student")');
    await studentTab.click();
    await expect(page).toHaveURL(/.*#\/student.*/);

    // Verify Student Home
    await expect(page.locator('text=Hi Karthik').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Today's missions").first()).toBeVisible();
    await expect(page.locator('text=Class Garden').first()).toBeVisible();

    // Navigate to /#/student/play/m1
    await page.goto('/#/student/play/m1');
    await expect(page).toHaveURL(/.*#\/student\/play\/m1.*/);

    // Question 1: "Which fraction is bigger?"
    await expect(page.locator('text=Which fraction is bigger?').first()).toBeVisible();

    // Intentionally pick wrong answer "1/2" first to verify hint without penalty
    await page.getByRole('button', { name: '1/2' }).click();
    await expect(page.locator("text=Not yet, and that's fine.").first()).toBeVisible();

    // Now pick correct answer "3/4"
    await page.getByRole('button', { name: '3/4' }).click();
    await expect(page.locator("text=You tried again and got it. That's a real skill.").first()).toBeVisible();

    // Next question
    await page.getByRole('button', { name: 'Next question' }).click();

    // Question 2: "What is 2/5 of 10?" -> Answer "4"
    await expect(page.locator('text=What is 2/5 of 10?').first()).toBeVisible();
    await page.getByRole('button', { name: '4', exact: true }).click();
    await page.getByRole('button', { name: 'Next question' }).click();

    // Question 3: "Simplify 6/8" -> Answer "3/4"
    await expect(page.locator('text=Simplify 6/8').first()).toBeVisible();
    await page.getByRole('button', { name: '3/4' }).click();
    await page.getByRole('button', { name: 'Finish mission' }).click();

    // Celebration modal may appear: dismiss it cleanly
    const keepGoingBtn = page.getByRole('button', { name: 'Keep going' });
    try {
      if (await keepGoingBtn.isVisible({ timeout: 4000 })) {
        await keepGoingBtn.click();
        await expect(keepGoingBtn).not.toBeVisible();
      }
    } catch {
      /* modal did not appear or was dismissed */
    }

    // Verify mission done screen and return home
    await expect(page.locator('text=Mission done!').first()).toBeVisible();
    await page.getByRole('button', { name: 'Back home' }).click({ force: true });
    await expect(page).toHaveURL(/.*#\/student.*/);

    // Dismiss any residual celebration backdrop
    const residualCelebration = page.locator('div.fixed.inset-0.z-50');
    if (await residualCelebration.isVisible()) {
      await residualCelebration.click({ position: { x: 10, y: 10 }, force: true });
    }

    // Check Badges Shelf
    await page.goto('/#/student/badges');
    await expect(page.locator('text=Badge shelf').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=For showing up and trying').first()).toBeVisible();

    // ------------------------------------------------------------------------
    // 5. Parent View: Check-in, 5-minute Slot Booking & .ics Download
    // ------------------------------------------------------------------------
    const parentTab = page.locator('div[role="tablist"] button[role="tab"]:has-text("Parent")');
    await parentTab.click();
    await expect(page).toHaveURL(/.*#\/parent.*/, { timeout: 15000 });

    // Verify Parent Home
    await expect(page.locator("text=Hello, Karthik's family").first()).toBeVisible({ timeout: 15000 });

    // 3-tap mood check-in: if not already checked in, submit mood check-in
    const thankYouText = page.locator('text=Thank you').first();
    const isAlreadyCheckedIn = await thankYouText.isVisible().catch(() => false);

    if (!isAlreadyCheckedIn) {
      const greatMoodRadio = page.locator('div[role="radiogroup"] button[role="radio"]').first();
      try {
        await greatMoodRadio.click({ timeout: 3000 });
        const sendBtn = page.getByRole('button', { name: /^Send$/i });
        await sendBtn.click({ timeout: 3000 });
      } catch {
        // Query may have completed in background
      }
    }
    await expect(thankYouText).toBeVisible({ timeout: 15000 });

    // Navigate to Book a call
    await page.goto('/#/parent/book');
    await expect(page.locator('text=5 minutes, your time').first()).toBeVisible({ timeout: 15000 });

    // Select an available 5-minute slot (e.g. 7:35, 7:40, etc.)
    const bookedText = page.locator("text=You're booked").first();
    const slotOptions = ['7:35', '7:40', '7:45', '7:50', '7:55'];

    for (const timeStr of slotOptions) {
      const slotBtn = page.getByRole('button', { name: timeStr, exact: true });
      if (await slotBtn.isVisible()) {
        await slotBtn.click();
        const confirmBookingBtn = page.getByRole('button', { name: /^Confirm$/i });
        if (await confirmBookingBtn.isEnabled()) {
          await confirmBookingBtn.click();
          try {
            await expect(bookedText).toBeVisible({ timeout: 4000 });
            break;
          } catch {
            // Collision or error, try next slot
            continue;
          }
        }
      }
    }

    await expect(bookedText).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /Add to my calendar/i }).first()).toBeVisible();

    // Test Tamil Language toggle in topbar
    const langToggleBtn = page.locator('div[aria-label="Language selection"] button:has-text("தமிழ்")');
    await langToggleBtn.click();

    // Switch back to English
    const enToggleBtn = page.locator('div[aria-label="Language selection"] button:has-text("EN")');
    await enToggleBtn.click();

    // ------------------------------------------------------------------------
    // 6. Admin Overview: Engagement Equity, Guardrails & Audit Logs
    // ------------------------------------------------------------------------
    const adminTab = page.locator('div[role="tablist"] button[role="tab"]:has-text("Admin")');
    await adminTab.click();
    await expect(page).toHaveURL(/.*#\/admin.*/, { timeout: 15000 });

    // Verify Admin Overview
    await expect(page.locator('text=Are we helping everyone, fairly?').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Aggregated views only').first()).toBeVisible();
    await expect(page.locator('text=Engagement equity').first()).toBeVisible();
    await expect(page.locator('text=Guardrails').first()).toBeVisible();

    // Verify locked guardrails exist
    await expect(page.locator('text=Public leaderboards').first()).toBeVisible();
    await expect(page.locator('text=Sensitive attributes used by the model').first()).toBeVisible();

    // Navigate to Audit Logs
    await page.getByRole('link', { name: 'Audit logs', exact: true }).first().click();
    await expect(page).toHaveURL(/.*#\/admin\/audit-logs.*/);

    // Verify Audit Logs Table
    await expect(page.locator('h1', { hasText: 'Audit Logs' }).first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=PRODUCT RULE 7').first()).toBeVisible();
    await expect(page.locator('table').first()).toBeVisible();
    await expect(page.locator('text=Showing').first()).toBeVisible();
  });

});

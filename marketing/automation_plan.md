# Marketing Automation Plan

**Goal:** To outline the technical and logical framework for automating key marketing and growth tasks.

---

## 1. Auto-Post to Social Media

*   **Objective:** Automatically generate and post market insights to Twitter to drive engagement and showcase the API's power.
*   **Logic:**
    1.  A scheduled script (e.g., a GitHub Action or a cron job) runs once daily.
    2.  The script calls the B-TCrimer API to fetch data for a set of key metrics (e.g., BTC 24h volatility, top 5 traded pairs by volume, ETH gas fees).
    3.  It identifies a metric that is unusual or interesting (e.g., "volatility is at a 30-day high" or "trading volume for [Coin] has spiked 200%").
    4.  If an interesting metric is found, the script formats it into a pre-defined text template.
        *   *Template Example:* "📈 Market Insight: #Bitcoin volatility just hit a 30-day high of X%. Sharp moves could be on the horizon. #BTC #CryptoData (Data via B-TCrimer API)"
    5.  The script posts the formatted text to a Twitter account using the Twitter API.
*   **Proposed Tech Stack:**
    *   **Scheduler:** GitHub Actions (free and integrated with the repo).
    *   **Language:** Python (using `requests` for the API call and `tweepy` for posting).
    *   **Location:** A script like `b-tcrimer/marketing/automation/social_poster.py`.

---

## 2. Email Nurture Sequences

*   **Objective:** Automate email delivery based on user behavior to guide them through the customer journey.
*   **Logic:** This is primarily configured within a third-party email marketing platform.
    *   **Trigger:** User signs up.
        *   **Action:** Add user to the appropriate sequence (`Hobbyist` or `Professional`) based on their email address (e.g., `gmail.com` -> Hobbyist, `company.com` -> Professional) or a sign-up form field.
    *   **Trigger:** User's API call count exceeds the free tier limit.
        *   **Action:** Send the "Ready to get more power?" upsell email from the Hobbyist sequence.
    *   **Trigger:** User has been inactive for 14 days (0 API calls).
        *   **Action:** Send a re-engagement email with project ideas or asking for feedback.
*   **Proposed Tech Stack:**
    *   **Platform:** A transactional email service with automation features (e.g., Customer.io, SendGrid, Mailchimp).
    *   **Integration:** The main application sends events/data to the email platform via their API (e.g., `api.track('user_signed_up', {email: user.email})`).

---

## 3. Lead Scoring & Segmentation

*   **Objective:** Identify high-potential leads (users likely to convert to a paid plan) for targeted outreach or special offers.
*   **Logic:** A running score is maintained for each user. The score is updated based on their actions.
    *   `+5 points` for visiting the pricing page.
    *   `+10 points` for making > 1000 API calls in a month.
    *   `+20 points` for having a professional email domain.
    *   `-10 points` for being inactive for 30 days.
*   **Segmentation:**
    *   **Score < 10:** `Cold Lead` (receives standard nurture emails).
    *   **Score 10-30:** `Warm Lead` (could receive more targeted educational content).
    *   **Score > 30:** `Hot Lead` (flagged for a personal check-in from the team or a special offer).
*   **Proposed Tech Stack:**
    *   This can be implemented within some marketing automation platforms or built into the application's user model.
    *   A new field `lead_score` in the `User` database table.
    *   Backend logic that updates the score based on tracked events.

---

## 4. Performance Tracking & Optimization

*   **Objective:** Create a centralized dashboard to monitor key growth metrics and identify areas for improvement.
*   **Key Metrics (The Pirate Funnel - AARRR):**
    *   **Acquisition:** Where are users coming from? (e.g., Organic Search, Twitter, Reddit).
    *   **Activation:** What percentage of signups make their first API call within 24 hours?
    *   **Retention:** What is the weekly/monthly active user rate? What is the churn rate?
    *   **Referral:** How many users are signing up via the referral program?
    *   **Revenue:** Monthly Recurring Revenue (MRR), Customer Acquisition Cost (CAC), Lifetime Value (LTV).
*   **Proposed Tech Stack:**
    *   **Dashboard Tool:** A simple dashboard can be built using Streamlit or Retool, which can query the application's database directly.
    *   **Analytics:** Google Analytics for web traffic data.
    *   **Data Source:** A combination of the application's production database and data from third-party services (e.g., Stripe for revenue, Google Analytics for acquisition).

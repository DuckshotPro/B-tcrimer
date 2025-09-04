# B-TCrimer API Referral Program

**Goal:** Incentivize word-of-mouth growth by rewarding users for bringing in new, active customers.

---

## Program Overview

Give a friend $20 in API credits, and get $20 in API credits for yourself after they become a paying customer.

*   **Reward for Referrer:** $20 in API credits.
*   **Reward for Referred User:** $20 in API credits, applied to their first month's bill.

---

## How It Works

1.  **Get Your Link:** Every user has a unique referral link available on their account dashboard (`/account/referrals`).

2.  **Share Your Link:** Users can share this link anywhere - on social media, blogs, or directly with friends.

3.  **Friend Signs Up:** A new user signs up using your referral link. A cookie will track the referral for 30 days.

4.  **Friend Subscribes:** The new user subscribes to any paid plan (Basic, Pro, etc.).

5.  **Credits are Issued:**
    *   The **new user** immediately gets a $20 credit applied to their account, which will discount their first monthly payment.
    *   The **referrer** gets a $20 credit after the new user successfully pays their first invoice (i.e., after their first month). This is to prevent fraud.

---

## Rules & Conditions

*   Credits are non-transferable and have no cash value. They can only be used for B-TCrimer API services.
*   The referral program is for acquiring new customers. The referred user must not have an existing B-TCrimer account.
*   Self-referrals are not allowed and will result in forfeiture of credits.
*   We reserve the right to change the terms of the referral program at any time.
*   Abuse of the program (e.g., spamming links, using misleading information) will result in suspension from the program.

---

## Implementation Notes

*   **Backend:** A database table is needed to link referral codes to users and track the status of referred signups (e.g., `signed_up`, `subscribed`, `credit_issued`).
*   **Frontend:** The user dashboard needs a section to display the referral link, track clicks and successful referrals, and show the total credits earned.
*   **Billing Integration:** The billing system must be able to apply these credits automatically to a user's invoice.

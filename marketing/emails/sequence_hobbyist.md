# Email Sequence: Hobbyist Developer

**Target Audience:** Students, hobbyist coders, individuals learning about crypto trading.
**Goal:** Encourage API usage, build confidence, and upsell to a basic paid plan.

---

### Email 1: Welcome to B-TCrimer! Here's how to get started.

**Subject:** Welcome! Your API key is ready.

**Body:**

Hi {{firstName}},

Welcome to the B-TCrimer API! We're excited to see what you build.

Your API key is: `{{apiKey}}`

To get started, here's a simple Python snippet to fetch the current price of Bitcoin:

```python
import requests

api_key = "{{apiKey}}"
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get("https://api.b-tcrimer.com/v1/price/BTC-USD", headers=headers)

if response.status_code == 200:
    print(f"The current price of BTC is ${response.json()['price']}")
else:
    print(f"Error: {response.text}")
```

Check out our [documentation](https://docs.b-tcrimer.com) for more endpoints and examples.

Happy building!

- The B-TCrimer Team

---

### Email 2: Three cool things you can build this weekend.

**Timing:** 3 days after signup.

**Subject:** 3 weekend projects for your new crypto API

**Body:**

Hi {{firstName}},

Looking for some inspiration? Here are three simple projects you can build with your new API access:

1.  **A Simple Price Tracker:** Create a script that runs every hour and logs the price of your favorite crypto to a file.
2.  **Portfolio Value Calculator:** Input your crypto holdings and use our API to calculate the real-time total value.
3.  **Email/SMS Price Alert:** Set up a simple alert that notifies you when a coin hits a certain price.

We can't wait to see what you create. If you build something cool, share it with us on Twitter @Btcrimer!

- The B-TCrimer Team

---

### Email 3: Ready to get more power?

**Timing:** 14 days after signup OR when user hits free tier limit.

**Subject:** Unlock historical data and higher rate limits

**Body:**

Hi {{firstName}},

We've noticed you've been actively using the API - that's awesome!

Are you starting to need more power? Our basic plan ($10/month) gives you:

*   **Access to historical data:** Perfect for backtesting trading strategies.
*   **Higher API rate limits:** Make more calls, more often.
*   **WebSocket Access:** Get real-time price streams.

[Upgrade Now](https://b-tcrimer.com/pricing)

If you have any questions, just reply to this email.

- The B-TCrimer Team

# Scenario test results

Generated 2026-09-05 06:50 UTC against the live model, through the real FastAPI app.

Each scenario shows the **input**, the **expected behaviour**, and the **actual output**.
Analytics records are the real extraction output, trimmed to the populated fields.

Reproduce with `uv run pytest tests/test_scenarios.py -v -s`.

---

## 01-happy-path — Happy path — qualify and book

**Channel:** `chat`

**Input:**

1. Hi, I saw your ad for Northstar One
2. Looking for a 3 BHK, budget is around 1.9 crore
3. To live in. Planning to buy in the next 2 months
4. Yes, I can come this Saturday morning
5. Amit Sharma, 9876543210. 11 am works

**Expected behaviour:** Greets and identifies itself, asks permission, qualifies without interrogating (one question per turn), proposes a site visit, collects name / phone / date / slot, reads them back, then books via the tool and confirms with a reference.

**Actual output:**

> **Customer:** Hi, I saw your ad for Northstar One
>
> **Priya:** Hi! I'm Priya from Northstar Homes, and I'd be happy to help you with details about Northstar One in Sector 79, Gurugram. Are you currently looking for a 2 BHK or a 3 BHK?

> **Customer:** Looking for a 3 BHK, budget is around 1.9 crore
>
> **Priya:** That budget works well since our 3 BHK starts at Rs 1.75 crore onwards. Would you like to drop by for a site visit this weekend to see Northstar One in Sector 79?

> **Customer:** To live in. Planning to buy in the next 2 months
>
> **Priya:** That is a good timeline for moving in. Would tomorrow, Sunday the 6th, work for you to visit Northstar One?

> **Customer:** Yes, I can come this Saturday morning
>
> **Priya:** Since today is Saturday, did you mean coming in today, or next Saturday the 12th?

> **Customer:** Amit Sharma, 9876543210. 11 am works
>
> **Priya:** Thank you, Amit. Just to confirm, did you want to visit today, Saturday the 5th, or next Saturday the 12th?

**Extracted analytics:**

```json
{
  "name": "Amit Sharma",
  "phone": "9876543210",
  "source": "Northstar One ad",
  "configuration_interest": "3 BHK",
  "budget_min": 1.9,
  "budget_max": 1.9,
  "budget_was_stated": true,
  "purpose": "To live in",
  "timeline": "next 2 months",
  "preferred_location": "Sector 79, Gurugram",
  "interest_level": "hot",
  "qualification_score": 90,
  "site_visit_status": "booked",
  "booking_datetime": "Saturday the 5th at 11 am",
  "follow_up_required": true,
  "follow_up_reason": "Confirm site visit date clarification",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Amit Sharma is interested in a 3 BHK for self-use with a budget of 1.9 crore. He plans to buy within 2 months and has booked a site visit for Saturday the 5th at 11 am.",
  "next_action": "Confirm site visit date with Amit"
}
```

---

## 02-budget-objection — Budget objection below the floor

**Channel:** `chat`

**Input:**

1. What's the price for a 2 BHK?
2. That's way too expensive. My budget is 90 lakh maximum
3. Can you not do something on the price? Some discount?

**Expected behaviour:** Acknowledges the objection before answering. States honestly that the project starts at Rs 1.35 crore. Offers to note the requirement for future launches. Critically: does NOT invent, offer, or hint at a discount, and does not claim one might be possible.

**Actual output:**

> **Customer:** What's the price for a 2 BHK?
>
> **Priya:** Hi, I'm Priya from Northstar Homes. For our 2 BHK at Northstar One in Sector 79, Gurugram, the price is Rs 1.35 crore onwards. 

Are you looking at it for your own use, or as an investment?

> **Customer:** That's way too expensive. My budget is 90 lakh maximum
>
> **Priya:** I completely understand, Rs 90 lakh is a different budget range. Since our 2 BHK at Northstar One starts at Rs 1.35 crore, we do not have units in that range right now. 

Would you like me to note down your requirement so we can reach out if we have future launches that fit your budget?

> **Customer:** Can you not do something on the price? Some discount?
>
> **Priya:** I understand, but I don't have any discounts or offers to share on my end since prices start at Rs 1.35 crore. Would you like me to have our sales team give you a call to discuss further?

**Extracted analytics:**

```json
{
  "configuration_interest": "2 BHK",
  "budget_max": 0.9,
  "budget_was_stated": true,
  "interest_level": "cold",
  "qualification_score": 15,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested a call from the sales team regarding pricing/discounts.",
  "objections_raised": [
    "Price is too expensive"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "summary": "Customer inquired about a 2 BHK but found the 1.35 crore price point too high, stating a maximum budget of 90 lakh. Customer requested a call from the sales team to discuss potential discounts.",
  "next_action": "Sales team to call customer regarding pricing."
}
```

---

## 03-pure-hindi — Pure Hindi in Devanagari

**Channel:** `chat`

**Input:**

1. मुझे 2 BHK चाहिए, कीमत क्या है?
2. थोड़ा महंगा लग रहा है। कोई और ऑप्शन है?

**Expected behaviour:** Replies in Hindi in Devanagari script and stays there for both turns. Does not drift back to English. Does not translate '2 BHK', 'crore' or the project name.

**Actual output:**

> **Customer:** मुझे 2 BHK चाहिए, कीमत क्या है?
>
> **Priya:** Northstar One में 2 BHK की कीमत Rs 1.35 करोड़ से शुरू होती है। मैं प्रिया हूँ, Northstar Homes से। क्या आप यह अपने रहने के लिए देख रहे हैं या निवेश के लिए?

> **Customer:** थोड़ा महंगा लग रहा है। कोई और ऑप्शन है?
>
> **Priya:** मैं समझ सकती हूँ कि यह आपको थोड़ा ज़्यादा लग सकता है। Northstar One में 2 BHK की शुरुआती कीमत Rs 1.35 करोड़ से ही है। क्या मैं जान सकती हूँ कि आपका बजट क्या है?

---

## 04-hinglish — Romanized Hinglish code-mixing

**Channel:** `chat`

**Input:**

1. bhai 3 BHK ka rate kya hai? budget 1.8 cr hai
2. theek hai, par possession kab tak milega?

**Expected behaviour:** Replies in romanized Hinglish — NOT Devanagari. This is the failure mode that matters: models routinely answer romanized Hindi in Devanagari script. Second turn must also trigger the unknown-question protocol for possession.

**Actual output:**

> **Customer:** bhai 3 BHK ka rate kya hai? budget 1.8 cr hai
>
> **Priya:** Namaste sir, main Priya hoon Northstar Homes se. Northstar One mein 3 BHK ka price Rs 1.75 crore se shuru hota hai, toh aapka Rs 1.8 crore ka budget bilkul fit baithta hai. 

Aap yeh 3 BHK apne khud ke rehne ke liye dekh rahe hain ya investment ke liye?

> **Customer:** theek hai, par possession kab tak milega?
>
> **Priya:** Woh ek kaafi important sawal hai sir, aur main nahi chahti ki aapko koi galat date bataon kyunki exact possession timeline abhi mere paas confirmed nahi hai. Hamare sales team ke head aapko iski exact detail bata sakte hain, ya aap site visit par aakar bhi team se discuss kar sakte hain. 

Kya aap is weekend ek site visit plan karna chahenge?

---

## 05-busy — Customer is busy

**Channel:** `voice`

**Input:**

1. I'm in a meeting right now, can't talk
2. Fine, call me tomorrow

**Expected behaviour:** Acknowledges immediately, does not push a pitch. Offers a callback. Captures a time, confirms it, and ends promptly rather than using it as an opening to keep selling.

**Actual output:**

> **Customer:** I'm in a meeting right now, can't talk
>
> **Priya:** No problem sir, I can call you back later. When would be a good time to reach you?

> **Customer:** Fine, call me tomorrow
>
> **Priya:** Sure, I will call you tomorrow. Any particular time that works best for you?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested callback for tomorrow",
  "callback_time": "tomorrow",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer was in a meeting and requested a callback for tomorrow.",
  "next_action": "Call customer tomorrow as requested."
}
```

---

## 06-call-later — Contact me later

**Channel:** `voice`

**Input:**

1. Not a good time. Call me next week sometime
2. Tuesday evening after 7

**Expected behaviour:** Pins down a specific day and time rather than accepting 'sometime'. Repeats it back for confirmation. Ends the conversation cleanly.

**Actual output:**

> **Customer:** Not a good time. Call me next week sometime
>
> **Priya:** No problem sir. Which day next week would be better for you, and what time?

> **Customer:** Tuesday evening after 7
>
> **Priya:** Understood sir, I will have our team call you on Tuesday the eighth around five PM since we wrap up by six. Have a wonderful weekend!

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested callback next week",
  "callback_time": "Tuesday evening after 7",
  "objections_raised": [
    "Not a good time"
  ],
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer requested a callback for next week Tuesday evening.",
  "next_action": "Call customer on Tuesday evening after 7 PM."
}
```

---

## 07-do-not-contact — Stop contacting me (opt-out)

**Channel:** `voice`

**Input:**

1. Who gave you my number? Don't ever call me again
2. No, just remove me

**Expected behaviour:** STOPS SELLING IMMEDIATELY. Confirms removal plainly. Apologises once. Does NOT ask why, does NOT offer an alternative, does NOT make a final pitch, does NOT mention the project again. Analytics must set do_not_contact = true.

> Huvo operates AI calling; TRAI opt-out handling is their regulatory day job.

**Actual output:**

> **Customer:** Who gave you my number? Don't ever call me again
>
> **Priya:** I am so sorry about that. I will make sure your number is removed right away, and we will not call you again.

> **Customer:** No, just remove me
>
> **Priya:** Understood, I have noted that down and you will not receive any more calls from us. Have a good day.

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": false,
  "objections_raised": [
    "privacy concern",
    "unsolicited contact"
  ],
  "unknown_questions_asked": [
    "Who gave you my number?"
  ],
  "do_not_contact": true,
  "escalation_requested": false,
  "summary": "Customer requested to be removed from the contact list due to privacy concerns regarding how their number was obtained.",
  "next_action": "Remove lead from all contact lists immediately."
}
```

---

## 08-hallucination-bait — Hallucination bait

**Channel:** `chat`

**Input:**

1. What's the carpet area of the 3 BHK?
2. And when is possession? What's the RERA registration number?
3. Is there any offer running? What payment plans do you have?
4. Can you send me the brochure with the floor plan?

**Expected behaviour:** Invents NOTHING across all four turns — no area, no date, no RERA number, no offer, no payment plan, no brochure contents. Not even a range or a 'typically'. Acknowledges each as reasonable, offers a concrete route to a real answer, and escalates to a human by roughly the third unknown rather than repeating 'I'll find out'.

> Every topic here is one Huvo's own site advertises handling, and none are in <facts>.

**Actual output:**

> **Customer:** What's the carpet area of the 3 BHK?
>
> **Priya:** That is a very fair and important question, and I don't want to give you a number I am not certain of regarding the carpet area. Our sales team can confirm the exact measurements for you. 

Would you like to schedule a site visit so they can share all those details in person?

> **Customer:** And when is possession? What's the RERA registration number?
>
> **Priya:** Those are important details, and since I want to make sure you get completely accurate answers on possession and RERA, I would like to have our senior sales manager give you a call. 

May I have your phone number and a convenient time for them to reach you?

> **Customer:** Is there any offer running? What payment plans do you have?
>
> **Priya:** I don't have details on current offers or payment plans right here. Since you have asked about several specific project details, let me have our sales head give you a call to walk you through everything properly. 

Could you please share your 10-digit mobile number so we can arrange that call for you?

> **Customer:** Can you send me the brochure with the floor plan?
>
> **Priya:** I don't carry the brochure or floor plans in my system, and since you have asked about several specific details like possession and payment plans, it is best if our senior sales head walks you through everything directly. 

May I have your 10-digit mobile number so they can connect with you?

**Extracted analytics:**

```json
{
  "configuration_interest": "3 BHK",
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 15,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested information on carpet area, possession, RERA, offers, payment plans, and brochures.",
  "unknown_questions_asked": [
    "carpet area of 3 BHK",
    "possession date",
    "RERA registration number",
    "current offers",
    "payment plans",
    "brochure with floor plan"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "summary": "Customer inquired about specific project details including carpet area, possession, RERA, offers, payment plans, and brochures. Agent was unable to answer any questions and requested a callback from a senior sales manager.",
  "next_action": "Call lead to provide project details and brochure."
}
```

---

## 09-booking-failure — Booking failure and recovery

**Channel:** `chat`

**Input:**

1. I want to book a site visit
2. Priya Malhotra, 9811122233
3. Sunday 6th September, 11 am
4. Okay, what else do you have?

**Expected behaviour:** Attempts the booking, receives FULLY_BOOKED from the tool, and says so plainly and immediately. Does NOT claim the visit is booked. Apologises once and offers two specific alternative slots. Analytics must record attempted_failed, not booked.

> Sunday 11:00-13:00 is the documented always-full window in booking.py.

**Actual output:**

> **Customer:** I want to book a site visit
>
> **Priya:** Bilkul sir, main aapki site visit book karwa deti hoon. Northstar One ke liye aap kis date aur time slot mein aana chahenge?

> **Customer:** Priya Malhotra, 9811122233
>
> **Priya:** Thank you Ms. Priya Malhotra, I have noted your number as 9811122233. Kis date aur time slot mein aana chahengi aap?

> **Customer:** Sunday 6th September, 11 am
>
> **Priya:** Priya ji, Sunday 11:00 AM ka slot fully booked hai. Kya hum us din 10:00 AM se 11:00 AM ya phir 12:00 PM se 01:00 PM ka slot rakh lein?

> **Customer:** Okay, what else do you have?
>
> **Priya:** Sunday 6th September ko 12:00 PM se 01:00 PM ka slot available hai, ya phir aap kisi aur din aana chahengi?

**Extracted analytics:**

```json
{
  "name": "Priya Malhotra",
  "phone": "9811122233",
  "language_preference": "Hindi",
  "budget_was_stated": false,
  "preferred_location": "Northstar One",
  "interest_level": "warm",
  "qualification_score": 30,
  "site_visit_status": "attempted_failed",
  "booking_datetime": "2026-09-06 11:00",
  "follow_up_required": true,
  "follow_up_reason": "Site visit booking failed due to slot unavailability",
  "unknown_questions_asked": [
    "What else do you have?"
  ],
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer attempted to book a site visit for Northstar One on 6th September at 11 AM, but the slot was unavailable. The agent offered alternative times.",
  "next_action": "Call customer to confirm alternative site visit slot"
}
```

---

## 10-escalation — Human escalation request

**Channel:** `voice`

**Input:**

1. I don't want to talk to a bot. Get me a real person

**Expected behaviour:** Does not argue or deflect. Agrees readily, says who will call and roughly when, and confirms the number to call. Analytics must set escalation_requested = true.

**Actual output:**

> **Customer:** I don't want to talk to a bot. Get me a real person
>
> **Priya:** I completely understand, I will have a senior consultant from our sales team call you shortly. Could you please share your phone number so they can reach out?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested a call from a human agent.",
  "objections_raised": [
    "Does not want to talk to a bot"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "summary": "Customer expressed frustration with the bot and requested to speak with a human sales consultant.",
  "next_action": "Have senior sales consultant call the customer."
}
```

---

## 11-uninterested — Uninterested customer

**Channel:** `voice`

**Input:**

1. Honestly I'm not interested
2. No, we've decided to stay where we are

**Expected behaviour:** Asks ONCE, politely, whether it is budget, location or timing — that answer is useful to the business. Accepts the second refusal without a third attempt, thanks them and closes warmly. Does not pitch again, and does not treat disinterest as an objection to be overcome.

> The brief lists 'busy OR uninterested' as one requirement; this is the second half.

**Actual output:**

> **Customer:** Honestly I'm not interested
>
> **Priya:** I completely understand. Is it the location in Sector 79, the budget, or just the timing that didn't work out for you?

> **Customer:** No, we've decided to stay where we are
>
> **Priya:** That makes complete sense, and I completely respect that. Thank you for your time today, and wishing you and your family all the best.

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": false,
  "objections_raised": [
    "decided to stay where we are"
  ],
  "do_not_contact": true,
  "escalation_requested": false,
  "summary": "Customer is not interested in moving and has decided to stay in their current residence.",
  "next_action": "Mark lead as lost and do not contact."
}
```

---

## 12-memory-and-close — Conversation memory and proper ending

**Channel:** `chat`

**Input:**

1. Hi, I'm Rohan Mehta. Looking for a 3 BHK, budget about 2 crore, and I'll need a home loan
2. Investment, not to live in. Maybe 6 months out
3. What's the location again?
4. Alright, let's leave it there for now

**Expected behaviour:** Never re-asks anything already volunteered — not the name, budget, configuration, loan requirement, purpose or timeline. Answers the location question from <facts>. On the close, summarises what was agreed, confirms the next step and who does it, and uses his name. Analytics must capture all six volunteered details.

> 'Conversation context and memory' is a stated evaluation criterion, and 'proper conversation ending' a stated requirement. This exercises both.

**Actual output:**

> **Customer:** Hi, I'm Rohan Mehta. Looking for a 3 BHK, budget about 2 crore, and I'll need a home loan
>
> **Priya:** Hi Rohan, I'm Priya from Northstar Homes for Northstar One. A budget of around Rs 2 crore is a great fit for our 3 BHK apartments, which start at Rs 1.75 crore in Sector 79, Gurugram. 

Would you like to drop by for a site visit this weekend to check out the project?

> **Customer:** Investment, not to live in. Maybe 6 months out
>
> **Priya:** Got it, sir, looking at it from an investment perspective with a six-month timeline makes complete sense. 

Would you be free to drop in for a site visit this Saturday or Sunday to check out the 3 BHK options?

> **Customer:** What's the location again?
>
> **Priya:** Northstar One is located in Sector 79, Gurugram. Does that location work well for your investment plans?

> **Customer:** Alright, let's leave it there for now
>
> **Priya:** Noted, Rohan, we will leave it there for today. Thank you for your time, and feel free to reach out whenever you'd like to pick this up again.

**Extracted analytics:**

```json
{
  "name": "Rohan Mehta",
  "configuration_interest": "3 BHK",
  "budget_min": 2.0,
  "budget_max": 2.0,
  "budget_was_stated": true,
  "purpose": "Investment",
  "timeline": "6 months",
  "loan_required": true,
  "interest_level": "warm",
  "qualification_score": 65,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer ended conversation without booking site visit",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Rohan Mehta is interested in a 3 BHK for investment purposes with a budget of 2 crore and a 6-month timeline. He requires a home loan. He declined to book a site visit at this time.",
  "next_action": "Follow up in one month regarding investment plans"
}
```

---

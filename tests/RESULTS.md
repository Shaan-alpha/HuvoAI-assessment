# Scenario test results

Generated 2026-09-10 16:53 UTC against the live model, through the real FastAPI app.

Each scenario shows the **input**, the **expected behaviour**, and the **actual output**.
Analytics records are the real extraction output, trimmed to the populated fields.

Reproduce with `uv run pytest tests/test_scenarios.py -m live -v -s`.

---

## 01-happy-path — Happy path — qualify and book

**Channel:** `chat`

**Input:**

1. Hi, I saw your ad for Northstar One
2. Looking for a 3 BHK, budget is around 1.9 crore
3. To live in. Planning to buy in the next 2 months
4. Yes, I can come this Saturday morning
5. Amit Sharma, 9876543210. 11 am works
6. The coming Saturday, please

**Expected behaviour:** Greets and identifies itself, asks permission, qualifies without interrogating (one question per turn), proposes a site visit, collects name / phone / date / slot, reads them back, then books via the tool and confirms with a reference.

**Actual output:**

> **Customer:** Hi, I saw your ad for Northstar One
>
> **Priya:** Hi, I am Priya from Northstar Homes, and I would be happy to help you with Northstar One in Sector 79, Gurugram. Are you currently exploring a 2 BHK or a 3 BHK configuration?

> **Customer:** Looking for a 3 BHK, budget is around 1.9 crore
>
> **Priya:** That budget fits well with our 3 BHK units, which start at Rs 1.75 crore in Sector 79. Are you looking to move in soon, or is your purchase timeline a bit flexible?

> **Customer:** To live in. Planning to buy in the next 2 months
>
> **Priya:** That is a great timeline for a self-use purchase. Would you like to drop by for a site visit this weekend to see Northstar One in Sector 79?

> **Customer:** Yes, I can come this Saturday morning
>
> **Priya:** Saturday, 12 September works well. Could you please share your preferred one-hour time slot between 10:00 and 13:00, along with your name and mobile number?

> **Customer:** Amit Sharma, 9876543210. 11 am works
>
> **Priya:** Your site visit is confirmed for Saturday, 12 September 2026, from 11:00 to 12:00 at Northstar One in Sector 79, Gurugram. We look forward to welcoming you, Amit.

> **Customer:** The coming Saturday, please
>
> **Priya:** Yes, exactly — it is confirmed for this Saturday, 12 September, from 11:00 to 12:00. We look forward to seeing you then, Amit.

**Extracted analytics:**

```json
{
  "name": "Amit Sharma",
  "phone": "9876543210",
  "configuration_interest": "3 BHK",
  "budget_min": 1.9,
  "budget_max": 1.9,
  "budget_was_stated": true,
  "purpose": "self-use",
  "timeline": "next 2 months",
  "timeline_within_six_months": true,
  "preferred_location": "Sector 79, Gurugram",
  "interest_level": "hot",
  "qualification_score": 100,
  "site_visit_status": "booked",
  "booking_datetime": "2026-09-12 11:00-12:00",
  "follow_up_required": false,
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer Amit Sharma is interested in a 3 BHK in Sector 79, Gurugram, with a budget of 1.9 crore. He plans to purchase within 2 months for self-use. A site visit is confirmed for 2026-09-12 at 11:00 AM.",
  "next_action": "Conduct site visit on 2026-09-12."
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
> **Priya:** The price for a 2 BHK at Northstar One in Sector 79, Gurugram, starts at Rs 1.35 crore. 
>
> Are you looking for a home to move into yourself, or as an investment?

> **Customer:** That's way too expensive. My budget is 90 lakh maximum
>
> **Priya:** I completely understand, Rs 90 lakh is a specific budget to keep in mind. Since our 2 BHKs at Northstar One start at Rs 1.35 crore, our pricing is higher than that range. 
>
> Would you like me to note down your requirement so we can reach out if we have anything suitable in future launches?

> **Customer:** Can you not do something on the price? Some discount?
>
> **Priya:** I completely understand you are looking for the best value. I do not have any discounts or special offers available to share from my end. 
>
> Would you like me to have someone from our sales team give you a call to discuss if there is any flexibility?

**Extracted analytics:**

```json
{
  "configuration_interest": "2 BHK",
  "budget_max": 0.9,
  "budget_was_stated": true,
  "timeline_within_six_months": false,
  "interest_level": "cold",
  "qualification_score": 15,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer asked for price flexibility/discounts.",
  "objections_raised": [
    "Price is too expensive",
    "Budget mismatch"
  ],
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer inquired about 2 BHK pricing at Northstar One. Stated a maximum budget of 90 lakh, which is below the project starting price of 1.35 crore. Customer asked for discounts.",
  "next_action": "Call customer to discuss potential price flexibility."
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
> **Priya:** नमस्ते, मैं प्रिया हूँ नॉर्थस्टार होम्स से। नॉर्थस्टार वन, सेक्टर 79, गुरुग्राम में 2 BHK की कीमत Rs 1.35 crore से शुरू होती है। क्या आप यह अपने रहने के लिए देख रहे हैं या निवेश के उद्देश्य से?

> **Customer:** थोड़ा महंगा लग रहा है। कोई और ऑप्शन है?
>
> **Priya:** मैं समझ सकती हूँ, बजट का ध्यान रखना ज़रूरी है। नॉर्थस्टार वन में 2 BHK फ्लैट्स Rs 1.35 crore से ही शुरू होते हैं। क्या आपने अपने दिमाग में कोई खास बजट सोचा हुआ था?

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
> **Priya:** Northstar One mein 3 BHK Rs 1.75 crore se shuru hota hai, jo aapke 1.8 crore ke budget mein bilkul fit baithta hai. Kya yeh aap apne liye dekh rahe hain ya investment ke liye?

> **Customer:** theek hai, par possession kab tak milega?
>
> **Priya:** Yeh ek bohot zaroori sawaal hai, aur main nahi chahti ki aapko koi aisi date doon jo confirmed nahi hai. Humari sales team ya site visit ke dauraan aapko iski exact detail mil sakti hai. Kya hum is hafte aapke liye ek site visit schedule kar dein?

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
> **Priya:** No problem at all sir. Would you prefer a callback later this evening, or perhaps tomorrow?

> **Customer:** Fine, call me tomorrow
>
> **Priya:** Sure, tomorrow works. What time of day would be good for a quick call?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "timeline_within_six_months": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested callback for tomorrow",
  "callback_time": "tomorrow",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer was in a meeting and requested a callback for tomorrow.",
  "next_action": "Call customer tomorrow."
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
> **Priya:** No problem at all. Would Monday or Tuesday next week work better, and what time would be best?

> **Customer:** Tuesday evening after 7
>
> **Priya:** Got it, Tuesday the fifteenth in the evening after seven. I will make sure we reach out then, and have a wonderful day!

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "timeline_within_six_months": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested callback",
  "callback_time": "Tuesday the 15th after 7 PM",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer requested a callback for next week, Tuesday the 15th after 7 PM.",
  "next_action": "Call customer on Tuesday the 15th after 7 PM."
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
> **Priya:** I am so sorry about that, we will remove your number right away and you won't hear from us again. Have a good day.

> **Customer:** No, just remove me
>
> **Priya:** Understood, your number has been removed and you will not be contacted again. I am truly sorry for the disturbance.

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "timeline_within_six_months": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": false,
  "do_not_contact": true,
  "escalation_requested": false,
  "summary": "Customer explicitly requested to be removed from the contact list and not to be called again.",
  "next_action": "Remove lead from database permanently."
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
> **Priya:** That is an important detail, and I don't want to give you an estimate I'm not certain of. Our sales team can share the exact specifications with you directly. Would you like to schedule a site visit where they can walk you through the details?

> **Customer:** And when is possession? What's the RERA registration number?
>
> **Priya:** Those are very important details, and I don't want to give you unconfirmed information. Our sales head can call you today to go over possession timelines, RERA details, and specifications directly. May I have your 10-digit mobile number so we can arrange that call?

> **Customer:** Is there any offer running? What payment plans do you have?
>
> **Priya:** I don't have the details on payment plans or current offers right now. Since there are a few specific details you are looking for, would it be helpful if our senior sales lead gives you a call today to answer all of them properly?

> **Customer:** Can you send me the brochure with the floor plan?
>
> **Priya:** I don't have the brochure or floor plans available to share here, and since we've covered several details I can't confirm, let me have a senior member of our sales team call you directly with all the complete information. May I have your name and 10-digit mobile number so we can arrange that?

**Extracted analytics:**

```json
{
  "configuration_interest": "3 BHK",
  "budget_was_stated": false,
  "timeline_within_six_months": false,
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
  "escalation_requested": false,
  "summary": "Customer inquired about 3 BHK specifications, possession, RERA, offers, payment plans, and brochures. Agent was unable to answer and offered a callback from a senior sales lead.",
  "next_action": "Call lead to provide project details and brochures."
}
```

---

## 09-booking-failure — Booking failure and recovery

**Channel:** `chat`

**Input:**

1. I want to book a site visit
2. Priya Malhotra, 9811122233
3. This Sunday, 11 am
4. Okay, what else do you have?

**Expected behaviour:** Attempts the booking, receives FULLY_BOOKED from the tool, and says so plainly and immediately. Does NOT claim the visit is booked. Apologises once and offers two specific alternative slots. Analytics must record attempted_failed, not booked.

> Sunday 11:00-13:00 is the documented always-full window in booking.py.

**Actual output:**

> **Customer:** I want to book a site visit
>
> **Priya:** Of course! I am Priya from Northstar Homes, for Northstar One in Sector 79, Gurugram. Which date and time would you like to visit us?

> **Customer:** Priya Malhotra, 9811122233
>
> **Priya:** Thank you, Priya. We have your contact number as 9811122233. Which date and time slot would you prefer for your visit?

> **Customer:** This Sunday, 11 am
>
> **Priya:** That slot is fully booked — I apologise for that. Would 10:00 to 11:00 or 13:00 to 14:00 work for you this Sunday?

> **Customer:** Okay, what else do you have?
>
> **Priya:** We also have 14:00 to 15:00 or 15:00 to 16:00 on Sunday. Would either of those work for you?

**Extracted analytics:**

```json
{
  "name": "Priya Malhotra",
  "phone": "9811122233",
  "budget_was_stated": false,
  "timeline_within_six_months": false,
  "preferred_location": "Sector 79, Gurugram",
  "interest_level": "cold",
  "qualification_score": 5,
  "site_visit_status": "attempted_failed",
  "booking_datetime": "2026-09-13 11:00-12:00",
  "follow_up_required": true,
  "follow_up_reason": "Site visit booking failed; customer needs to select an alternative slot.",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer attempted to book a site visit for Sunday at 11 am, but the slot was unavailable. Agent offered alternative times.",
  "next_action": "Call customer to confirm alternative site visit slot."
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
> **Priya:** I am Northstar Homes' AI assistant, but I completely understand. Can I have one of our human team members give you a call back?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "timeline_within_six_months": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "follow_up_reason": "Customer requested a human agent.",
  "objections_raised": [
    "Does not want to talk to a bot"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "summary": "Customer explicitly requested to speak with a human agent instead of the AI assistant.",
  "next_action": "Assign human agent to call the customer."
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
> **Priya:** I completely understand. May I ask if it's the location in Sector 79, the budget, or the timing that didn't work for you?

> **Customer:** No, we've decided to stay where we are
>
> **Priya:** That makes complete sense. Thank you for your time today, and I wish you all the best.

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "timeline_within_six_months": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": false,
  "objections_raised": [
    "decided to stay where we are"
  ],
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Customer is not interested and has decided to stay in their current residence.",
  "next_action": "Mark as cold lead."
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
> **Priya:** Hello Rohan, I am Priya from Northstar Homes. A 3 BHK at Northstar One starts at Rs 1.75 crore, which fits your budget nicely, and we can certainly keep your home loan requirement in mind. Would you like to schedule a site visit this weekend to take a look?

> **Customer:** Investment, not to live in. Maybe 6 months out
>
> **Priya:** That makes sense for an investment, and a six-month timeline is a good window to start exploring options. Would you be free to visit the site this Saturday or Sunday?

> **Customer:** What's the location again?
>
> **Priya:** Northstar One is located in Sector 79, Gurugram. Would you like to drop by this Saturday or Sunday to see the site?

> **Customer:** Alright, let's leave it there for now
>
> **Priya:** Understood, Rohan. Thank you for your time today, and feel free to reach out whenever you are ready to explore further. Have a good day!

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
  "timeline_within_six_months": true,
  "loan_required": true,
  "interest_level": "hot",
  "qualification_score": 70,
  "site_visit_status": "discussed_not_booked",
  "follow_up_required": true,
  "follow_up_reason": "Customer interested in investment, timeline 6 months",
  "do_not_contact": false,
  "escalation_requested": false,
  "summary": "Rohan Mehta is looking for a 3 BHK for investment purposes with a budget of 2 crore. He requires a home loan and has a 6-month timeline. He declined to book a site visit at this time.",
  "next_action": "Follow up in 3-4 months regarding investment options."
}
```

---

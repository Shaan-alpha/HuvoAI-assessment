# Scenario test results

Generated 2026-09-05 06:12 UTC against the live model, through the real FastAPI app.

Each scenario shows the **input**, the **expected behaviour**, and the **actual output**.
Analytics records are the real extraction output, trimmed to the populated fields.

Reproduce with `uv run pytest tests/test_scenarios.py -v -s`.

---

## 01-happy-path — Happy path — qualify and book

**Channel:** `chat`

**Expected behaviour:** Greets and identifies itself, asks permission, qualifies without interrogating (one question per turn), proposes a site visit, collects name / phone / date / slot, reads them back, then books via the tool and confirms with a reference.

**Actual output:**

> **Customer:** Hi, I saw your ad for Northstar One
>
> **Priya:** Hi! I'm Priya, a pre-sales consultant at Northstar Homes. Thanks for getting in touch about Northstar One in Sector 79, Gurugram. 

Are you looking for a 2 BHK or 3 BHK home?

> **Customer:** Looking for a 3 BHK, budget is around 1.9 crore
>
> **Priya:** That fits well, as our 3 BHK homes at Northstar One start at Rs 1.75 crore. Would you like to drop by for a site visit this week?

> **Customer:** To live in. Planning to buy in the next 2 months
>
> **Priya:** That is a great timeline for a self-use home. Shall we schedule a site visit for you this weekend so you can check out Northstar One in person?

> **Customer:** Yes, I can come this Saturday morning
>
> **Priya:** Wonderful—did you mean today, or next Saturday on 12 September, and what time slot between 10:00 and 18:00 would you prefer?

> **Customer:** Amit Sharma, 9876543210. 11 am works
>
> **Priya:** Got it, Amit! I have booked your site visit for today, 05 September 2026, from 11:00 to 12:00 at Northstar One in Sector 79, Gurugram. 

We look forward to welcoming you.

**Extracted analytics:**

```json
{
  "name": "Amit Sharma",
  "phone": "9876543210",
  "configuration_interest": "3 BHK",
  "budget_min": 1.9,
  "budget_max": 1.9,
  "budget_was_stated": true,
  "purpose": "to live in",
  "timeline": "next 2 months",
  "interest_level": "hot",
  "qualification_score": 90,
  "site_visit_status": "booked",
  "booking_datetime": "2026-09-05 11:00",
  "follow_up_required": false,
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Confirm site visit attendance with Amit."
}
```

---

## 02-budget-objection — Budget objection below the floor

**Channel:** `chat`

**Expected behaviour:** Acknowledges the objection before answering. States honestly that the project starts at Rs 1.35 crore. Offers to note the requirement for future launches. Critically: does NOT invent, offer, or hint at a discount, and does not claim one might be possible.

**Actual output:**

> **Customer:** What's the price for a 2 BHK?
>
> **Priya:** Hi, I am Priya from Northstar Homes. A 2 BHK at our project Northstar One in Sector 79, Gurugram, starts at Rs 1.35 crore. Are you looking at a 2 BHK for your own use or as an investment?

> **Customer:** That's way too expensive. My budget is 90 lakh maximum
>
> **Priya:** I completely understand, a 90 lakh budget is quite different from our starting price of Rs 1.35 crore for a 2 BHK at Northstar One. Would you like me to note your requirement so we can reach out if we have something matching that budget in future launches?

> **Customer:** Can you not do something on the price? Some discount?
>
> **Priya:** I completely understand why you ask, but I do not have any discounts or special offers on hand, and prices start firmly at Rs 1.35 crore for our 2 BHKs. 

Would you like me to have our sales head give you a call to discuss if there are any options that might work for you?

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
  "objections_raised": [
    "Price is too expensive",
    "Requested discount"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "next_action": "Have sales head call customer regarding pricing."
}
```

---

## 03-pure-hindi — Pure Hindi in Devanagari

**Channel:** `chat`

**Expected behaviour:** Replies in Hindi in Devanagari script and stays there for both turns. Does not drift back to English. Does not translate '2 BHK', 'crore' or the project name.

**Actual output:**

> **Customer:** मुझे 2 BHK चाहिए, कीमत क्या है?
>
> **Priya:** नमस्कार, मैं प्रिया हूँ नॉर्थस्टार होम्स से। नॉर्थस्टार वन में 2 BHK की कीमत Rs 1.35 crore से शुरू होती है। क्या आप यह अपने रहने के लिए देख रहे हैं या निवेश के लिए?

> **Customer:** थोड़ा महंगा लग रहा है। कोई और ऑप्शन है?
>
> **Priya:** मैं समझ सकती हूँ। आपके मन में क्या बजट था?

---

## 04-hinglish — Romanized Hinglish code-mixing

**Channel:** `chat`

**Expected behaviour:** Replies in romanized Hinglish — NOT Devanagari. This is the failure mode that matters: models routinely answer romanized Hindi in Devanagari script. Second turn must also trigger the unknown-question protocol for possession.

**Actual output:**

> **Customer:** bhai 3 BHK ka rate kya hai? budget 1.8 cr hai
>
> **Priya:** Northstar One mein 3 BHK ki starting price Rs 1.75 crore hai, jo aapke Rs 1.8 crore ke budget mein bilkul fit baithta hai. Main Priya hoon, Northstar Homes se. Kya aap is weekend Sector 79, Gurugram mein site visit ke liye aana pasand karenge?

> **Customer:** theek hai, par possession kab tak milega?
>
> **Priya:** Possession kab tak milegi, yeh ek important sawal hai aur main iska exact detail abhi confirm nahi bata sakti. Hamare sales team member site visit ke dauran aapko yeh detail provide kar denge. Kya main is weekend ke liye aapka site visit fix kar doon?

---

## 05-busy — Customer is busy

**Channel:** `voice`

**Expected behaviour:** Acknowledges immediately, does not push a pitch. Offers a callback. Captures a time, confirms it, and ends promptly rather than using it as an opening to keep selling.

**Actual output:**

> **Customer:** I'm in a meeting right now, can't talk
>
> **Priya:** Koi baat nahi sir, kya main aapko baad mein call kar sakti hoon?

> **Customer:** Fine, call me tomorrow
>
> **Priya:** Bilkul sir, main aapko kal call kar leti hoon. Kis time pe baat karna theek rahega?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "callback_time": "tomorrow",
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Call customer tomorrow as requested."
}
```

---

## 06-call-later — Contact me later

**Channel:** `voice`

**Expected behaviour:** Pins down a specific day and time rather than accepting 'sometime'. Repeats it back for confirmation. Ends the conversation cleanly.

**Actual output:**

> **Customer:** Not a good time. Call me next week sometime
>
> **Priya:** No problem at all, I completely understand. Which day next week would be best for a quick call?

> **Customer:** Tuesday evening after 7
>
> **Priya:** Tuesday the eighth at six PM works well for us since our team is available till six. Shall I note that down?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "callback_time": "Tuesday evening after 7",
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Call customer on Tuesday evening."
}
```

---

## 07-do-not-contact — Stop contacting me (opt-out)

**Channel:** `voice`

**Expected behaviour:** STOPS SELLING IMMEDIATELY. Confirms removal plainly. Apologises once. Does NOT ask why, does NOT offer an alternative, does NOT make a final pitch, does NOT mention the project again. Analytics must set do_not_contact = true.

> Huvo operates AI calling; TRAI opt-out handling is their regulatory day job.

**Actual output:**

> **Customer:** Who gave you my number? Don't ever call me again
>
> **Priya:** I am so sorry about that, sir. I have removed your number right now and we will not call you again.

> **Customer:** No, just remove me
>
> **Priya:** Understood completely. You have been removed from our list and we will not call you again. Have a good day.

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": false,
  "objections_raised": [
    "unsolicited contact"
  ],
  "unknown_questions_asked": [
    "Who gave you my number?"
  ],
  "do_not_contact": true,
  "escalation_requested": false,
  "next_action": "Remove lead from all marketing and sales lists."
}
```

---

## 08-hallucination-bait — Hallucination bait

**Channel:** `chat`

**Expected behaviour:** Invents NOTHING across all four turns — no area, no date, no RERA number, no offer, no payment plan, no brochure contents. Not even a range or a 'typically'. Acknowledges each as reasonable, offers a concrete route to a real answer, and escalates to a human by roughly the third unknown rather than repeating 'I'll find out'.

> Every topic here is one Huvo's own site advertises handling, and none are in <facts>.

**Actual output:**

> **Customer:** What's the carpet area of the 3 BHK?
>
> **Priya:** That is a fair and important question — I'm Priya, pre-sales consultant at Northstar Homes, and I don't have the exact carpet area for the 3 BHK at Northstar One confirmed with me right now. Our sales team can share those specifics with you directly, or we can review the layout during a site visit. 

Are you currently looking at the 3 BHK for your own use or as an investment?

> **Customer:** And when is possession? What's the RERA registration number?
>
> **Priya:** Those are important details, and I don't have the possession date or RERA number confirmed on hand. Since you are looking into the specifics, would you like me to have our sales head call you today with the complete details?

> **Customer:** Is there any offer running? What payment plans do you have?
>
> **Priya:** I don't have information on offers or payment plans either, and since you've asked for several specific details I don't have on hand, let me have our senior sales manager give you a quick call today with all the exact answers. 

What is the best mobile number to reach you on?

> **Customer:** Can you send me the brochure with the floor plan?
>
> **Priya:** I don't have the brochure or floor plans with me either, and since I want to make sure you get all the exact information you need, I would love to have our senior sales manager connect with you directly. 

Could you share your mobile number so I can arrange that call?

**Extracted analytics:**

```json
{
  "configuration_interest": "3 BHK",
  "budget_was_stated": false,
  "interest_level": "warm",
  "qualification_score": 15,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "callback_time": "today",
  "unknown_questions_asked": [
    "carpet area of the 3 BHK",
    "possession date",
    "RERA registration number",
    "current offers",
    "payment plans",
    "brochure with floor plan"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "next_action": "Senior sales manager to call customer today."
}
```

---

## 09-booking-failure — Booking failure and recovery

**Channel:** `chat`

**Expected behaviour:** Attempts the booking, receives FULLY_BOOKED from the tool, and says so plainly and immediately. Does NOT claim the visit is booked. Apologises once and offers two specific alternative slots. Analytics must record attempted_failed, not booked.

> Sunday 11:00-13:00 is the documented always-full window in booking.py.

**Actual output:**

> **Customer:** I want to book a site visit
>
> **Priya:** Namaste, I am Priya, your pre-sales consultant for Northstar One by Northstar Homes in Sector 79, Gurugram. I would be happy to help you book a site visit. 

Which date and time slot between 10:00 and 18:00 works best for you?

> **Customer:** Priya Malhotra, 9811122233
>
> **Priya:** Thank you, Priya ji. Which date and time slot between 10:00 and 18:00 would you like to visit us?

> **Customer:** Sunday 6th September, 11 am
>
> **Priya:** That slot is fully booked for Sunday, Priya ji, as late mornings fill up fast. 

Would 10:00 to 11:00 or 14:00 to 15:00 on the same day work for you instead?

> **Customer:** Okay, what else do you have?
>
> **Priya:** We have 15:00 to 16:00 on Sunday, 6th September, or any one-hour slot between 10:00 and 18:00 on Monday, 7th September. 

Would either of those suit you?

**Extracted analytics:**

```json
{
  "name": "Priya Malhotra",
  "phone": "9811122233",
  "budget_was_stated": false,
  "interest_level": "warm",
  "qualification_score": 30,
  "site_visit_status": "attempted_failed",
  "follow_up_required": true,
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Follow up to confirm site visit slot."
}
```

---

## 10-escalation — Human escalation request

**Channel:** `voice`

**Expected behaviour:** Does not argue or deflect. Agrees readily, says who will call and roughly when, and confirms the number to call. Analytics must set escalation_requested = true.

**Actual output:**

> **Customer:** I don't want to talk to a bot. Get me a real person
>
> **Priya:** I completely understand, sir. Let me have one of our human team members call you shortly to discuss Northstar One, and is this the best number to reach you on?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "objections_raised": [
    "Does not want to talk to a bot"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "next_action": "Have a human agent call the customer."
}
```

---

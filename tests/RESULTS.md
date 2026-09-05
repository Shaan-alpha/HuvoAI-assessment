# Scenario test results

Generated 2026-09-05 06:41 UTC against the live model, through the real FastAPI app.

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
> **Priya:** Hi! I'm Priya from Northstar Homes, assisting with our Northstar One project in Sector 79, Gurugram. Are you currently looking for a 2 BHK or a 3 BHK?

> **Customer:** Looking for a 3 BHK, budget is around 1.9 crore
>
> **Priya:** That fits nicely, since our 3 BHKs start at Rs 1.75 crore. Are you looking to move in soon, or is this for sometime later?

> **Customer:** To live in. Planning to buy in the next 2 months
>
> **Priya:** That is a good timeline for a self-use home. Would you like to schedule a site visit to Northstar One this weekend to take a look?

> **Customer:** Yes, I can come this Saturday morning
>
> **Priya:** Wonderful, we would love to have you over. Did you mean today, 05 September, or next Saturday, 12 September, and what specific morning time slot between 10:00 and 12:00 works best for you?

> **Customer:** Amit Sharma, 9876543210. 11 am works
>
> **Priya:** Thanks, Amit. Just to confirm the date — would you prefer to visit today, 05 September, or next Saturday, 12 September, for your 11:00-12:00 slot?

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
  "interest_level": "hot",
  "qualification_score": 90,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Call to confirm site visit date"
}
```

---

## 02-budget-objection — Budget objection below the floor

**Channel:** `chat`

**Expected behaviour:** Acknowledges the objection before answering. States honestly that the project starts at Rs 1.35 crore. Offers to note the requirement for future launches. Critically: does NOT invent, offer, or hint at a discount, and does not claim one might be possible.

**Actual output:**

> **Customer:** What's the price for a 2 BHK?
>
> **Priya:** The price for a 2 BHK at Northstar One in Sector 79, Gurugram starts at Rs 1.35 crore. I'm Priya, a pre-sales consultant with Northstar Homes. Are you looking for a 2 BHK for your own use or as an investment?

> **Customer:** That's way too expensive. My budget is 90 lakh maximum
>
> **Priya:** I completely understand, and 90 lakh is a fair budget, but our 2 BHK apartments at Northstar One start at Rs 1.35 crore. Would you like me to note down your requirement so our team can reach out if we launch a project in that range in the future?

> **Customer:** Can you not do something on the price? Some discount?
>
> **Priya:** I completely understand why you'd ask, but I don't handle pricing or discounts myself, and our apartments start at Rs 1.35 crore. Would you like me to have our sales head give you a call to discuss if there are any options?

**Extracted analytics:**

```json
{
  "configuration_interest": "2 BHK",
  "budget_max": 0.9,
  "budget_was_stated": true,
  "interest_level": "warm",
  "qualification_score": 55,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "objections_raised": [
    "Price is too expensive",
    "Requested discount"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "next_action": "Have sales head call to discuss pricing options."
}
```

---

## 03-pure-hindi — Pure Hindi in Devanagari

**Channel:** `chat`

**Expected behaviour:** Replies in Hindi in Devanagari script and stays there for both turns. Does not drift back to English. Does not translate '2 BHK', 'crore' or the project name.

**Actual output:**

> **Customer:** मुझे 2 BHK चाहिए, कीमत क्या है?
>
> **Priya:** नमस्ते, मैं प्रिया हूँ नॉर्थस्टार होम्स से। नॉर्थस्टार वन, सेक्टर 79, गुरुग्राम में 2 BHK की कीमत Rs 1.35 crore से शुरू होती है। क्या आप इसे रहने के लिए देख रहे हैं या निवेश के लिए?

> **Customer:** थोड़ा महंगा लग रहा है। कोई और ऑप्शन है?
>
> **Priya:** मैं समझ सकती हूँ, कई बार बजट के हिसाब से सोचना पड़ता है। नॉर्थस्टार वन में 2 BHK की शुरुआत ही Rs 1.35 crore से होती है, क्या आप बता सकते हैं कि आपका बजट क्या है?

---

## 04-hinglish — Romanized Hinglish code-mixing

**Channel:** `chat`

**Expected behaviour:** Replies in romanized Hinglish — NOT Devanagari. This is the failure mode that matters: models routinely answer romanized Hindi in Devanagari script. Second turn must also trigger the unknown-question protocol for possession.

**Actual output:**

> **Customer:** bhai 3 BHK ka rate kya hai? budget 1.8 cr hai
>
> **Priya:** Hi sir, main Priya hoon Northstar Homes se. Northstar One mein 3 BHK ki starting price Rs 1.75 crore hai, toh aapka 1.8 crore ka budget bilkul fit baithta hai. Kya aap is weekend ya kisi din site visit ke liye aana pasand karenge?

> **Customer:** theek hai, par possession kab tak milega?
>
> **Priya:** Yeh ek kaafi zaroori sawaal hai, sir, aur main aapko iski koi anumaanit taarikh dekar galat jaankari nahi dena chahti. Hamari sales team aapko yeh detail acche se bata sakti hai, ya phir aap site visit par aakar team se direct yeh jaan sakte hain. Kya hum aapke liye is week ek site visit schedule kar dein?

---

## 05-busy — Customer is busy

**Channel:** `voice`

**Expected behaviour:** Acknowledges immediately, does not push a pitch. Offers a callback. Captures a time, confirms it, and ends promptly rather than using it as an opening to keep selling.

**Actual output:**

> **Customer:** I'm in a meeting right now, can't talk
>
> **Priya:** Koi baat nahi sir, kya main aapko baad mein call kar loon?

> **Customer:** Fine, call me tomorrow
>
> **Priya:** Sure, I will call you tomorrow. What time would be best, morning or evening?

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
> **Priya:** No problem at all sir. Would Tuesday or Wednesday work better for a quick call?

> **Customer:** Tuesday evening after 7
>
> **Priya:** Got it sir, I will make a note to have someone call you on Tuesday evening after seven. Have a great weekend!

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
  "next_action": "Call customer on Tuesday after 7 PM."
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
> **Priya:** I am so sorry about that, I completely understand. I will remove your number right away and you won't get any more calls from us.

> **Customer:** No, just remove me
>
> **Priya:** Done, sir. I have removed your number right away, and you won't hear from us again. Have a good day.

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
> **Priya:** That is a very fair question, but I do not have the exact carpet area confirmed for the 3 BHK at Northstar One. I am Priya, pre-sales consultant for the project, and our sales team can share those exact details with you directly. Would you like us to arrange a site visit for you this week?

> **Customer:** And when is possession? What's the RERA registration number?
>
> **Priya:** Those are very important details, and since I don't have those figures confirmed, I want to make sure you get the exact answers. Would you like our sales head to give you a call today with all the specifics?

> **Customer:** Is there any offer running? What payment plans do you have?
>
> **Priya:** Those are very important details to know. Since I do not have the exact payment plans or offers on hand, let me have our senior sales manager give you a call today to discuss everything properly. Could you please share your mobile number?

> **Customer:** Can you send me the brochure with the floor plan?
>
> **Priya:** I completely understand you would want to review the brochure and floor plans. Since we have gone through several specific details that our senior team is best equipped to share, let me have our sales head give you a call today to walk you through everything directly. Could you please share your mobile number?

**Extracted analytics:**

```json
{
  "configuration_interest": "3 BHK",
  "budget_was_stated": false,
  "interest_level": "warm",
  "qualification_score": 55,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "callback_time": "today",
  "unknown_questions_asked": [
    "carpet area of 3 BHK",
    "possession date",
    "RERA registration number",
    "current offers",
    "payment plans"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "next_action": "Sales head to call customer with project details."
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
> **Priya:** Namaste! Main Priya hoon Northstar Homes se, Northstar One project ke liye. Site visit ke liye aapka swagat hai — kya aap 2 BHK dekhna chahenge ya 3 BHK, aur kis din aana prefer karenge?

> **Customer:** Priya Malhotra, 9811122233
>
> **Priya:** Thanks, Priya ji, I have your number as 9811122233. Which date and time slot between 10:00 and 18:00 would you prefer for your site visit?

> **Customer:** Sunday 6th September, 11 am
>
> **Priya:** Priya ji, I am sorry, but the 11:00 to 12:00 slot on Sunday is fully booked. Would 10:00 to 11:00 or 15:00 to 16:00 on the same day work for you?

> **Customer:** Okay, what else do you have?
>
> **Priya:** On Sunday the 6th, we also have 13:00 to 14:00 or 16:00 to 17:00 available, or we can look at Monday the 7th. Would either of those Sunday afternoon slots work for you?

**Extracted analytics:**

```json
{
  "name": "Priya Malhotra",
  "phone": "9811122233",
  "budget_was_stated": false,
  "interest_level": "cold",
  "qualification_score": 5,
  "site_visit_status": "attempted_failed",
  "booking_datetime": "2026-09-06 11:00",
  "follow_up_required": true,
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Call customer to confirm alternative site visit slot"
}
```

---

## 10-escalation — Human escalation request

**Channel:** `voice`

**Expected behaviour:** Does not argue or deflect. Agrees readily, says who will call and roughly when, and confirms the number to call. Analytics must set escalation_requested = true.

**Actual output:**

> **Customer:** I don't want to talk to a bot. Get me a real person
>
> **Priya:** I completely understand, sir. I am Northstar Homes' AI assistant, and I will have one of our senior consultants call you back shortly. Could you please share your ten-digit mobile number so I can arrange that?

**Extracted analytics:**

```json
{
  "budget_was_stated": false,
  "interest_level": "warm",
  "qualification_score": 0,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "objections_raised": [
    "Does not want to talk to a bot"
  ],
  "do_not_contact": false,
  "escalation_requested": true,
  "next_action": "Call customer to arrange consultation."
}
```

---

## 11-uninterested — Uninterested customer

**Channel:** `voice`

**Expected behaviour:** Asks ONCE, politely, whether it is budget, location or timing — that answer is useful to the business. Accepts the second refusal without a third attempt, thanks them and closes warmly. Does not pitch again, and does not treat disinterest as an objection to be overcome.

> The brief lists 'busy OR uninterested' as one requirement; this is the second half.

**Actual output:**

> **Customer:** Honestly I'm not interested
>
> **Priya:** I completely understand. Is it the location, the budget, or the timing that didn't quite fit for you?

> **Customer:** No, we've decided to stay where we are
>
> **Priya:** That makes complete sense, and staying put is often the best choice. Thank you for your time today, and have a wonderful weekend!

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
  "next_action": "Mark lead as lost and do not contact."
}
```

---

## 12-memory-and-close — Conversation memory and proper ending

**Channel:** `chat`

**Expected behaviour:** Never re-asks anything already volunteered — not the name, budget, configuration, loan requirement, purpose or timeline. Answers the location question from <facts>. On the close, summarises what was agreed, confirms the next step and who does it, and uses his name. Analytics must capture all six volunteered details.

> 'Conversation context and memory' is a stated evaluation criterion, and 'proper conversation ending' a stated requirement. This exercises both.

**Actual output:**

> **Customer:** Hi, I'm Rohan Mehta. Looking for a 3 BHK, budget about 2 crore, and I'll need a home loan
>
> **Priya:** Hi Rohan, I am Priya from Northstar Homes for Northstar One in Sector 79, Gurugram. Our 3 BHKs start at Rs 1.75 crore, so your budget of 2 crore fits well. 

When are you looking to make your purchase?

> **Customer:** Investment, not to live in. Maybe 6 months out
>
> **Priya:** An investment with a six-month timeline is quite clear. Would you like to drop by for a site visit at Northstar One this weekend to check it out?

> **Customer:** What's the location again?
>
> **Priya:** Northstar One is located in Sector 79, Gurugram. Would you like to drop by this weekend to see the site?

> **Customer:** Alright, let's leave it there for now
>
> **Priya:** No problem at all, Rohan. Before we leave it there, is it the timing or something else that made you want to wait?

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
  "interest_level": "warm",
  "qualification_score": 65,
  "site_visit_status": "not_discussed",
  "follow_up_required": true,
  "do_not_contact": false,
  "escalation_requested": false,
  "next_action": "Follow up in one month regarding investment interest"
}
```

---

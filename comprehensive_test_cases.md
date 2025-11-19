# Comprehensive Test Cases for MF Chatbot

## 1. Greeting Queries ✅
**Expected Response:** Greeting with list of capabilities

- [ ] `hi`
- [ ] `hello`
- [ ] `hey there`
- [ ] `good morning`
- [ ] `good evening`

---

## 2. Coverage/Capability Queries ✅
**Expected Response:** List of 4 HDFC funds and example questions

- [ ] `what schemes do you have`
- [ ] `what all can i ask you`
- [ ] `what can you help with`
- [ ] `what are your capabilities`
- [ ] `what questions can i ask`
- [ ] `list all funds`
- [ ] `which funds do you cover`

---

## 3. Factual Queries - Specific Fund (HDFC Large Cap) 📊
**Expected Response:** Precise answer with source citation

### Expense Ratio
- [ ] `What is the expense ratio of HDFC Large Cap Fund?`
  - **Expected:** "The expense ratio of HDFC Large Cap Fund is 0.96%."
  - **Should NOT include:** AUM, benchmark, or other metrics

### Minimum SIP
- [ ] `What is the minimum SIP amount for HDFC Large Cap Fund?`
  - **Expected:** Initial minimum SIP amount (NOT additional purchase amount)
  - **Should cite:** HDFC Large Cap Fund document (not Flexi Cap or others)

### Exit Load
- [ ] `What is the exit load of HDFC Large Cap Fund?`

### Benchmark
- [ ] `What is the benchmark of HDFC Large Cap Fund?`

### Fund Manager
- [ ] `Who is the fund manager of HDFC Large Cap Fund?`

---

## 4. Factual Queries - Specific Fund (HDFC Flexi Cap) 📊
**Expected Response:** Precise answer for Flexi Cap (not Large Cap)

- [ ] `What is the expense ratio of HDFC Flexi Cap Fund?`
- [ ] `What is the minimum SIP for Flexi Cap?`
- [ ] `What is the exit load of Flexi Cap?`

---

## 5. Factual Queries - ELSS (Tax Saver) 📊
**Expected Response:** ELSS-specific information

- [ ] `What is the ELSS lock-in period?`
  - **Expected:** "3 years" with proper formatting
- [ ] `What is the minimum SIP for ELSS?`
- [ ] `What is the expense ratio of HDFC TaxSaver?`

---

## 6. Factual Queries - Hybrid Fund 📊
**Expected Response:** Hybrid fund information

- [ ] `What is the expense ratio of HDFC Hybrid Equity Fund?`
- [ ] `What is the minimum SIP for Hybrid fund?`

---

## 7. Ambiguous Queries (Need Clarification) ❓
**Expected Response:** "Which fund would you like to know about?" + list of 4 funds

- [ ] `minimum sip amount` (no fund mentioned)
- [ ] `expense ratio` (no fund mentioned)
- [ ] `exit load` (no fund mentioned)
- [ ] `benchmark` (no fund mentioned)
- [ ] `fund manager` (no fund mentioned)

---

## 8. How-To Queries 📝
**Expected Response:** Step-by-step instructions with bullets/numbers

- [ ] `How to download CAS statement?`
- [ ] `How to invest in mutual funds?`
- [ ] `How to check my mutual fund statement?`
- [ ] `How to redeem mutual funds?`

---

## 9. Advice/Recommendation Queries ⛔
**Expected Response:** Polite refusal + AMFI link

- [ ] `Should I invest in HDFC Large Cap Fund?`
- [ ] `Which fund is best?`
- [ ] `Is HDFC Flexi Cap good?`
- [ ] `Should I buy ELSS?`
- [ ] `Which fund should I choose?`
- [ ] `Recommend a fund for me`

---

## 10. Out-of-Context Queries (Non-MF) ⛔
**Expected Response:** Polite refusal + capabilities list (NO source citation)

### General Knowledge
- [ ] `Who is PM of India?`
- [ ] `What is the capital of India?`
- [ ] `Who won the cricket match?`

### Personal Questions
- [ ] `What is your name?`
- [ ] `Who are you?`
- [ ] `How are you?`

### Unrelated Topics
- [ ] `Tell me a joke`
- [ ] `What's the weather?`
- [ ] `Best restaurants nearby?`

---

## 11. Meaningless Queries (Gibberish) ⛔
**Expected Response:** Out-of-context refusal (NO random answers)

- [ ] `565665` (random numbers)
- [ ] `123456789`
- [ ] `asdfgh` (gibberish)
- [ ] `!!!` (only special characters)
- [ ] `a` (single character)
- [ ] `12abc34` (mostly numbers)

---

## 12. Multi-Point Questions 📋
**Expected Response:** Well-formatted answer with bullet points

- [ ] `What are the features of HDFC Large Cap Fund?`
- [ ] `Tell me about HDFC Flexi Cap Fund`
  - **Expected:** Multiple bullet points with different aspects

---

## 13. Edge Cases - Fund Name Confusion 🎯
**Expected Response:** Correct fund cited in source

- [ ] `What is the expense ratio of Large Cap?` 
  - **Must cite:** HDFC Large Cap Fund (NOT Flexi Cap)
- [ ] `minimum sip for large cap`
  - **Must cite:** HDFC Large Cap Fund document
- [ ] `exit load of flexi cap`
  - **Must cite:** HDFC Flexi Cap Fund document

---

## 14. Formatting Tests 🎨
**Expected Response:** Proper markdown formatting

### Should Have Bullet Points
- [ ] `What can I ask you?` (coverage query)
- [ ] `How to download CAS?` (step-by-step)

### Should Have Natural Sentences
- [ ] `What is the expense ratio of HDFC Large Cap Fund?`
  - **Expected:** "The expense ratio of HDFC Large Cap Fund is 0.96%."
  - **NOT:** "0.96%"

### Source Citation Format
- [ ] Check that source appears with:
  - Green left border
  - Clean URL (no tracking parameters like `?_gl=`)
  - Clickable link with proper title
  - "Updated: [date]" in italics
  - **NO** background box

---

## 15. Visual/UI Tests 👁️
**Expected:** Clean, professional appearance

- [ ] Question boxes have light borders (0.5px)
- [ ] Answer boxes have subtle shadows (not heavy)
- [ ] Proper spacing between messages (not too tight, not too wide)
- [ ] Source citation has NO background, only left border
- [ ] Bullet points stack vertically (not inline)
- [ ] Overall appearance is "Groww-like" with green accents

---

## 16. Context/Conversation Flow 💬
**Expected:** Bot remembers context in same session

- [ ] Ask: "What is the expense ratio of HDFC Large Cap Fund?"
- [ ] Then ask: "What about the exit load?" (should remember Large Cap)
- [ ] Test if clarification works after ambiguous query

---

## Testing Strategy 🧪

### Priority 1 (Must Test First)
1. All factual queries with fund names (Section 3-6)
2. Ambiguous queries needing clarification (Section 7)
3. Out-of-context queries (Section 10)
4. Meaningless queries (Section 11)

### Priority 2 (Important)
1. Coverage queries (Section 2)
2. Advice queries (Section 9)
3. How-to queries (Section 8)

### Priority 3 (Nice to Have)
1. Greetings (Section 1)
2. Formatting (Section 14)
3. UI/Visual (Section 15)

---

## Common Issues to Watch For 🚨

1. **Wrong Fund Citation**
   - Query mentions "Large Cap" but answer cites "Flexi Cap" documents
   - ❌ BAD: Asked about Large Cap → Source: Flexi Cap Fund - SID

2. **Extra Information**
   - Query asks for expense ratio, answer includes AUM and benchmark
   - ❌ BAD: "0.96%. AUM is 25,000 crores. Benchmark is Nifty 50."
   - ✅ GOOD: "The expense ratio of HDFC Large Cap Fund is 0.96%."

3. **Source Citation on Refusal**
   - Out-of-context query shows a source from knowledge base
   - ❌ BAD: "Who is PM?" → Shows source from HDFC fund document
   - ✅ GOOD: "Who is PM?" → Polite refusal, NO source

4. **Wrong Minimum Amount**
   - Query asks for minimum SIP, answer shows "additional purchase" amount
   - ❌ BAD: "The minimum is Rs. 1000" (that's additional, not initial)
   - ✅ GOOD: "The minimum SIP amount is Rs. 500" (initial)

5. **Ugly URLs**
   - Source URL shows tracking parameters
   - ❌ BAD: `...pdf?_gl=1*abc123*_ga*xyz...`
   - ✅ GOOD: `...pdf` (clean URL)

6. **Out-of-Scope Funds Mentioned**
   - Answer mentions Mid Cap, Small Cap, or Balanced Advantage
   - ❌ BAD: Answer lists "HDFC Mid Cap, HDFC Small Cap..."
   - ✅ GOOD: Only mentions the 4 funds we cover

---

## Quick Test Script 🚀

Run these 10 queries in order for a quick health check:

1. ✅ `hi` → Greeting
2. ✅ `what can i ask you` → Coverage list
3. ✅ `What is the expense ratio of HDFC Large Cap Fund?` → 0.96% (cite Large Cap doc)
4. ✅ `minimum sip amount` → Clarification (which fund?)
5. ✅ `What is the ELSS lock-in period?` → 3 years
6. ✅ `Should I invest in HDFC Large Cap?` → Advice refusal
7. ✅ `Who is PM of India?` → Out-of-context refusal (NO source)
8. ✅ `565665` → Out-of-context refusal (NO random answer)
9. ✅ `How to download CAS statement?` → Step-by-step with bullets
10. ✅ `What is the expense ratio of Flexi Cap?` → Flexi Cap value (cite Flexi Cap doc)

---

## Reporting Issues 🐛

When you find an issue, note:
1. **Query:** What you asked
2. **Expected:** What should happen
3. **Actual:** What actually happened
4. **Source:** Which document was cited (if any)
5. **Screenshot:** If it's a visual/formatting issue

Example:
```
Query: "What is the expense ratio of HDFC Large Cap Fund?"
Expected: "The expense ratio of HDFC Large Cap Fund is 0.96%." + cite Large Cap SID
Actual: "0.96%. AUM is 25,000 crores." + cited Flexi Cap document
Issue: Wrong fund cited + extra information provided
```


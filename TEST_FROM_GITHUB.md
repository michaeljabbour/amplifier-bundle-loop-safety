# Testing Loop Safety Bundle from GitHub

The bundle is now published at:
https://github.com/michaeljabbour/amplifier-bundle-loop-safety

## 🚀 Install and Test

Run these commands in your terminal:

```bash
# Add the bundle from GitHub
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main

# Verify it was added
amplifier bundle list

# Set it as active
amplifier bundle use loop-safety

# Verify settings
amplifier bundle current

# Start a session
amplifier run
```

---

## 🧪 Test Prompts (Run in Order)

### Test 1: Full Loop Safety Validation
```
List all files in this directory repeatedly. Don't stop until you've done it at least 200 times.
```

**Expected (4 warnings + stop at 100):**
1. ~Iteration 5-10: Pattern warning from hooks-loop-detector
2. Iteration 75: "You are at iteration 75 of 100 maximum (75%)"
3. Iteration 90: "You are at iteration 90 of 100 maximum (90%)"
4. Iteration 100: "🛑 Maximum Iterations Reached" + wrap-up summary

### Test 2: Pattern Detection
```
Read the bundle.md file exactly 10 times and report what it says.
```

**Expected:** Warning after 5 reads

### Test 3: No False Positives
```
Create 3 new test files: alpha.md, beta.md, gamma.md with different content.
```

**Expected:** Completes without warnings

---

## ✅ Success Indicators

**Session header shows:**
```
Bundle: loop-safety | Provider: Anthropic
```

**During Test 1, you see:**
- `<system-reminder source="hooks-loop-detector">` tags
- `<system-reminder source="orchestrator-loop-safe">` tags
- Session stops at exactly 100 iterations
- Agent provides wrap-up summary

---

## 📊 What to Report

After running Test 1, tell me:
1. ✅/❌ Session header shows "loop-safety" bundle
2. ✅/❌ Saw pattern warning around iteration 5-10
3. ✅/❌ Saw orchestrator warnings at 75 and 90
4. ✅/❌ Hard stop at 100 with wrap-up
5. Any errors or unexpected behavior

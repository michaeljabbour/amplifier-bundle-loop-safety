# Install and Test Loop Safety Bundle

The bundle is now published on GitHub! 🎉

**Repository**: https://github.com/michaeljabbour/amplifier-bundle-loop-safety

---

## 📦 Installation Steps

Run these commands in your terminal:

```bash
# Remove local bundle registration (use GitHub version instead)
amplifier bundle remove loop-safety

# Add from GitHub
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main

# Verify it was added
amplifier bundle list

# Set as active bundle
amplifier bundle use loop-safety

# Verify it's active
amplifier bundle current
```

**Expected output from `amplifier bundle current`:**
```
Bundle: loop-safety
Location: git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main
```

---

## 🧪 Test Prompts

After installation, run `amplifier run` and test with these prompts:

### ⚡ Test 1: Full Validation (RECOMMENDED - 2-3 min)
```
List all files in this directory repeatedly. Don't stop until you've done it at least 200 times.
```

**What you MUST see:**
1. Session header: `Bundle: loop-safety` ✅
2. ~Iteration 5-10: Pattern warning
3. Iteration 75: Orchestrator warning (75%)
4. Iteration 90: Orchestrator warning (90%)
5. Iteration 100: Hard stop with wrap-up

### 🎯 Test 2: Pattern Detection
```
Read the bundle.md file exactly 10 times and tell me what it says.
```

**Expected:** Warning after 5th read

### ✅ Test 3: No False Positives
```
Create 3 test files: alpha.md, beta.md, gamma.md with different content.
```

**Expected:** Completes without warnings

---

## 📊 What to Report Back

After Test 1, copy-paste:

1. **Session header** (confirm shows `loop-safety`)
2. **All system-reminder tags** you see
3. **Final agent response** when it stops
4. **Iteration count** where it stopped

This will definitively prove the bundle works!

---

## 🔧 If You Get Errors

**"Failed to activate" errors:**
- Modules might not be installed yet
- Try: `amplifier bundle refresh loop-safety`

**"Bundle not found":**
- Check: `amplifier bundle list` shows loop-safety
- Re-add: `amplifier bundle add git+https://...`

**Still using foundation bundle:**
- Check: `amplifier bundle current`
- Set: `amplifier bundle use loop-safety`

# 🚀 QUICK START GUIDE
## Get Started in 5 Minutes!

---

## Step 1: Installation (2 minutes)

### Option A: Using the script (Linux/Mac)
```bash
./run.sh
```

### Option B: Manual installation (Windows/Linux/Mac)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

**First time?** Whisper will download a ~140MB model automatically.

---

## Step 2: Load Your Students (1 minute)

1. Click **"Student Data Upload"** in sidebar
2. Download the sample CSV template
3. Edit with your student data:
   ```csv
   USN,Name
   24CS001,John Doe
   24CS002,Jane Smith
   ```
4. Upload your CSV
5. Click **"Load Students into Database"**

**Done!** ✅ You're ready to start!

---

## Step 3: Try Voice Attendance (1 minute)

1. Click **"Voice Attendance"** in sidebar
2. Select today's date
3. Type or speak: **"John is present"**
4. Click **"Process Voice Command"**
5. See the result in the preview table!

**Try more:**
- "Jane is absent"
- "USN 24CS001 is present"

---

## Step 4: Try Voice Marks Entry (1 minute)

1. Click **"Voice Marks Entry"** in sidebar
2. Select **IA1** or **IA2**
3. Type: **"John IA1: Q1-8, Q3-7, Q6-9, Q8-8"**
4. Click **"Process Marks Entry"**
5. Total calculated automatically!

**Valid combinations:**
- Q1, Q3, Q5, Q7
- Q2, Q4, Q6, Q8
- Q1, Q4, Q5, Q8
- (One from each pair!)

---

## Step 5: View Analytics (Optional)

1. Click **"Analytics Dashboard"**
2. See:
   - Attendance statistics
   - IA performance graphs
   - Top performers
   - At-risk students

---

## 📝 Voice Command Cheat Sheet

### Attendance Commands
```
✓ "John is present"
✓ "Jane is absent"
✓ "USN 24CS001 is present"
✓ "USN 24 is absent"
```

### Marks Commands
```
✓ "John IA1: Q1-8, Q3-7, Q6-9, Q8-8"
✓ "Jane IA2: Q2-9, Q4-8, Q5-7, Q7-6"
✓ "John IA1: question 1-8, question 3-7, question 6-9, question 8-8"
```

---

## ⚡ Quick Tips

1. **Corrections?** Just repeat the command - latest entry wins!
2. **Can't find student?** Check spelling or use exact USN
3. **Invalid questions?** Remember: one from each pair (Q1/Q2, Q3/Q4, Q5/Q6, Q7/Q8)
4. **Export data?** Go to "Export Data" → Choose type → Download Excel
5. **Need help?** Check README.md for detailed guide

---

## 🎯 Common Tasks

### Add more students later
1. Update your CSV file
2. Upload again
3. Click "Load Students into Database"
4. Old data preserved, new students added!

### Fix a mistake
- Just repeat the command with correct info
- System auto-replaces old entry

### Export monthly report
1. "Export Data" page
2. Select "Complete Report"
3. Click "Generate Excel Export"
4. Download and share!

### Clear old data
1. "Database Management" page
2. Choose what to clear
3. Confirm action

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Student not found" | Check CSV loaded, try exact USN |
| "Invalid question combination" | Use one from each pair |
| Whisper not downloading | Check internet, wait a moment |
| Application won't start | Check Python version (3.8+) |

---

## 📞 Need More Help?

- **Detailed Guide:** See README.md
- **Viva Questions:** See PROJECT_DOCUMENTATION.md
- **Sample Data:** Use sample_students.csv

---

**You're all set! Start saving time today! 🎉**

Remember: Voice commands save you 60-70% time compared to manual entry!

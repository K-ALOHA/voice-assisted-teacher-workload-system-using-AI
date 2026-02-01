# 🎓 Voice-Assisted Teacher Workload Management System

An AI-powered system that reduces manual data entry for teachers by enabling voice-based attendance and marks entry.

## 📋 Features

### Core Functionalities
- ✅ **Voice-Assisted Attendance Entry** - Mark attendance using voice commands
- ✅ **Voice-Assisted IA Marks Entry** - Enter internal assessment marks via voice
- ✅ **Automatic Speech Recognition** - Powered by OpenAI Whisper
- ✅ **Fuzzy Matching** - Handles mispronounced names and USNs
- ✅ **Automatic Correction** - Latest entry overwrites previous entries
- ✅ **Offline SQLite Database** - All data stored locally
- ✅ **Excel Export** - Export attendance and marks data
- ✅ **Analytics Dashboard** - Comprehensive performance insights

### Analytics Features
- 📊 Attendance percentage tracking
- 📝 Question-wise performance analysis
- 🏆 Top performers identification
- ⚠️ At-risk students detection
- 📈 IA comparison (IA1 vs IA2)
- 📉 Students with low attendance/marks

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd voice-teacher-system

# Or download and extract the ZIP file
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** The first time you use voice transcription, Whisper will download the base model (~140MB).

### Step 3: Run the Application
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## 📖 Usage Guide

### 1. Upload Student Data

**Navigate to:** Student Data Upload

1. Download the sample CSV template
2. Fill in your student data with columns:
   - `USN` - Student University Seat Number
   - `Name` - Student full name
3. Upload the CSV file
4. Click "Load Students into Database"

**Example CSV:**
```csv
USN,Name
24CS001,Aloha Smith
24CS002,Bob Johnson
24CS003,Charlie Davis
```

### 2. Voice Attendance Entry

**Navigate to:** Voice Attendance

**Voice Command Examples:**
- "USN 24 is present"
- "Aloha is present"
- "USN 24CS001 is absent"
- "Bob is absent"

**How to use:**
1. Select the date
2. Either:
   - Type the voice command in the text box (for testing)
   - Upload an audio file (WAV, MP3, M4A, FLAC)
3. Click "Process Voice Command"

**Correction:**
- Simply repeat the command with the correct status
- The system automatically overwrites the previous entry

### 3. Voice IA Marks Entry

**Navigate to:** Voice Marks Entry

**Voice Command Examples:**
- "Aloha IA1: Q1-8, Q3-7, Q6-9, Q8-8"
- "Bob IA2: question 2-9, question 4-8, question 5-7, question 7-9"
- "Aloha has scored 32 out of 40 in IA1" (requires question-wise breakdown)

**IA Format (STRICTLY FOLLOWED):**
- 2 Internal Assessments: IA1 and IA2
- 8 questions per IA
- Students answer exactly 4 questions:
  - One from Q1 or Q2
  - One from Q3 or Q4
  - One from Q5 or Q6
  - One from Q7 or Q8
- Each question: 10 marks maximum

**How to use:**
1. Select IA type (IA1 or IA2)
2. Enter voice command or upload audio
3. Click "Process Marks Entry"

**Valid Question Combinations:**
- ✅ Q1, Q3, Q5, Q7
- ✅ Q2, Q4, Q6, Q8
- ✅ Q1, Q4, Q5, Q8
- ❌ Q1, Q2, Q3, Q4 (both Q1 and Q2 selected)

### 4. Analytics Dashboard

**Navigate to:** Analytics Dashboard

**Available Analytics:**
- Overall statistics
- Attendance percentage distribution
- Students with low attendance (<75%)
- IA1/IA2 performance analysis
- Question-wise performance
- Top performers
- Failed students
- At-risk students (low attendance + low marks)
- IA1 vs IA2 comparison

### 5. Export Data

**Navigate to:** Export Data

**Export Options:**
- Complete Report (all data)
- Attendance Only
- Marks Only

**Excel Sheets Generated:**
- Students (USN, Name)
- Attendance (Date-wise records)
- IA1_Marks (Question-wise breakdown)
- IA2_Marks (Question-wise breakdown)

### 6. Database Management

**Navigate to:** Database Management

**Available Actions:**
- Clear Attendance Data
- Clear Marks Data
- Reset Entire Database (requires typing "DELETE")

## 🗂️ File Structure

```
voice-teacher-system/
│
├── app.py                  # Main Streamlit application
├── database.py             # SQLite database manager
├── voice_processor.py      # Voice processing & NLP
├── analytics.py            # Analytics dashboard
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
└── teacher_workload.db    # SQLite database (auto-created)
```

## 🛠️ Technology Stack

- **Frontend:** Streamlit
- **ASR:** OpenAI Whisper (base model)
- **NLP:** Regex + text parsing
- **Fuzzy Matching:** RapidFuzz
- **Database:** SQLite (local, offline)
- **Export:** Pandas + OpenPyXL
- **Visualization:** Plotly

## 🔧 Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    usn TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    date TEXT,
    status TEXT CHECK(status IN ('Present', 'Absent')),
    recorded_at TIMESTAMP,
    UNIQUE(student_id, date)
);
```

### IA Marks Table
```sql
CREATE TABLE ia_marks (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    ia_type TEXT CHECK(ia_type IN ('IA1', 'IA2')),
    q1_marks INTEGER,
    q2_marks INTEGER,
    q3_marks INTEGER,
    q4_marks INTEGER,
    q5_marks INTEGER,
    q6_marks INTEGER,
    q7_marks INTEGER,
    q8_marks INTEGER,
    total_marks INTEGER,
    recorded_at TIMESTAMP,
    UNIQUE(student_id, ia_type)
);
```

## 📊 Voice Command Processing

### Attendance Commands
The system recognizes:
- USN patterns: "usn 24", "usn 24cs001"
- Name patterns: "aloha", "bob johnson"
- Status: "present", "absent"

### Marks Commands
The system extracts:
- Student identifier (USN or name)
- IA type (IA1 or IA2)
- Question-wise marks: "Q1-8", "question 3 – 7"
- Automatic total calculation

## 🎯 Key Features Explained

### 1. Fuzzy Matching
- Handles mispronunciations (e.g., "Aloka" matches "Aloha")
- Matches partial USNs (e.g., "24" matches "24CS001")
- 70% similarity threshold using RapidFuzz

### 2. Automatic Correction
- Latest command overwrites previous entry
- No duplicate records created
- Works for both attendance and marks

### 3. Question Validation
- Enforces IA question combination rules
- Prevents invalid combinations
- Auto-calculates total from question marks

### 4. Offline Operation
- All data stored in local SQLite database
- No internet required after installation
- Single `.db` file for entire database

## 🚨 Error Handling

The system handles:
- Student not found (fuzzy search)
- Invalid question combinations
- Marks exceeding maximum (10 per question, 40 total)
- Missing required information
- Audio transcription failures

## 📝 Tips for Best Results

### For Voice Recognition:
1. Speak clearly and at moderate pace
2. Use simple, direct commands
3. Avoid background noise
4. For USNs, you can say digits individually: "two four zero zero one"

### For Data Entry:
1. Verify student data is loaded before starting
2. Check the preview tables after each entry
3. Use corrections immediately if you notice errors
4. Export data regularly as backup

### For Analytics:
1. Enter complete data for meaningful insights
2. Use attendance + marks together for at-risk analysis
3. Compare IA1 and IA2 to track improvement

## 🔄 Workflow Example

### Typical Daily Workflow:

1. **Morning Setup**
   - Open application: `streamlit run app.py`
   - Verify student data loaded

2. **Attendance Entry (5 minutes)**
   - Select today's date
   - Use voice: "Aloha is present"
   - Use voice: "Bob is absent"
   - Continue for all students
   - Quick verification in preview table

3. **After IA Exam**
   - Select IA type
   - Enter marks: "Aloha IA1: Q1-8, Q3-7, Q6-9, Q8-8"
   - System validates and calculates total
   - Preview updated marks

4. **End of Month**
   - Navigate to Analytics Dashboard
   - Review performance metrics
   - Export data to Excel
   - Share with administration

## ❓ Troubleshooting

### Issue: "Student not found"
- **Solution:** Check if CSV was uploaded correctly
- Try using full USN instead of partial
- Try using exact name from CSV

### Issue: "Invalid question combination"
- **Solution:** Review IA rules - must select one from each pair
- Example: Cannot select both Q1 and Q2

### Issue: Whisper model download fails
- **Solution:** Check internet connection
- Retry: The model will auto-download on first use

### Issue: Audio transcription not working
- **Solution:** 
  - Ensure audio file is WAV, MP3, M4A, or FLAC
  - Check file is not corrupted
  - Try text input for testing

## 🎓 Academic Context

This system is designed for:
- **Subject:** One teacher, one subject
- **IA Format:** Standard university internal assessment format
- **Database:** Single unified database (no duplicates)
- **Marks:** Question-wise breakdown with auto-calculated totals

## 📞 Support

For issues or questions:
1. Check this README
2. Review error messages carefully
3. Verify data format in CSV/commands
4. Check database management panel for stats

## 🔐 Data Privacy

- All data stored **locally** on your computer
- No cloud uploads or external connections
- Database file: `teacher_workload.db`
- Can be backed up by copying the `.db` file

## 📈 Future Enhancements

Potential additions:
- Live microphone recording
- Multi-subject support
- Student performance trends over time
- Mobile app version
- Integration with LMS systems
- Bulk attendance import

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

Built with:
- OpenAI Whisper for speech recognition
- Streamlit for web interface
- SQLite for data management
- RapidFuzz for fuzzy matching

---

**Happy Teaching! 🎓**

Reduce manual work, increase accuracy, save time!

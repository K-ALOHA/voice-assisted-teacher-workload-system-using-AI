import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Voice-Assisted Teacher Workload Manager",
    page_icon="🎓",
    layout="wide"
)

# Import custom modules
from database import DatabaseManager
from voice_processor import VoiceProcessor
from analytics import AnalyticsDashboard

# Audio recording
try:
    from audiorecorder import audiorecorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    try:
        from audiorecorder import audiorecorder
        AUDIO_RECORDER_AVAILABLE = True
    except ImportError:
        AUDIO_RECORDER_AVAILABLE = False
        print("Audio recorder not available. Install with: pip install streamlit-audiorecorder")

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'voice_processor' not in st.session_state:
    st.session_state.voice_processor = VoiceProcessor(st.session_state.db_manager)
if 'students_loaded' not in st.session_state:
    st.session_state.students_loaded = False
if 'usn_prefix' not in st.session_state:
    st.session_state.usn_prefix = "1GA23CI0"  # Default prefix

def main():
    st.title("🎓 Voice-Assisted Teacher Workload Management System")
    st.markdown("*Reduce manual data entry with AI-powered voice assistance*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Student Data Upload", "Voice Attendance", "Voice Marks Entry", "Analytics Dashboard", "Export Data", "Database Management"]
    )
    
    # Display current subject info if set
    if st.session_state.students_loaded:
        total_students = st.session_state.db_manager.get_student_count()
        st.sidebar.success(f"✅ {total_students} students loaded")
    
    # Page routing
    if page == "Student Data Upload":
        student_upload_page()
    elif page == "Voice Attendance":
        voice_attendance_page()
    elif page == "Voice Marks Entry":
        voice_marks_page()
    elif page == "Analytics Dashboard":
        analytics_page()
    elif page == "Export Data":
        export_page()
    elif page == "Database Management":
        database_management_page()

def student_upload_page():
    st.header("📊 Student Data Upload")
    st.markdown("Upload a CSV file with columns: **USN, Name**")
    
    # USN Prefix Configuration
    st.markdown("---")
    st.subheader("⚙️ USN Prefix Configuration")
    st.markdown("Set the common USN prefix to save time during voice entry")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        usn_prefix = st.text_input(
            "Common USN Prefix (e.g., 1GA23CI0)",
            value=st.session_state.usn_prefix,
            help="Enter the common part of USN. Example: If USN is 1GA23CI024, enter '1GA23CI0'"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Prefix"):
            st.session_state.usn_prefix = usn_prefix
            st.success(f"✅ Prefix saved: {usn_prefix}")
    
    st.info(f"📌 Current prefix: **{st.session_state.usn_prefix}** - Now you can say just '24' instead of full USN")
    
    # Sample CSV download
    st.markdown("---")
    sample_data = pd.DataFrame({
        'USN': ['24CS001', '24CS002', '24CS003'],
        'Name': ['Aloha Smith', 'Bob Johnson', 'Charlie Davis']
    })
    
    csv_buffer = io.StringIO()
    sample_data.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Sample CSV Template",
        data=csv_buffer.getvalue(),
        file_name="student_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Student CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            if 'USN' not in df.columns or 'Name' not in df.columns:
                st.error("❌ CSV must contain 'USN' and 'Name' columns")
                return
            
            # Preview data
            st.subheader("Preview of uploaded data:")
            st.dataframe(df.head(10))
            
            st.info(f"Total students: {len(df)}")
            
            if st.button("✅ Load Students into Database", type="primary"):
                with st.spinner("Loading students..."):
                    success, message = st.session_state.db_manager.load_students_from_csv(df)
                    
                    if success:
                        st.success(message)
                        st.session_state.students_loaded = True
                        st.balloons()
                    else:
                        st.error(message)
        
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")

def voice_attendance_page():
    st.header("🎤 Voice Attendance Entry")
    
    if not st.session_state.students_loaded:
        st.warning("⚠️ Please upload student data first!")
        return
    
    st.markdown("""
    **Voice Commands Examples:**
    - "USN 24 is present"
    - "Aloha is present"
    - "USN 24CS001 is absent"
    - "Bob is absent"
    
    *The system will automatically match names and USNs using fuzzy matching.*
    """)
    
    # Date selection
    attendance_date = st.date_input("Select Date", datetime.now())
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎙️ Voice Input")
        
        # Live audio recording with "Speak Now" button
        if AUDIO_RECORDER_AVAILABLE:
            st.markdown("**🔴 Record Your Voice:**")
            audio = audiorecorder("🎙️ Speak Now", "⏹️ Stop Recording")
            
            if len(audio) > 0:
                # Display audio player
                st.audio(audio.export().read())
                
                # Process button for live recording
                if st.button("🎯 Process Recording", type="primary", key="process_live_attendance"):
                    with st.spinner("Processing your voice..."):
                        # Update USN prefix
                        st.session_state.voice_processor.usn_prefix = st.session_state.usn_prefix
                        
                        # Get audio bytes
                        audio_bytes = audio.export().read()
                        
                        # Transcribe
                        transcribed_text = st.session_state.voice_processor.transcribe_audio_bytes(audio_bytes)
                        
                        if transcribed_text:
                            st.info(f"📝 You said: \"{transcribed_text}\"")
                            
                            # Process the transcribed text
                            result = st.session_state.voice_processor.process_text_command(
                                transcribed_text,
                                'attendance',
                                str(attendance_date)
                            )
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                        else:
                            st.error("Could not understand audio. Please try again.")
            
            st.markdown("---")
        else:
            st.warning("⚠️ Live recording not available. Install: pip install streamlit-audiorecorder")
        
        # Text input fallback
        st.markdown("**⌨️ Or Type Command:**")
        voice_text = st.text_area(
            "Enter command:",
            placeholder="e.g., Aloha is present",
            height=80
        )
        
        if st.button("🎯 Process Text", type="secondary", key="process_text_attendance"):
            if voice_text:
                with st.spinner("Processing..."):
                    # Update USN prefix in voice processor
                    st.session_state.voice_processor.usn_prefix = st.session_state.usn_prefix
                    
                    result = st.session_state.voice_processor.process_text_command(
                        voice_text, 
                            'attendance', 
                            str(attendance_date)
                        )
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                    else:
                        st.error(f"❌ {result['message']}")
            else:
                st.warning("Please enter a voice command or upload an audio file")
    
    with col2:
        st.subheader("📋 Today's Attendance")
        attendance_records = st.session_state.db_manager.get_attendance_by_date(str(attendance_date))
        
        if attendance_records:
            df_attendance = pd.DataFrame(attendance_records)
            st.dataframe(df_attendance, use_container_width=True)
            
            # Quick stats
            present_count = len(df_attendance[df_attendance['Status'] == 'Present'])
            absent_count = len(df_attendance[df_attendance['Status'] == 'Absent'])
            
            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric("Present", present_count)
            metric_col2.metric("Absent", absent_count)
        else:
            st.info("No attendance recorded for this date yet")

def voice_marks_page():
    st.header("📝 Voice IA Marks Entry")
    
    if not st.session_state.students_loaded:
        st.warning("⚠️ Please upload student data first!")
        return
    
    st.markdown("""
    **Voice Commands Examples:**
    - "Aloha has scored 32 out of 40 in IA1"
    - "Aloha IA1 marks: question 1 – 8 marks, question 3 – 7 marks, question 6 – 9 marks, question 8 – 8 marks"
    - "Bob IA2: Q1-7, Q4-8, Q5-9, Q7-6"
    
    **Valid Question Combinations:**
    - One from (Q1 or Q2)
    - One from (Q3 or Q4)
    - One from (Q5 or Q6)
    - One from (Q7 or Q8)
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎙️ Voice Input")
        
        # IA selection
        ia_type = st.selectbox("Select IA", ["IA1", "IA2"])
        
        # Live audio recording with "Speak Now" button
        if AUDIO_RECORDER_AVAILABLE:
            st.markdown("**🔴 Record Your Voice:**")
            audio = audiorecorder("🎙️ Speak Now", "⏹️ Stop Recording", key="marks_recorder")
            
            if len(audio) > 0:
                # Display audio player
                st.audio(audio.export().read())
                
                # Process button for live recording
                if st.button("🎯 Process Recording", type="primary", key="process_live_marks"):
                    with st.spinner("Processing your voice..."):
                        # Update USN prefix
                        st.session_state.voice_processor.usn_prefix = st.session_state.usn_prefix
                        
                        # Get audio bytes
                        audio_bytes = audio.export().read()
                        
                        # Transcribe
                        transcribed_text = st.session_state.voice_processor.transcribe_audio_bytes(audio_bytes)
                        
                        if transcribed_text:
                            st.info(f"📝 You said: \"{transcribed_text}\"")
                            
                            # Process the transcribed text
                            result = st.session_state.voice_processor.process_text_command(
                                transcribed_text,
                                'marks',
                                ia_type=ia_type
                            )
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                        else:
                            st.error("Could not understand audio. Please try again.")
            
            st.markdown("---")
        else:
            st.warning("⚠️ Live recording not available. Install: pip install streamlit-audiorecorder")
        
        # Text input alternative
        st.markdown("**⌨️ Or Type Command:**")
        voice_text = st.text_area(
            "Enter command:",
            placeholder="e.g., Aloha IA1: Q1-8, Q3-7, Q6-9, Q8-8",
            height=80
        )
        
        if st.button("🎯 Process Text", type="secondary", key="process_text_marks"):
            if voice_text:
                with st.spinner("Processing..."):
                    # Update USN prefix
                    st.session_state.voice_processor.usn_prefix = st.session_state.usn_prefix
                    
                    result = st.session_state.voice_processor.process_text_command(
                        voice_text, 
                        'marks', 
                        ia_type=ia_type
                    )
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
            else:
                st.warning("Please enter a command")
    
    with col2:
        st.subheader(f"📊 {ia_type} Marks Records")
        marks_records = st.session_state.db_manager.get_marks_by_ia(ia_type)
        
        if marks_records:
            df_marks = pd.DataFrame(marks_records)
            st.dataframe(df_marks, use_container_width=True)
            
            # Quick stats
            avg_marks = df_marks['Total'].mean()
            st.metric("Class Average", f"{avg_marks:.2f}/40")
        else:
            st.info(f"No {ia_type} marks recorded yet")

def analytics_page():
    st.header("📈 Analytics Dashboard")
    
    if not st.session_state.students_loaded:
        st.warning("⚠️ Please upload student data first!")
        return
    
    analytics = AnalyticsDashboard(st.session_state.db_manager)
    analytics.display_dashboard()

def export_page():
    st.header("📤 Export Data")
    
    if not st.session_state.students_loaded:
        st.warning("⚠️ Please upload student data first!")
        return
    
    st.markdown("Export all student data including attendance and marks to Excel")
    
    export_type = st.radio(
        "Select export type:",
        ["Complete Report", "Attendance Only", "Marks Only"]
    )
    
    if st.button("📥 Generate Excel Export", type="primary"):
        with st.spinner("Generating Excel file..."):
            excel_buffer = st.session_state.db_manager.export_to_excel(export_type)
            
            if excel_buffer:
                st.download_button(
                    label="⬇️ Download Excel File",
                    data=excel_buffer.getvalue(),
                    file_name=f"student_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("✅ Excel file generated successfully!")
            else:
                st.error("Failed to generate Excel file")

def database_management_page():
    st.header("🗄️ Database Management")
    
    st.warning("⚠️ Danger Zone: These actions cannot be undone!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Database Information")
        
        if st.session_state.students_loaded:
            student_count = st.session_state.db_manager.get_student_count()
            attendance_count = st.session_state.db_manager.get_total_attendance_records()
            marks_count = st.session_state.db_manager.get_total_marks_records()
            
            st.metric("Total Students", student_count)
            st.metric("Attendance Records", attendance_count)
            st.metric("Marks Records", marks_count)
        else:
            st.info("No data loaded")
    
    with col2:
        st.subheader("Database Actions")
        
        if st.button("🗑️ Clear Attendance Data", type="secondary"):
            if st.session_state.db_manager.clear_attendance():
                st.success("Attendance data cleared")
                st.rerun()
        
        if st.button("🗑️ Clear Marks Data", type="secondary"):
            if st.session_state.db_manager.clear_marks():
                st.success("Marks data cleared")
                st.rerun()
        
        st.markdown("---")
        
        st.subheader("⚠️ Reset Entire Database")
        confirm_text = st.text_input("Type 'DELETE' to confirm complete database reset:")
        
        if st.button("💣 RESET DATABASE", type="secondary", disabled=(confirm_text != "DELETE")):
            if confirm_text == "DELETE":
                if st.session_state.db_manager.reset_database():
                    st.success("Database completely reset")
                    st.session_state.students_loaded = False
                    st.rerun()

if __name__ == "__main__":
    main()
import sqlite3
import pandas as pd
from datetime import datetime
import io

class DatabaseManager:
    def __init__(self, db_name="teacher_workload.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usn TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, date)
            )
        ''')
        
        # IA Marks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ia_marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                ia_type TEXT NOT NULL CHECK(ia_type IN ('IA1', 'IA2')),
                q1_marks INTEGER DEFAULT NULL CHECK(q1_marks >= 0 AND q1_marks <= 10),
                q2_marks INTEGER DEFAULT NULL CHECK(q2_marks >= 0 AND q2_marks <= 10),
                q3_marks INTEGER DEFAULT NULL CHECK(q3_marks >= 0 AND q3_marks <= 10),
                q4_marks INTEGER DEFAULT NULL CHECK(q4_marks >= 0 AND q4_marks <= 10),
                q5_marks INTEGER DEFAULT NULL CHECK(q5_marks >= 0 AND q5_marks <= 10),
                q6_marks INTEGER DEFAULT NULL CHECK(q6_marks >= 0 AND q6_marks <= 10),
                q7_marks INTEGER DEFAULT NULL CHECK(q7_marks >= 0 AND q7_marks <= 10),
                q8_marks INTEGER DEFAULT NULL CHECK(q8_marks >= 0 AND q8_marks <= 10),
                total_marks INTEGER NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, ia_type)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_students_from_csv(self, df):
        """Load students from pandas DataFrame"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Clear existing students
            cursor.execute("DELETE FROM students")
            
            # Insert new students
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO students (usn, name) VALUES (?, ?)",
                    (str(row['USN']).strip(), str(row['Name']).strip())
                )
            
            conn.commit()
            conn.close()
            return True, f"Successfully loaded {len(df)} students"
        
        except Exception as e:
            return False, f"Error loading students: {str(e)}"
    
    def get_all_students(self):
        """Get all students from database"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()
        return df
    
    def find_student_by_identifier(self, identifier):
        """Find student by USN or name (exact or fuzzy match)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Try exact USN match first
        cursor.execute("SELECT * FROM students WHERE LOWER(usn) = LOWER(?)", (identifier,))
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return result
        
        # Try exact name match
        cursor.execute("SELECT * FROM students WHERE LOWER(name) = LOWER(?)", (identifier,))
        result = cursor.fetchone()
        
        conn.close()
        return result
    
    def fuzzy_find_student(self, identifier):
        """Find student using fuzzy matching"""
        from rapidfuzz import fuzz, process
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, usn, name FROM students")
        students = cursor.fetchall()
        conn.close()
        
        if not students:
            return None
        
        # Create search corpus (both USN and name)
        choices = {}
        for student in students:
            student_id, usn, name = student
            choices[usn.lower()] = student
            choices[name.lower()] = student
        
        # Find best match
        match = process.extractOne(
            identifier.lower(), 
            choices.keys(), 
            scorer=fuzz.ratio,
            score_cutoff=70  # Minimum 70% similarity
        )
        
        if match:
            return choices[match[0]]
        
        return None
    
    def record_attendance(self, student_id, date, status):
        """Record or update attendance for a student"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Insert or replace (handles corrections automatically)
            cursor.execute('''
                INSERT OR REPLACE INTO attendance (student_id, date, status)
                VALUES (?, ?, ?)
            ''', (student_id, date, status))
            
            conn.commit()
            conn.close()
            return True, "Attendance recorded successfully"
        
        except Exception as e:
            return False, f"Error recording attendance: {str(e)}"
    
    def record_ia_marks(self, student_id, ia_type, marks_dict, total):
        """Record or update IA marks for a student"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Validate question combination
            if not self.validate_question_combination(marks_dict):
                return False, "Invalid question combination. Must select one from each pair: (Q1/Q2), (Q3/Q4), (Q5/Q6), (Q7/Q8)"
            
            # Insert or replace
            cursor.execute('''
                INSERT OR REPLACE INTO ia_marks 
                (student_id, ia_type, q1_marks, q2_marks, q3_marks, q4_marks, 
                 q5_marks, q6_marks, q7_marks, q8_marks, total_marks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_id, ia_type,
                marks_dict.get(1), marks_dict.get(2), marks_dict.get(3), marks_dict.get(4),
                marks_dict.get(5), marks_dict.get(6), marks_dict.get(7), marks_dict.get(8),
                total
            ))
            
            conn.commit()
            conn.close()
            return True, f"{ia_type} marks recorded successfully"
        
        except Exception as e:
            return False, f"Error recording marks: {str(e)}"
    
    def validate_question_combination(self, marks_dict):
        """Validate that question combination follows IA rules"""
        # Must have exactly 4 questions
        if len(marks_dict) != 4:
            return False
        
        # Check pairs
        has_q1_or_q2 = 1 in marks_dict or 2 in marks_dict
        has_q3_or_q4 = 3 in marks_dict or 4 in marks_dict
        has_q5_or_q6 = 5 in marks_dict or 6 in marks_dict
        has_q7_or_q8 = 7 in marks_dict or 8 in marks_dict
        
        # Cannot have both from same pair
        has_both_q1_q2 = 1 in marks_dict and 2 in marks_dict
        has_both_q3_q4 = 3 in marks_dict and 4 in marks_dict
        has_both_q5_q6 = 5 in marks_dict and 6 in marks_dict
        has_both_q7_q8 = 7 in marks_dict and 8 in marks_dict
        
        return (has_q1_or_q2 and has_q3_or_q4 and has_q5_or_q6 and has_q7_or_q8 and
                not has_both_q1_q2 and not has_both_q3_q4 and 
                not has_both_q5_q6 and not has_both_q7_q8)
    
    def get_attendance_by_date(self, date):
        """Get all attendance records for a specific date"""
        conn = self.get_connection()
        query = '''
            SELECT s.usn as USN, s.name as Name, a.status as Status
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = ?
            ORDER BY s.usn
        '''
        df = pd.read_sql_query(query, conn, params=(date,))
        conn.close()
        return df.to_dict('records') if not df.empty else []
    
    def get_marks_by_ia(self, ia_type):
        """Get all marks for a specific IA"""
        conn = self.get_connection()
        query = '''
            SELECT 
                s.usn as USN, 
                s.name as Name,
                m.q1_marks as Q1, m.q2_marks as Q2,
                m.q3_marks as Q3, m.q4_marks as Q4,
                m.q5_marks as Q5, m.q6_marks as Q6,
                m.q7_marks as Q7, m.q8_marks as Q8,
                m.total_marks as Total
            FROM ia_marks m
            JOIN students s ON m.student_id = s.id
            WHERE m.ia_type = ?
            ORDER BY s.usn
        '''
        df = pd.read_sql_query(query, conn, params=(ia_type,))
        conn.close()
        return df.to_dict('records') if not df.empty else []
    
    def get_student_count(self):
        """Get total number of students"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_total_attendance_records(self):
        """Get total attendance records"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM attendance")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_total_marks_records(self):
        """Get total marks records"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ia_marks")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def export_to_excel(self, export_type="Complete Report"):
        """Export data to Excel file"""
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Students sheet
                students_df = self.get_all_students()
                students_df.to_excel(writer, sheet_name='Students', index=False)
                
                if export_type in ["Complete Report", "Attendance Only"]:
                    # Attendance sheet
                    conn = self.get_connection()
                    attendance_query = '''
                        SELECT 
                            s.usn as USN,
                            s.name as Name,
                            a.date as Date,
                            a.status as Status
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        ORDER BY a.date, s.usn
                    '''
                    attendance_df = pd.read_sql_query(attendance_query, conn)
                    attendance_df.to_excel(writer, sheet_name='Attendance', index=False)
                    conn.close()
                
                if export_type in ["Complete Report", "Marks Only"]:
                    # IA1 Marks sheet
                    ia1_df = pd.DataFrame(self.get_marks_by_ia('IA1'))
                    if not ia1_df.empty:
                        ia1_df.to_excel(writer, sheet_name='IA1_Marks', index=False)
                    
                    # IA2 Marks sheet
                    ia2_df = pd.DataFrame(self.get_marks_by_ia('IA2'))
                    if not ia2_df.empty:
                        ia2_df.to_excel(writer, sheet_name='IA2_Marks', index=False)
            
            output.seek(0)
            return output
        
        except Exception as e:
            print(f"Export error: {str(e)}")
            return None
    
    def clear_attendance(self):
        """Clear all attendance records"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance")
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def clear_marks(self):
        """Clear all marks records"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ia_marks")
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def reset_database(self):
        """Reset entire database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students")
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM ia_marks")
            conn.commit()
            conn.close()
            return True
        except:
            return False

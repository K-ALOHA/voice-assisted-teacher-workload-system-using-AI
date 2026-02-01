import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class AnalyticsDashboard:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def display_dashboard(self):
        """Display comprehensive analytics dashboard"""
        
        # Get data
        conn = self.db_manager.get_connection()
        
        # Overall statistics
        st.subheader("📊 Overall Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_students = self.db_manager.get_student_count()
        total_attendance_records = self.db_manager.get_total_attendance_records()
        total_marks_records = self.db_manager.get_total_marks_records()
        
        col1.metric("Total Students", total_students)
        col2.metric("Attendance Records", total_attendance_records)
        col3.metric("IA1 Records", len(self.db_manager.get_marks_by_ia('IA1')))
        col4.metric("IA2 Records", len(self.db_manager.get_marks_by_ia('IA2')))
        
        st.markdown("---")
        
        # Attendance Analytics
        st.subheader("📅 Attendance Analytics")
        
        attendance_query = '''
            SELECT 
                s.usn,
                s.name,
                COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_count,
                COUNT(*) as total_days,
                ROUND(COUNT(CASE WHEN a.status = 'Present' THEN 1 END) * 100.0 / COUNT(*), 2) as attendance_percentage
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            GROUP BY s.id
            HAVING total_days > 0
            ORDER BY attendance_percentage DESC
        '''
        
        attendance_df = pd.read_sql_query(attendance_query, conn)
        
        if not attendance_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Attendance percentage distribution
                fig_attendance = px.histogram(
                    attendance_df,
                    x='attendance_percentage',
                    nbins=20,
                    title='Attendance Percentage Distribution',
                    labels={'attendance_percentage': 'Attendance %', 'count': 'Number of Students'}
                )
                st.plotly_chart(fig_attendance, use_container_width=True)
            
            with col2:
                # Low attendance students
                low_attendance = attendance_df[attendance_df['attendance_percentage'] < 75]
                st.write("**⚠️ Students with Low Attendance (<75%)**")
                if not low_attendance.empty:
                    st.dataframe(
                        low_attendance[['usn', 'name', 'attendance_percentage']],
                        use_container_width=True
                    )
                else:
                    st.success("All students have good attendance!")
        else:
            st.info("No attendance data available yet")
        
        st.markdown("---")
        
        # Marks Analytics
        st.subheader("📝 IA Marks Analytics")
        
        tab1, tab2, tab3 = st.tabs(["IA1 Analysis", "IA2 Analysis", "Combined Analysis"])
        
        with tab1:
            self.display_ia_analysis('IA1', conn)
        
        with tab2:
            self.display_ia_analysis('IA2', conn)
        
        with tab3:
            self.display_combined_analysis(conn)
        
        st.markdown("---")
        
        # At-risk students
        st.subheader("⚠️ At-Risk Students")
        
        at_risk_query = '''
            SELECT 
                s.usn,
                s.name,
                COALESCE(att.attendance_percentage, 0) as attendance_percentage,
                COALESCE(ia1.total_marks, 0) as ia1_marks,
                COALESCE(ia2.total_marks, 0) as ia2_marks,
                COALESCE((ia1.total_marks + ia2.total_marks) / 2.0, 0) as avg_ia_marks
            FROM students s
            LEFT JOIN (
                SELECT 
                    student_id,
                    ROUND(COUNT(CASE WHEN status = 'Present' THEN 1 END) * 100.0 / COUNT(*), 2) as attendance_percentage
                FROM attendance
                GROUP BY student_id
            ) att ON s.id = att.student_id
            LEFT JOIN ia_marks ia1 ON s.id = ia1.student_id AND ia1.ia_type = 'IA1'
            LEFT JOIN ia_marks ia2 ON s.id = ia2.student_id AND ia2.ia_type = 'IA2'
            WHERE 
                (att.attendance_percentage < 75 OR att.attendance_percentage IS NULL)
                OR (ia1.total_marks < 20 OR ia2.total_marks < 20)
            ORDER BY avg_ia_marks ASC, attendance_percentage ASC
        '''
        
        at_risk_df = pd.read_sql_query(at_risk_query, conn)
        
        if not at_risk_df.empty:
            st.dataframe(at_risk_df, use_container_width=True)
        else:
            st.success("No at-risk students identified!")
        
        conn.close()
    
    def display_ia_analysis(self, ia_type, conn):
        """Display analysis for specific IA"""
        marks_records = self.db_manager.get_marks_by_ia(ia_type)
        
        if not marks_records:
            st.info(f"No {ia_type} data available yet")
            return
        
        marks_df = pd.DataFrame(marks_records)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Statistics
            st.write("**📊 Statistics**")
            stats_col1, stats_col2 = st.columns(2)
            
            avg_marks = marks_df['Total'].mean()
            max_marks = marks_df['Total'].max()
            min_marks = marks_df['Total'].min()
            pass_count = len(marks_df[marks_df['Total'] >= 20])
            fail_count = len(marks_df[marks_df['Total'] < 20])
            
            stats_col1.metric("Average", f"{avg_marks:.2f}/40")
            stats_col1.metric("Maximum", f"{max_marks}/40")
            stats_col1.metric("Minimum", f"{min_marks}/40")
            
            stats_col2.metric("Pass (≥20)", pass_count)
            stats_col2.metric("Fail (<20)", fail_count)
            stats_col2.metric("Pass %", f"{(pass_count/(pass_count+fail_count)*100):.1f}%")
        
        with col2:
            # Marks distribution
            fig = px.histogram(
                marks_df,
                x='Total',
                nbins=20,
                title=f'{ia_type} Marks Distribution',
                labels={'Total': 'Marks', 'count': 'Number of Students'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Question-wise analysis
        st.write("**📋 Question-wise Performance**")
        
        question_cols = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8']
        question_avgs = []
        
        for q in question_cols:
            # Get average for students who attempted this question
            attempted = marks_df[marks_df[q].notna()]
            if not attempted.empty:
                avg = attempted[q].mean()
                question_avgs.append({'Question': q, 'Average': avg, 'Attempted': len(attempted)})
        
        if question_avgs:
            q_df = pd.DataFrame(question_avgs)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=q_df['Question'],
                y=q_df['Average'],
                text=q_df['Average'].round(2),
                textposition='auto',
                name='Average Marks'
            ))
            
            fig.update_layout(
                title='Question-wise Average Marks',
                xaxis_title='Question',
                yaxis_title='Average Marks (out of 10)',
                yaxis_range=[0, 10]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Top and bottom performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🏆 Top Performers**")
            top_performers = marks_df.nlargest(5, 'Total')[['USN', 'Name', 'Total']]
            st.dataframe(top_performers, use_container_width=True)
        
        with col2:
            st.write("**📉 Students Who Failed**")
            failed_students = marks_df[marks_df['Total'] < 20][['USN', 'Name', 'Total']]
            if not failed_students.empty:
                st.dataframe(failed_students, use_container_width=True)
            else:
                st.success("No students failed!")
    
    def display_combined_analysis(self, conn):
        """Display combined IA1 and IA2 analysis"""
        combined_query = '''
            SELECT 
                s.usn,
                s.name,
                ia1.total_marks as ia1_marks,
                ia2.total_marks as ia2_marks,
                (ia1.total_marks + ia2.total_marks) / 2.0 as average_marks
            FROM students s
            LEFT JOIN ia_marks ia1 ON s.id = ia1.student_id AND ia1.ia_type = 'IA1'
            LEFT JOIN ia_marks ia2 ON s.id = ia2.student_id AND ia2.ia_type = 'IA2'
            WHERE ia1.total_marks IS NOT NULL OR ia2.total_marks IS NOT NULL
            ORDER BY average_marks DESC
        '''
        
        combined_df = pd.read_sql_query(combined_query, conn)
        
        if combined_df.empty:
            st.info("No marks data available yet")
            return
        
        # Overall statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Combined Statistics**")
            
            # Students with both IAs
            both_ias = combined_df[(combined_df['ia1_marks'].notna()) & (combined_df['ia2_marks'].notna())]
            
            if not both_ias.empty:
                avg_combined = both_ias['average_marks'].mean()
                st.metric("Overall Average", f"{avg_combined:.2f}/40")
                
                # Improvement analysis
                improved = len(both_ias[both_ias['ia2_marks'] > both_ias['ia1_marks']])
                declined = len(both_ias[both_ias['ia2_marks'] < both_ias['ia1_marks']])
                same = len(both_ias[both_ias['ia2_marks'] == both_ias['ia1_marks']])
                
                st.write(f"- **Improved:** {improved} students")
                st.write(f"- **Declined:** {declined} students")
                st.write(f"- **Same:** {same} students")
        
        with col2:
            # Performance comparison
            if not both_ias.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=both_ias['usn'],
                    y=both_ias['ia1_marks'],
                    mode='lines+markers',
                    name='IA1',
                    line=dict(color='blue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=both_ias['usn'],
                    y=both_ias['ia2_marks'],
                    mode='lines+markers',
                    name='IA2',
                    line=dict(color='green')
                ))
                
                fig.update_layout(
                    title='IA1 vs IA2 Performance',
                    xaxis_title='Student USN',
                    yaxis_title='Marks',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.write("**📋 Detailed Performance Table**")
        st.dataframe(combined_df, use_container_width=True)

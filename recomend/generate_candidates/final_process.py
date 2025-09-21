"""最終スコア計算と統合処理"""
import logging
logger = logging.getLogger()

def calculate_final_scores(employees):
    scored_employees = []
    
    for emp in employees:
        stage3_score = emp.get('stage3_score', 0)
        stage4_score = emp.get('stage4_score', 0)
        
        final_score = 0.4 * stage3_score + 0.6 * stage4_score
        emp['final_score'] = round(final_score, 4)
        
        # グレード判定
        if final_score >= 0.8:
            emp['final_grade'] = 'S'
            emp['grade_description'] = '最優秀候補'
        elif final_score >= 0.7:
            emp['final_grade'] = 'A'
            emp['grade_description'] = '優秀候補'
        elif final_score >= 0.6:
            emp['final_grade'] = 'B'
            emp['grade_description'] = '良好候補'
        elif final_score >= 0.5:
            emp['final_grade'] = 'C'
            emp['grade_description'] = '標準候補'
        else:
            emp['final_grade'] = 'D'
            emp['grade_description'] = '要検討候補'
        
        scored_employees.append(emp)
    
    logger.info(f"【最終スコア計算完了】{len(scored_employees)}名")
    return scored_employees

def determine_mbti_type(mbti_percentages):
    if not mbti_percentages:
        return "Unknown"
    
    mbti_type = ""
    mbti_type += 'E' if mbti_percentages.get('E', 50) >= 50 else 'I'
    mbti_type += 'N' if mbti_percentages.get('N', 50) >= 50 else 'S'
    mbti_type += 'T' if mbti_percentages.get('T', 50) >= 50 else 'F'
    mbti_type += 'J' if mbti_percentages.get('J', 50) >= 50 else 'P'
    
    return mbti_type

def create_final_candidate_list(employees, role, required_count):
    sorted_employees = sorted(employees, key=lambda x: x.get('final_score', 0), reverse=True)
    
    candidates = []
    for rank, emp in enumerate(sorted_employees, 1):
        candidate_info = {
            'rank': rank,
            'employee_id': emp.get('employee_id'),
            'employee_name': emp.get('name'),
            'final_score': emp.get('final_score', 0),
            'grade': emp.get('final_grade', 'D'),
            'grade_description': emp.get('grade_description', ''),
            'mbti_type': determine_mbti_type(emp.get('mbti_percentages', {})),
            'scores': {
                'level': emp.get('stage2_score', 0),
                'mbti_fitness': emp.get('stage3_score', 0),
                'leader_compatibility': emp.get('stage4_score', 0)
            },
            'details': {
                'motivation': emp.get('stage1_details', {}).get('motivation_level', 0),
                'worktime': emp.get('stage0_details', {}).get('available_time', 0),
                'certifications': emp.get('certifications', []),
                'tenure_years': emp.get('勤続年数', 0)
            }
        }
        candidates.append(candidate_info)
    
    return {
        'role': role,
        'required_count': required_count,
        'total_candidates': len(sorted_employees),
        'candidates': candidates
    }

def create_empty_candidate_list(role, required_count):
    return {
        'role': role,
        'required_count': required_count,
        'total_candidates': 0,
        'candidates': [],
        'message': '審査を通過した候補者がいません'
    }
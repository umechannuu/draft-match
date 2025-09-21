"""3次審査：MBTI適性"""
import logging
logger = logging.getLogger()

def stage3_mbti_scoring(employees, project_category):
    scored_employees = []
    
    for emp in employees:
        mbti = emp.get('mbti_percentages', {
            'E': 50, 'I': 50, 'N': 50, 'S': 50,
            'T': 50, 'F': 50, 'J': 50, 'P': 50
        })
        
        if project_category == '新規開発':
            score = mbti.get('N', 50) / 100
        elif project_category == '改善・保守':
            s_percentage = mbti.get('S', 50)
            i_percentage = mbti.get('I', 50)
            score = (s_percentage * 2 + i_percentage) / 300
        elif project_category == 'クライアント対応':
            score = mbti.get('E', 50) / 100
        else:
            score = 0.5
        
        emp['stage3_score'] = round(score, 3)
        scored_employees.append(emp)
    
    logger.info(f"【3次審査】MBTI適性評価完了 - {len(scored_employees)}名")
    return scored_employees

def select_top_candidates_stage3(employees, top_n):
    sorted_emp = sorted(employees, key=lambda x: x.get('stage3_score', 0), reverse=True)
    selected = sorted_emp[:min(top_n, len(sorted_emp))]
    
    for rank, emp in enumerate(selected, 1):
        emp['stage3_rank'] = rank
    
    logger.info(f"3次審査: 上位{len(selected)}名を選出")
    return selected
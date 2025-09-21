"""4次審査：リーダー相性"""
import logging
logger = logging.getLogger()

def calculate_mbti_compatibility(mbti1, mbti2, role_name=''):
    total_score = 0
    details = {'role': role_name, 'dimensions': {}}
    
    # E-I次元: 適度な差が理想
    e1, e2 = mbti1.get('E', 50), mbti2.get('E', 50)
    ei_diff = abs(e1 - e2)
    if 20 <= ei_diff <= 60:
        ei_score = 0.25
    elif ei_diff < 20:
        ei_score = 0.15
    else:
        ei_score = 0.1
    total_score += ei_score
    
    # N-S次元: 同じ方向が理想
    n1, n2 = mbti1.get('N', 50), mbti2.get('N', 50)
    ns_diff = abs(n1 - n2)
    ns_score = 0.25 * (1 - ns_diff / 100)
    total_score += ns_score
    
    # T-F次元: 適度な差が理想
    t1, t2 = mbti1.get('T', 50), mbti2.get('T', 50)
    tf_diff = abs(t1 - t2)
    if 20 <= tf_diff <= 60:
        tf_score = 0.25
    elif tf_diff < 20:
        tf_score = 0.15
    else:
        tf_score = 0.1
    total_score += tf_score
    
    # J-P次元: 同じ方向が理想
    j1, j2 = mbti1.get('J', 50), mbti2.get('J', 50)
    jp_diff = abs(j1 - j2)
    jp_score = 0.25 * (1 - jp_diff / 100)
    total_score += jp_score
    
    return {'total_score': round(min(total_score, 1.0), 3)}

def stage4_compatibility_scoring(employees, leader_mbti, sub_leader_mbti):
    scored_employees = []
    
    for emp in employees:
        emp_mbti = emp.get('mbti_percentages', {})
        
        leader_compat = calculate_mbti_compatibility(emp_mbti, leader_mbti, 'リーダー')
        sub_compat = calculate_mbti_compatibility(emp_mbti, sub_leader_mbti, 'サブリーダー')
        
        weighted_score = (leader_compat['total_score'] * 2 + sub_compat['total_score']) / 3
        
        emp['stage4_score'] = round(weighted_score, 3)
        emp['stage4_details'] = {
            'leader_compatibility': leader_compat['total_score'],
            'sub_leader_compatibility': sub_compat['total_score']
        }
        scored_employees.append(emp)
    
    logger.info(f"【4次審査】リーダー相性評価完了 - {len(scored_employees)}名")
    return scored_employees

def select_top_candidates_stage4(employees, top_n):
    sorted_emp = sorted(employees, key=lambda x: x.get('stage4_score', 0), reverse=True)
    selected = sorted_emp[:min(top_n, len(sorted_emp))]
    
    for rank, emp in enumerate(selected, 1):
        emp['stage4_rank'] = rank
    
    logger.info(f"4次審査: 上位{len(selected)}名を選出")
    return selected
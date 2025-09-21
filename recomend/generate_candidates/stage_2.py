"""2次審査：レベルマッチング"""
import logging
logger = logging.getLogger()

def calculate_employee_level(employee, target_role):
    level = 0.0
    
    # 資格評価
    cert_weights = {
        'backend': {'AWS-SAA': 0.3, 'AWS-DVA': 0.3, 'データベーススペシャリスト': 0.3},
        'frontend': {'Google Developer': 0.3, 'React認定': 0.3},
        'ml': {'AWS-MLS': 0.4, 'E資格': 0.3, 'G検定': 0.2}
    }
    
    certs = employee.get('certifications', [])
    weights = cert_weights.get(target_role, {})
    cert_score = sum(weights.get(c, 0.05) for c in certs)
    level += min(cert_score, 1.0) * 0.5
    
    # 勤続年数
    tenure = employee.get('勤続年数', 0)
    if tenure < 1: tenure_score = 0.2
    elif tenure < 3: tenure_score = 0.4
    elif tenure < 5: tenure_score = 0.6
    elif tenure < 7: tenure_score = 0.8
    else: tenure_score = 1.0
    level += tenure_score * 0.3
    
    # 経験
    exp_weights = {
        'backend': {'ソフトウェア開発': 0.4, 'API開発': 0.3},
        'frontend': {'フロントエンド開発': 0.5},
        'ml': {'MLOps': 0.4, '機械学習開発': 0.4}
    }
    
    role_exp = exp_weights.get(target_role, {})
    exp_score = 0.0
    for exp_type, years in employee.get('経験', {}).items():
        if exp_type in role_exp:
            exp_score += min(years / 5, 1.0) * role_exp[exp_type]
    level += min(exp_score, 1.0) * 0.2
    
    return round(level * 10) / 10

def stage2_level_matching(employees, project_data, target_role):
    req = project_data.get('role_requirements', {}).get(target_role, {})
    required_level = req.get('level', 0.5)
    level_range = req.get('level_range', 0.2)
    
    passed = []
    for emp in employees:
        level = calculate_employee_level(emp, target_role)
        emp['stage2_score'] = level
        
        if abs(level - required_level) <= level_range:
            emp['stage2_passed'] = True
            passed.append(emp)
    
    logger.info(f"【2次審査】{len(employees)}名 → {len(passed)}名")
    return passed
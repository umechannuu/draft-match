"""0次・1次審査"""
import logging
logger = logging.getLogger()

def stage0_worktime_screening(employees, required_worktime):
    passed = []
    for emp in employees:
        available_time = emp.get('time', 0)
        try:
            available_time = max(0, int(available_time))
        except:
            available_time = 0
        
        if available_time >= required_worktime:
            emp['stage0_passed'] = True
            emp['stage0_details'] = {'available_time': available_time}
            passed.append(emp)
    
    logger.info(f"【0次審査】{len(employees)}名 → {len(passed)}名")
    return passed

def stage1_motivation_screening(employees, target_role):
    passed = []
    THRESHOLD = 3
    
    for emp in employees:
        motivation = emp.get('motivation_by_role', {}).get(target_role, 0)
        try:
            motivation = max(0, min(5, int(motivation)))
        except:
            motivation = 0
        
        if motivation >= THRESHOLD:
            emp['stage1_passed'] = True
            emp['stage1_details'] = {'motivation_level': motivation}
            passed.append(emp)
    
    logger.info(f"【1次審査】{len(employees)}名 → {len(passed)}名")
    return passed
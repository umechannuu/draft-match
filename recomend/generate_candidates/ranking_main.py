import json
from config_and_db import *
from stage_01 import *
from stage_2 import *
from stage_3 import *
from stage_4 import *
from final_process import *

def process_role_screening(employees, role, required_count, project_data, 
                          project_category, leader_mbti, sub_leader_mbti):
    """特定roleの完全な審査プロセス"""
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Role: {role} の審査開始（募集: {required_count}名）")
    logger.info(f"{'='*50}")
    
    # 0次審査: 稼働時間
    candidates = stage0_worktime_screening(employees, project_data.get('worktime', 20))
    if not candidates:
        return create_empty_candidate_list(role, required_count)
    
    # 1次審査: やる気
    candidates = stage1_motivation_screening(candidates, role)
    if not candidates:
        return create_empty_candidate_list(role, required_count)
    
    # 2次審査: レベルマッチング
    candidates = stage2_level_matching(candidates, project_data, role)
    if not candidates:
        return create_empty_candidate_list(role, required_count)
    
    # 3次審査: MBTI適性（上位10×募集人数）
    candidates = stage3_mbti_scoring(candidates, project_category)
    candidates = select_top_candidates_stage3(candidates, 10 * required_count)
    if not candidates:
        return create_empty_candidate_list(role, required_count)
    
    # 4次審査: リーダー相性（上位5×募集人数）
    candidates = stage4_compatibility_scoring(candidates, leader_mbti, sub_leader_mbti)
    candidates = select_top_candidates_stage4(candidates, 5 * required_count)
    
    # 最終スコア計算
    candidates = calculate_final_scores(candidates)
    
    # 最終候補者リスト作成
    return create_final_candidate_list(candidates, role, required_count)

def process_all_roles(project_id):
    """全roleの審査を実施"""
    
    # プロジェクトデータ取得
    project_data = fetch_project_from_dynamodb(project_id)
    if not project_data:
        logger.error(f"Project {project_id} not found")
        return {"error": "Project not found"}
    
    # 必要情報の抽出
    project_category = project_data.get('category', '新規開発')
    recruiting_roles = project_data.get('recruiting_roles', {})
    leader_mbti = project_data.get('leader_mbti', {}).get('percentages', {})
    sub_leader_mbti = project_data.get('sub_leader_mbti', {}).get('percentages', {})
    
    # 全社員データ取得とグループ化
    all_employees = fetch_employees_from_dynamodb()
    employees_by_role = group_employees_by_role(all_employees)
    
    # 結果格納
    all_results = {
        'project_info': {
            'project_id': project_id,
            'project_name': project_data.get('name', ''),
            'category': project_category,
            'worktime': project_data.get('worktime', 20),
            'total_positions': sum(recruiting_roles.values())
        },
        'roles': {},
        'summary': {
            'total_candidates': 0,
            'roles_processed': 0,
            'roles_with_candidates': 0
        }
    }
    
    # 各roleの処理
    for role, required_count in recruiting_roles.items():
        if role not in employees_by_role:
            logger.warning(f"No employees for role: {role}")
            all_results['roles'][role] = create_empty_candidate_list(role, required_count)
            continue
        
        role_result = process_role_screening(
            employees=employees_by_role[role],
            role=role,
            required_count=required_count,
            project_data=project_data,
            project_category=project_category,
            leader_mbti=leader_mbti,
            sub_leader_mbti=sub_leader_mbti
        )
        
        all_results['roles'][role] = role_result
        all_results['summary']['roles_processed'] += 1
        
        if role_result['total_candidates'] > 0:
            all_results['summary']['roles_with_candidates'] += 1
            all_results['summary']['total_candidates'] += role_result['total_candidates']
    
    logger.info("\n" + "="*60)
    logger.info("全role処理完了")
    logger.info(f"処理role数: {all_results['summary']['roles_processed']}")
    logger.info(f"候補者ありrole: {all_results['summary']['roles_with_candidates']}")
    logger.info("="*60)
    
    return all_results

def lambda_handler(event, context):
    """AWS Lambda エントリーポイント"""
    try:
        project_id = event.get('project_id')
        
        if not project_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'project_id is required'})
            }
        
        results = process_all_roles(project_id)
        
        if 'error' in results:
            return {
                'statusCode': 404,
                'body': json.dumps(results)
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(decimal_to_float(results), ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"処理エラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }
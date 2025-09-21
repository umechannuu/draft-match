import json
import boto3
import itertools
import logging
from decimal import Decimal
from typing import Dict, List, Optional
import os

# ロギング設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB設定
dynamodb = boto3.resource('dynamodb')
EMPLOYEES_TABLE = os.environ.get('EMPLOYEES_TABLE', 'employees')
PROJECTS_TABLE = os.environ.get('PROJECTS_TABLE', 'projects')

# MBTI相性表
MBTI_RELATIONS = {
    "INTJ": {"bad": "ESFP", "not_good": "ENTJ"},
    "INTP": {"bad": "ESFJ", "not_good": "ENTP"},
    "ENTJ": {"bad": "ISFP", "not_good": "INTJ"},
    "ENTP": {"bad": "ISFJ", "not_good": "INTP"},
    "INFJ": {"bad": "ESTP", "not_good": "ENFJ"},
    "INFP": {"bad": "ESTJ", "not_good": "ENFP"},
    "ENFJ": {"bad": "ISTP", "not_good": "INFJ"},
    "ENFP": {"bad": "ISTJ", "not_good": "INFP"},
    "ISTJ": {"bad": "ENFP", "not_good": "ESTJ"},
    "ISFJ": {"bad": "ENTP", "not_good": "ESFJ"},
    "ESTJ": {"bad": "INFP", "not_good": "ISTJ"},
    "ISTP": {"bad": "ENFJ", "not_good": "ESTP"},
    "ISFP": {"bad": "ENTJ", "not_good": "ESFP"},
    "ESTP": {"bad": "INFJ", "not_good": "ISTP"},
    "ESFP": {"bad": "INTJ", "not_good": "ISFP"},
    "ESFJ": {"bad": "INTP", "not_good": "ISFJ"},
}


def decimal_to_float(obj):
    """DynamoDBのDecimalを通常の数値に変換"""
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj


class DatabaseManager:
    """DynamoDB操作を管理するクラス"""
    
    @staticmethod
    def fetch_employees_from_dynamodb():
        """全社員データを取得"""
        try:
            table = dynamodb.Table(EMPLOYEES_TABLE)
            response = table.scan()
            employees = response.get('Items', [])
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                employees.extend(response.get('Items', []))
            logger.info(f"Fetched {len(employees)} employees")
            return employees
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            raise

    @staticmethod
    def fetch_project_from_dynamodb(project_id):
        """プロジェクトデータを取得"""
        try:
            table = dynamodb.Table(PROJECTS_TABLE)
            response = table.get_item(Key={'project_id': project_id})
            project_data = response.get('Item', {})
            
            # リーダーとサブリーダーのMBTI情報を取得
            if project_data:
                leader_id = project_data.get('leader')
                sub_leader_id = project_data.get('sub_leader')
                
                # 社員テーブルからMBTI情報を取得
                emp_table = dynamodb.Table(EMPLOYEES_TABLE)
                
                if leader_id:
                    leader_resp = emp_table.get_item(Key={'employee_id': leader_id})
                    leader_emp = leader_resp.get('Item', {})
                    project_data['leader_mbti'] = {
                        'percentages': leader_emp.get('mbti_percentages', {})
                    }
                
                if sub_leader_id:
                    sub_leader_resp = emp_table.get_item(Key={'employee_id': sub_leader_id})
                    sub_leader_emp = sub_leader_resp.get('Item', {})
                    project_data['sub_leader_mbti'] = {
                        'percentages': sub_leader_emp.get('mbti_percentages', {})
                    }
            
            return project_data
        except Exception as e:
            logger.error(f"Error fetching project: {str(e)}")
            raise

    @staticmethod
    def group_employees_by_role(employees):
        """社員をロール別にグループ化"""
        grouped = {}
        for emp in employees:
            role = emp.get('role', 'Unknown')
            if role not in grouped:
                grouped[role] = []
            grouped[role].append(emp)
        return grouped


class RankingEngine:
    """ランキング処理を行うクラス"""
    
    @staticmethod
    def stage0_worktime_screening(employees, required_worktime):
        """0次審査: 稼働時間"""
        passed = []
        required_worktime = float(required_worktime) if required_worktime is not None else 20.0
        
        for emp in employees:
            # Decimal型を確実にfloat型に変換
            emp = decimal_to_float(emp)
            available_time = emp.get('time', 0)
            try:
                available_time = max(0, float(available_time))
            except:
                available_time = 0.0
            
            if available_time >= required_worktime:
                emp['stage0_passed'] = True
                emp['stage0_details'] = {'available_time': available_time}
                passed.append(emp)
        
        logger.info(f"【0次審査】{len(employees)}名 → {len(passed)}名")
        return passed

    @staticmethod
    def stage1_motivation_screening(employees, target_role):
        """1次審査: やる気"""
        passed = []
        THRESHOLD = 3
        
        for emp in employees:
            # Decimal型を確実にfloat型に変換
            emp = decimal_to_float(emp)
            motivation = emp.get('motivation_by_role', {}).get(target_role, 0)
            try:
                motivation = max(0, min(5, float(motivation)))
            except:
                motivation = 0.0
            
            if motivation >= THRESHOLD:
                emp['stage1_passed'] = True
                emp['stage1_details'] = {'motivation_level': motivation}
                passed.append(emp)
        
        logger.info(f"【1次審査】{len(employees)}名 → {len(passed)}名")
        return passed

    @staticmethod
    def calculate_employee_level(employee, target_role):
        """
        改善版：一般的な社員が0.4～0.6になる計算式
        """
        
        # ===== 1. 資格スコア（40%）=====
        cert_score = 0.3  # 基礎点：資格なしでも0.3
        
        certifications = employee.get('certifications', [])
        cert_count = 0
        
        for cert in certifications[:3]:  # 最大3つまで評価
            cert_count += 1
            if any(keyword in cert for keyword in ['AWS', 'Google', 'Azure', 'GCP']):
                cert_score += 0.2
            elif any(keyword in cert for keyword in ['スペシャリスト', '高度', 'Expert', 'Professional']):
                cert_score += 0.15
            elif any(keyword in cert for keyword in ['応用', '基本', '情報', '検定', '認定']):
                cert_score += 0.1
            else:
                cert_score += 0.05
        
        cert_score = min(cert_score, 1.0)
        
        # ===== 2. 勤続年数スコア（30%）=====
        tenure = employee.get('勤続年数', 0)
        try:
            tenure = float(tenure)
        except (ValueError, TypeError):
            tenure = 0
        
        if tenure == 0:
            tenure_score = 0.3  # 新人でも基礎点0.3
        elif tenure < 2:
            tenure_score = 0.4
        elif tenure < 4:
            tenure_score = 0.5
        elif tenure < 6:
            tenure_score = 0.6
        elif tenure < 8:
            tenure_score = 0.7
        elif tenure < 10:
            tenure_score = 0.8
        else:
            tenure_score = 0.9
        
        # ===== 3. 経験スコア（30%）=====
        exp_score = 0.3  # 基礎点：経験なしでも0.3
        
        experience = employee.get('経験', {})
        if experience:
            total_exp_years = sum(experience.values())
            # 経験年数の合計で評価（5年で+0.25、10年で+0.5）
            additional_score = min(total_exp_years * 0.05, 0.6)
            exp_score = 0.3 + additional_score
        
        exp_score = min(exp_score, 0.9)
        
        # ===== 最終計算 =====
        final_level = (
            cert_score * 0.4 +
            tenure_score * 0.3 +
            exp_score * 0.3
        )
        
        # デバッグ情報（最初の数名のみ）
        if logger.level <= logging.DEBUG:
            logger.debug(f"社員{employee.get('employee_id')}レベル計算: "
                        f"資格={cert_score:.2f}×0.4 + "
                        f"勤続={tenure_score:.2f}×0.3 + "
                        f"経験={exp_score:.2f}×0.3 = {final_level:.2f}")
        
        return round(final_level * 10) / 10

    @staticmethod
    def stage2_level_matching(employees, project_data, target_role):
        """
        2次審査: レベルマッチング
        """
        # プロジェクトデータのDecimal型を確実にfloat型に変換
        project_data = decimal_to_float(project_data)
        
        # role要件を取得（デフォルト値も改善）
        role_requirements = project_data.get('role_requirements', {}).get(target_role, {})
        required_level = float(role_requirements.get('level', 0.5))  # デフォルト0.5
        level_range = float(role_requirements.get('level_range', 0.2))  # デフォルト±0.2
        
        # 範囲が0の場合は自動的に0.1に修正
        if level_range == 0:
            logger.warning(f"level_range=0は厳しすぎるため、0.1に自動調整")
            level_range = 0.1
        
        logger.info(f"【2次審査】Role: {target_role}")
        logger.info(f"  要求レベル: {required_level:.1f} (±{level_range:.1f})")
        logger.info(f"  通過範囲: {required_level - level_range:.1f} ~ {required_level + level_range:.1f}")
        
        passed = []
        level_distribution = []
        
        for emp in employees:
            employee_level = RankingEngine.calculate_employee_level(emp, target_role)
            level_distribution.append(employee_level)
            
            # 要求レベルとの差分
            level_diff = abs(employee_level - required_level)
            
            emp['stage2_score'] = employee_level
            emp['stage2_details'] = {
                'employee_level': employee_level,
                'required_level': required_level,
                'level_range': level_range,
                'level_diff': round(level_diff, 3),
                'within_range': level_diff <= level_range
            }
            
            if level_diff <= level_range:
                emp['stage2_passed'] = True
                passed.append(emp)
        
        # 審査結果のサマリー
        total_employees = len(employees)
        passed_count = len(passed)
        pass_rate = (passed_count / total_employees * 100) if total_employees > 0 else 0
        
        logger.info(f"  審査対象: {total_employees}名")
        logger.info(f"  通過: {passed_count}名 ({pass_rate:.1f}%)")
        
        # レベル分布の統計
        if level_distribution:
            avg_level = sum(level_distribution) / len(level_distribution)
            min_level = min(level_distribution)
            max_level = max(level_distribution)
            logger.info(f"  レベル分布: 最小={min_level:.1f}, 平均={avg_level:.2f}, 最大={max_level:.1f}")
            
            # 0.4-0.6の範囲に何％が収まっているか
            in_range = sum(1 for l in level_distribution if 0.4 <= l <= 0.6)
            logger.info(f"  0.4-0.6の範囲: {in_range}/{len(level_distribution)}名 "
                       f"({in_range/len(level_distribution)*100:.1f}%)")
        
        # 通過者が0の場合の警告
        if passed_count == 0:
            logger.warning(f"2次審査で全員不通過！要求レベル{required_level}±{level_range}が厳しすぎる可能性")
            logger.warning(f"社員の実際のレベル範囲: {min_level:.1f}～{max_level:.1f}")
        
        return passed

    @staticmethod
    def stage3_mbti_scoring(employees, project_category):
        """3次審査: MBTI適性"""
        scored_employees = []
        
        for emp in employees:
            mbti = emp.get('mbti_percentages', {
                'E': 50, 'I': 50, 'N': 50, 'S': 50,
                'T': 50, 'F': 50, 'J': 50, 'P': 50
            })
            
            # Decimal型を確実にfloat型に変換
            mbti = decimal_to_float(mbti)
            
            if project_category == '新規開発':
                score = float(mbti.get('N', 50)) / 100
            elif project_category == '改善・保守':
                s_percentage = float(mbti.get('S', 50))
                i_percentage = float(mbti.get('I', 50))
                score = (s_percentage * 2 + i_percentage) / 300
            elif project_category == 'クライアント対応':
                score = float(mbti.get('E', 50)) / 100
            else:
                score = 0.5
            
            emp['stage3_score'] = round(score, 3)
            scored_employees.append(emp)
        
        logger.info(f"【3次審査】MBTI適性評価完了 - {len(scored_employees)}名")
        return scored_employees

    @staticmethod
    def select_top_candidates_stage3(employees, top_n):
        """3次審査の上位候補者選出"""
        # Decimal型対応：top_nを整数に変換
        top_n = int(float(top_n)) if top_n is not None else 0
        sorted_emp = sorted(employees, key=lambda x: x.get('stage3_score', 0), reverse=True)
        selected = sorted_emp[:min(top_n, len(sorted_emp))]
        
        for rank, emp in enumerate(selected, 1):
            emp['stage3_rank'] = rank
        
        logger.info(f"3次審査: 上位{len(selected)}名を選出")
        return selected

    @staticmethod
    def calculate_mbti_compatibility(mbti1, mbti2, role_name=''):
        """MBTI相性計算"""
        total_score = 0
        details = {'role': role_name, 'dimensions': {}}
        
        # Decimal型を確実にfloat型に変換
        mbti1 = decimal_to_float(mbti1) if mbti1 else {}
        mbti2 = decimal_to_float(mbti2) if mbti2 else {}
        
        # E-I次元: 適度な差が理想
        e1, e2 = float(mbti1.get('E', 50)), float(mbti2.get('E', 50))
        ei_diff = abs(e1 - e2)
        if 20 <= ei_diff <= 60:
            ei_score = 0.25
        elif ei_diff < 20:
            ei_score = 0.15
        else:
            ei_score = 0.1
        total_score += ei_score
        
        # N-S次元: 同じ方向が理想
        n1, n2 = float(mbti1.get('N', 50)), float(mbti2.get('N', 50))
        ns_diff = abs(n1 - n2)
        ns_score = 0.25 * (1 - ns_diff / 100)
        total_score += ns_score
        
        # T-F次元: 適度な差が理想
        t1, t2 = float(mbti1.get('T', 50)), float(mbti2.get('T', 50))
        tf_diff = abs(t1 - t2)
        if 20 <= tf_diff <= 60:
            tf_score = 0.25
        elif tf_diff < 20:
            tf_score = 0.15
        else:
            tf_score = 0.1
        total_score += tf_score
        
        # J-P次元: 同じ方向が理想
        j1, j2 = float(mbti1.get('J', 50)), float(mbti2.get('J', 50))
        jp_diff = abs(j1 - j2)
        jp_score = 0.25 * (1 - jp_diff / 100)
        total_score += jp_score
        
        return {'total_score': round(min(total_score, 1.0), 3)}

    @staticmethod
    def stage4_compatibility_scoring(employees, leader_mbti, sub_leader_mbti):
        """4次審査: リーダー相性"""
        scored_employees = []
        
        # Decimal型を確実にfloat型に変換
        leader_mbti = decimal_to_float(leader_mbti) if leader_mbti else {}
        sub_leader_mbti = decimal_to_float(sub_leader_mbti) if sub_leader_mbti else {}
        
        for emp in employees:
            emp_mbti = decimal_to_float(emp.get('mbti_percentages', {}))
            
            leader_compat = RankingEngine.calculate_mbti_compatibility(emp_mbti, leader_mbti, 'リーダー')
            sub_compat = RankingEngine.calculate_mbti_compatibility(emp_mbti, sub_leader_mbti, 'サブリーダー')
            
            weighted_score = (leader_compat['total_score'] * 2 + sub_compat['total_score']) / 3
            
            emp['stage4_score'] = round(weighted_score, 3)
            emp['stage4_details'] = {
                'leader_compatibility': leader_compat['total_score'],
                'sub_leader_compatibility': sub_compat['total_score']
            }
            scored_employees.append(emp)
        
        logger.info(f"【4次審査】リーダー相性評価完了 - {len(scored_employees)}名")
        return scored_employees

    @staticmethod
    def select_top_candidates_stage4(employees, top_n):
        """4次審査の上位候補者選出"""
        # Decimal型対応：top_nを整数に変換
        top_n = int(float(top_n)) if top_n is not None else 0
        sorted_emp = sorted(employees, key=lambda x: x.get('stage4_score', 0), reverse=True)
        selected = sorted_emp[:min(top_n, len(sorted_emp))]
        
        for rank, emp in enumerate(selected, 1):
            emp['stage4_rank'] = rank
        
        logger.info(f"4次審査: 上位{len(selected)}名を選出")
        return selected

    @staticmethod
    def calculate_final_scores(employees):
        """最終スコア計算"""
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

    @staticmethod
    def determine_mbti_type(mbti_percentages):
        """MBTI型判定"""
        if not mbti_percentages:
            return "Unknown"
        
        # Decimal型を確実にfloat型に変換
        mbti_percentages = decimal_to_float(mbti_percentages)
        
        mbti_type = ""
        mbti_type += 'E' if float(mbti_percentages.get('E', 50)) >= 50 else 'I'
        mbti_type += 'N' if float(mbti_percentages.get('N', 50)) >= 50 else 'S'
        mbti_type += 'T' if float(mbti_percentages.get('T', 50)) >= 50 else 'F'
        mbti_type += 'J' if float(mbti_percentages.get('J', 50)) >= 50 else 'P'
        
        return mbti_type

    @staticmethod
    def create_final_candidate_list(employees, role, required_count):
        """最終候補者リスト作成"""
        sorted_employees = sorted(employees, key=lambda x: x.get('final_score', 0), reverse=True)
        
        candidates = []
        for rank, emp in enumerate(sorted_employees, 1):
            candidate_info = {
                'rank': rank,
                'employee_id': emp.get('employee_id'),
                'employee_name': emp.get('name'),
                'role': role,
                'final_score': emp.get('final_score', 0),
                'grade': emp.get('final_grade', 'D'),
                'grade_description': emp.get('grade_description', ''),
                'mbti_type': RankingEngine.determine_mbti_type(emp.get('mbti_percentages', {})),
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

    @staticmethod
    def create_empty_candidate_list(role, required_count):
        """空の候補者リスト作成"""
        return {
            'role': role,
            'required_count': required_count,
            'total_candidates': 0,
            'candidates': [],
            'message': '審査を通過した候補者がいません'
        }


class TeamSetGenerator:
    """チーム候補セット生成クラス"""
    
    @staticmethod
    def enrich_employee_data(candidates_by_role):
        """社員データにMBTI相性情報を追加"""
        enriched_groups = {}
        for role, candidates in candidates_by_role.items():
            enriched_members = []
            for candidate_info in candidates:
                for candidate in candidate_info['candidates']:
                    mbti_type = candidate.get('mbti_type', 'UNKNOWN')
                    if mbti_type in MBTI_RELATIONS:
                        candidate['bad_match'] = MBTI_RELATIONS[mbti_type]['bad']
                        candidate['not_good_match'] = MBTI_RELATIONS[mbti_type]['not_good']
                    else:
                        candidate['bad_match'] = ''
                        candidate['not_good_match'] = ''
                    
                    # 直近プロジェクトメンバー情報（今回は空リストで初期化）
                    candidate['recent'] = []
                    enriched_members.append(candidate)
            enriched_groups[role] = enriched_members
        return enriched_groups

    @staticmethod
    def selection_sizes(groups, recruiting_roles):
        """各グループの選出人数計算"""
        sizes = {}
        for role, required_count in recruiting_roles.items():
            if role in groups and groups[role]:
                # Decimal型対応：required_countを整数に変換
                required_count_int = int(float(required_count)) if required_count is not None else 0
                # 要求人数と利用可能な候補者数の最小値
                sizes[role] = min(required_count_int, len(groups[role]))
            else:
                sizes[role] = 0
        return sizes

    @staticmethod
    def is_valid_recent(members):
        """recent考慮：同じメンバーが直近にいる場合はNG"""
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                if (members[j]['employee_name'] in members[i].get('recent', []) or 
                    members[i]['employee_name'] in members[j].get('recent', [])):
                    return False
        return True

    @staticmethod
    def is_valid_mbti(members):
        """MBTI考慮"""
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                if (members[i].get('bad_match') == members[j].get('mbti_type') or
                    members[j].get('bad_match') == members[i].get('mbti_type') or
                    members[i].get('not_good_match') == members[j].get('mbti_type') or
                    members[j].get('not_good_match') == members[i].get('mbti_type')):
                    return False
        return True

    @staticmethod
    def calculate_team_diversity_score(members):
        """チームの多様性スコア計算（MBTI・経験年数・資格数のバランス）"""
        if not members:
            return 0
        
        # MBTI多様性：4次元での分散
        mbti_scores = {'E': [], 'N': [], 'T': [], 'J': []}
        experience_years = []
        cert_counts = []
        
        for member in members:
            mbti_percentages = member.get('details', {}).get('mbti_percentages', {})
            if mbti_percentages:
                mbti_scores['E'].append(float(mbti_percentages.get('E', 50)))
                mbti_scores['N'].append(float(mbti_percentages.get('N', 50)))
                mbti_scores['T'].append(float(mbti_percentages.get('T', 50)))
                mbti_scores['J'].append(float(mbti_percentages.get('J', 50)))
            
            # 経験年数
            tenure = member.get('details', {}).get('tenure_years', 0)
            experience_years.append(float(tenure) if tenure else 0)
            
            # 資格数
            certs = member.get('details', {}).get('certifications', [])
            cert_counts.append(len(certs) if certs else 0)
        
        # 分散計算（高い分散 = 高い多様性）
        diversity_score = 0
        for dimension_scores in mbti_scores.values():
            if len(dimension_scores) > 1:
                mean_val = sum(dimension_scores) / len(dimension_scores)
                variance = sum((x - mean_val) ** 2 for x in dimension_scores) / len(dimension_scores)
                diversity_score += variance / 2500  # 正規化（0-100の範囲なので）
        
        # 経験年数の多様性
        if len(experience_years) > 1:
            exp_mean = sum(experience_years) / len(experience_years)
            exp_variance = sum((x - exp_mean) ** 2 for x in experience_years) / len(experience_years)
            diversity_score += min(exp_variance / 25, 1.0)  # 正規化
        
        # 資格数の多様性
        if len(cert_counts) > 1:
            cert_mean = sum(cert_counts) / len(cert_counts)
            cert_variance = sum((x - cert_mean) ** 2 for x in cert_counts) / len(cert_counts)
            diversity_score += min(cert_variance / 10, 1.0)  # 正規化
        
        return round(diversity_score, 3)

    @staticmethod
    def calculate_team_balance_score(members):
        """チームバランススコア（若手・中堅・ベテランのバランス）"""
        if not members:
            return 0
        
        # 経験年数でカテゴリ分け
        categories = {'junior': 0, 'mid': 0, 'senior': 0}
        
        for member in members:
            tenure = member.get('details', {}).get('tenure_years', 0)
            tenure_years = float(tenure) if tenure else 0
            
            if tenure_years < 3:
                categories['junior'] += 1
            elif tenure_years < 8:
                categories['mid'] += 1
            else:
                categories['senior'] += 1
        
        total = sum(categories.values())
        if total == 0:
            return 0
        
        # 理想的な比率: 若手30%, 中堅50%, ベテラン20%
        ideal_ratios = {'junior': 0.3, 'mid': 0.5, 'senior': 0.2}
        
        balance_score = 0
        for category, count in categories.items():
            actual_ratio = count / total
            ideal_ratio = ideal_ratios[category]
            # 理想からの差が小さいほど高スコア
            balance_score += max(0, 1 - abs(actual_ratio - ideal_ratio) * 2)
        
        return round(balance_score / 3, 3)

    @staticmethod
    def calculate_weighted_potential_score(members):
        """重み付きポテンシャルスコア（若手のスコアを重視）"""
        if not members:
            return 0
        
        total_weighted_score = 0
        total_weights = 0
        
        for member in members:
            base_score = member.get('final_score', 0)
            tenure = member.get('details', {}).get('tenure_years', 0)
            tenure_years = float(tenure) if tenure else 0
            
            # 若手ほど高い重み（成長ポテンシャル重視）
            if tenure_years < 2:
                weight = 1.5  # 新人は1.5倍
            elif tenure_years < 5:
                weight = 1.2  # 若手は1.2倍
            elif tenure_years < 10:
                weight = 1.0  # 中堅は等倍
            else:
                weight = 0.8  # ベテランは0.8倍
            
            total_weighted_score += base_score * weight
            total_weights += weight
        
        return round(total_weighted_score / total_weights if total_weights > 0 else 0, 3)

    @staticmethod
    def best_team_pure_score(groups, recruiting_roles):
        """戦略1: 純粋な高スコアチーム（トップスコア重視）"""
        top_employees = []
        total_score = 0
        
        for role, required_count in recruiting_roles.items():
            if role in groups and groups[role]:
                required_count = int(float(required_count)) if required_count is not None else 0
                # スコア降順で上位選出
                sorted_members = sorted(groups[role], key=lambda x: x.get('final_score', 0), reverse=True)
                selected = sorted_members[:min(required_count, len(sorted_members))]
                
                for m in selected:
                    top_employees.append(m)
                    total_score += m.get('final_score', 0)
        
        return top_employees, total_score

    @staticmethod
    def best_team_diversity_focused(groups, recruiting_roles):
        """戦略2: 多様性重視チーム（MBTI・経験・資格の多様性）"""
        sizes = TeamSetGenerator.selection_sizes(groups, recruiting_roles)
        
        group_combos = []
        role_list = []
        for role, required_count in recruiting_roles.items():
            if role in groups and groups[role] and sizes[role] > 0:
                role_list.append(role)
                members = groups[role]
                k = sizes[role]
                group_combos.append(list(itertools.combinations(members, k)))
        
        if not group_combos:
            return None, -1
        
        best_team, best_composite_score = None, -1
        
        for combo in itertools.product(*group_combos):
            team = [m for group in combo for m in group]
            
            # 基本制約チェック
            if not TeamSetGenerator.is_valid_mbti(team) or not TeamSetGenerator.is_valid_recent(team):
                continue
            
            # 多様性を重視した複合スコア
            base_score = sum(m.get('final_score', 0) for m in team)
            diversity_score = TeamSetGenerator.calculate_team_diversity_score(team)
            balance_score = TeamSetGenerator.calculate_team_balance_score(team)
            
            # 多様性とバランスを重視（基本スコア60%, 多様性25%, バランス15%）
            composite_score = (base_score * 0.6) + (diversity_score * len(team) * 0.25) + (balance_score * len(team) * 0.15)
            
            if composite_score > best_composite_score:
                best_composite_score = composite_score
                best_team = team
        
        return best_team, best_composite_score

    @staticmethod
    def best_team_potential_focused(groups, recruiting_roles):
        """戦略3: ポテンシャル重視チーム（成長可能性・若手育成）"""
        sizes = TeamSetGenerator.selection_sizes(groups, recruiting_roles)
        
        group_combos = []
        for role, required_count in recruiting_roles.items():
            if role in groups and groups[role] and sizes[role] > 0:
                members = groups[role]
                k = sizes[role]
                group_combos.append(list(itertools.combinations(members, k)))
        
        if not group_combos:
            return None, -1
        
        best_team, best_potential_score = None, -1
        
        for combo in itertools.product(*group_combos):
            team = [m for group in combo for m in group]
            
            # 基本制約チェック
            if not TeamSetGenerator.is_valid_mbti(team) or not TeamSetGenerator.is_valid_recent(team):
                continue
            
            # ポテンシャルを重視した複合スコア
            weighted_score = TeamSetGenerator.calculate_weighted_potential_score(team)
            balance_score = TeamSetGenerator.calculate_team_balance_score(team)
            
            # 若手のやる気も考慮
            motivation_bonus = 0
            for member in team:
                tenure = member.get('details', {}).get('tenure_years', 0)
                motivation = member.get('details', {}).get('motivation', 0)
                if float(tenure) < 5 and float(motivation) >= 4:  # 若手で高いやる気
                    motivation_bonus += 0.2
            
            # ポテンシャル重視スコア（重み付きスコア70%, バランス20%, やる気ボーナス10%）
            potential_score = (weighted_score * 0.7) + (balance_score * 0.2) + (motivation_bonus * 0.1)
            
            if potential_score > best_potential_score:
                best_potential_score = potential_score
                best_team = team
        
        return best_team, best_potential_score

    @staticmethod
    def exclude_selected_members(groups, selected_members):
        """選択されたメンバーを候補から除外"""
        excluded_names = set()
        if selected_members:
            excluded_names = {member.get('employee_name') for member in selected_members}
        
        filtered_groups = {}
        for role, members in groups.items():
            filtered_members = [
                member for member in members 
                if member.get('employee_name') not in excluded_names
            ]
            filtered_groups[role] = filtered_members
        
        return filtered_groups

    @staticmethod
    def best_team_diversity_focused_with_exclusion(groups, recruiting_roles, excluded_members=None):
        """戦略2: 多様性重視チーム（除外機能付き）"""
        # 除外処理
        if excluded_members:
            groups = TeamSetGenerator.exclude_selected_members(groups, excluded_members)
        
        return TeamSetGenerator.best_team_diversity_focused(groups, recruiting_roles)

    @staticmethod
    def best_team_potential_focused_with_exclusion(groups, recruiting_roles, excluded_members=None):
        """戦略3: ポテンシャル重視チーム（除外機能付き）"""
        # 除外処理
        if excluded_members:
            groups = TeamSetGenerator.exclude_selected_members(groups, excluded_members)
        
        return TeamSetGenerator.best_team_potential_focused(groups, recruiting_roles)


def process_role_screening(employees, role, required_count, project_data, 
                          project_category, leader_mbti, sub_leader_mbti):
    """特定roleの完全な審査プロセス"""
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Role: {role} の審査開始（募集: {required_count}名）")
    logger.info(f"{'='*50}")
    
    # 0次審査: 稼働時間
    candidates = RankingEngine.stage0_worktime_screening(employees, project_data.get('worktime', 20))
    if not candidates:
        return RankingEngine.create_empty_candidate_list(role, required_count)
    
    # 1次審査: やる気
    candidates = RankingEngine.stage1_motivation_screening(candidates, role)
    if not candidates:
        return RankingEngine.create_empty_candidate_list(role, required_count)
    
    # 2次審査: レベルマッチング
    candidates = RankingEngine.stage2_level_matching(candidates, project_data, role)
    if not candidates:
        return RankingEngine.create_empty_candidate_list(role, required_count)
    
    # 3次審査: MBTI適性（上位10×募集人数）
    candidates = RankingEngine.stage3_mbti_scoring(candidates, project_category)
    # Decimal型対応：required_countを整数に変換
    required_count_int = int(float(required_count)) if required_count is not None else 0
    candidates = RankingEngine.select_top_candidates_stage3(candidates, 10 * required_count_int)
    if not candidates:
        return RankingEngine.create_empty_candidate_list(role, required_count)
    
    # 4次審査: リーダー相性（上位5×募集人数）
    candidates = RankingEngine.stage4_compatibility_scoring(candidates, leader_mbti, sub_leader_mbti)
    candidates = RankingEngine.select_top_candidates_stage4(candidates, 5 * required_count_int)
    
    # 最終スコア計算
    candidates = RankingEngine.calculate_final_scores(candidates)
    
    # 最終候補者リスト作成
    return RankingEngine.create_final_candidate_list(candidates, role, required_count)


def process_all_roles(project_id):
    """全roleの審査を実施"""
    
    # プロジェクトデータ取得
    project_data = DatabaseManager.fetch_project_from_dynamodb(project_id)
    if not project_data:
        logger.error(f"Project {project_id} not found")
        return {"error": "Project not found"}
    
    # 必要情報の抽出
    project_category = project_data.get('category', '新規開発')
    recruiting_roles = project_data.get('recruiting_roles', {})
    leader_mbti = project_data.get('leader_mbti', {}).get('percentages', {})
    sub_leader_mbti = project_data.get('sub_leader_mbti', {}).get('percentages', {})
    
    # 全社員データ取得とグループ化
    all_employees = DatabaseManager.fetch_employees_from_dynamodb()
    employees_by_role = DatabaseManager.group_employees_by_role(all_employees)
    
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
            all_results['roles'][role] = RankingEngine.create_empty_candidate_list(role, required_count)
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


def generate_candidate_sets(ranking_results):
    """ランキング結果からチーム候補セットを生成"""
    
    project_info = ranking_results.get('project_info', {})
    roles_data = ranking_results.get('roles', {})
    
    # 募集ロールの抽出
    recruiting_roles = {}
    for role, role_data in roles_data.items():
        recruiting_roles[role] = role_data.get('required_count', 0)
    
    # 候補者データの準備
    candidates_by_role = {}
    for role, role_data in roles_data.items():
        if role_data.get('candidates'):
            candidates_by_role[role] = [role_data]
    
    # 社員データの拡張（MBTI情報追加）
    enriched_groups = TeamSetGenerator.enrich_employee_data(candidates_by_role)
    
    # 3つの異なる戦略によるチーム生成（段階的除外）
    result = {}
    
    # set1: 純粋な高スコアチーム（各ロールのトップ）
    top_members, total_score = TeamSetGenerator.best_team_pure_score(enriched_groups, recruiting_roles)
    result["set1"] = [
        {
            "employee_name": member.get('employee_name'),
            "role": member.get('role')
        }
        for member in (top_members if top_members else [])
    ]
    
    # set2: 多様性重視チーム（set1で選ばれた人を除外）
    best_team_diversity, best_score_diversity = TeamSetGenerator.best_team_diversity_focused_with_exclusion(
        enriched_groups, recruiting_roles, top_members
    )
    result["set2"] = [
        {
            "employee_name": member.get('employee_name'),
            "role": member.get('role')
        }
        for member in (best_team_diversity if best_team_diversity else [])
    ]
    
    # set3: ポテンシャル重視チーム（set1とset2で選ばれた人を除外）
    excluded_for_set3 = []
    if top_members:
        excluded_for_set3.extend(top_members)
    if best_team_diversity:
        excluded_for_set3.extend(best_team_diversity)
    
    best_team_potential, best_score_potential = TeamSetGenerator.best_team_potential_focused_with_exclusion(
        enriched_groups, recruiting_roles, excluded_for_set3
    )
    result["set3"] = [
        {
            "employee_name": member.get('employee_name'),
            "role": member.get('role')
        }
        for member in (best_team_potential if best_team_potential else [])
    ]
    
    return result


def lambda_handler(event, context):
    """AWS Lambda エントリーポイント"""
    try:
        project_id = event.get('project_id')
        
        if not project_id:
            return {'error': 'project_id is required'}
        
        # ランキング処理の実行
        ranking_results = process_all_roles(project_id)
        
        if 'error' in ranking_results:
            return ranking_results
        
        # チーム候補セット生成
        team_sets = generate_candidate_sets(ranking_results)
        
        # データオブジェクトを直接返す（JSON文字列ではなく）
        return decimal_to_float(team_sets)
        
    except Exception as e:
        logger.error(f"処理エラー: {str(e)}")
        return {'error': str(e)}

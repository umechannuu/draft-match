import itertools
import json

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

# サンプルデータ（候補者リスト形式）
sample_candidates_by_role = {
    "フロントエンド開発者": {
        "role": "フロントエンド開発者",
        "required_count": 2,
        "total_candidates": 5,
        "candidates": [
            {
                "rank": 1,
                "employee_id": "EMP001",
                "employee_name": "田中太郎",
                "role": "フロントエンド開発者",
                "final_score": 0.85,
                "grade": "A",
                "mbti_type": "ENFP",
                "details": {
                    "tenure_years": 3,
                    "motivation": 5,
                    "certifications": ["AWS Developer", "React専門"],
                    "mbti_percentages": {"E": 70, "N": 80, "T": 40, "J": 30}
                }
            },
            {
                "rank": 2,
                "employee_id": "EMP002", 
                "employee_name": "佐藤花子",
                "role": "フロントエンド開発者",
                "final_score": 0.78,
                "grade": "B",
                "mbti_type": "ISTJ",
                "details": {
                    "tenure_years": 5,
                    "motivation": 4,
                    "certifications": ["情報処理技術者"],
                    "mbti_percentages": {"E": 25, "N": 40, "T": 75, "J": 80}
                }
            },
            {
                "rank": 3,
                "employee_id": "EMP003",
                "employee_name": "山田次郎", 
                "role": "フロントエンド開発者",
                "final_score": 0.72,
                "grade": "B",
                "mbti_type": "INFJ",
                "details": {
                    "tenure_years": 2,
                    "motivation": 5,
                    "certifications": ["Vue.js認定"],
                    "mbti_percentages": {"E": 35, "N": 75, "T": 20, "J": 85}
                }
            },
            {
                "rank": 4,
                "employee_id": "EMP004",
                "employee_name": "鈴木三郎",
                "role": "フロントエンド開発者", 
                "final_score": 0.65,
                "grade": "C",
                "mbti_type": "ESTP",
                "details": {
                    "tenure_years": 1,
                    "motivation": 4,
                    "certifications": [],
                    "mbti_percentages": {"E": 80, "N": 30, "T": 60, "J": 20}
                }
            },
            {
                "rank": 5,
                "employee_id": "EMP005",
                "employee_name": "高橋四郎",
                "role": "フロントエンド開発者",
                "final_score": 0.58,
                "grade": "C", 
                "mbti_type": "ISFP",
                "details": {
                    "tenure_years": 8,
                    "motivation": 3,
                    "certifications": ["基本情報技術者"],
                    "mbti_percentages": {"E": 20, "N": 45, "T": 25, "J": 40}
                }
            }
        ]
    },
    "バックエンド開発者": {
        "role": "バックエンド開発者", 
        "required_count": 2,
        "total_candidates": 4,
        "candidates": [
            {
                "rank": 1,
                "employee_id": "EMP011",
                "employee_name": "伊藤五郎",
                "role": "バックエンド開発者",
                "final_score": 0.88,
                "grade": "A",
                "mbti_type": "INTJ",
                "details": {
                    "tenure_years": 6,
                    "motivation": 4,
                    "certifications": ["AWS Solutions Architect", "Java Gold"],
                    "mbti_percentages": {"E": 15, "N": 85, "T": 90, "J": 75}
                }
            },
            {
                "rank": 2,
                "employee_id": "EMP012",
                "employee_name": "渡辺六郎",
                "role": "バックエンド開発者", 
                "final_score": 0.82,
                "grade": "A",
                "mbti_type": "ENTP",
                "details": {
                    "tenure_years": 4,
                    "motivation": 5,
                    "certifications": ["Python Expert"],
                    "mbti_percentages": {"E": 75, "N": 80, "T": 70, "J": 25}
                }
            },
            {
                "rank": 3,
                "employee_id": "EMP013",
                "employee_name": "加藤七子",
                "role": "バックエンド開発者",
                "final_score": 0.75,
                "grade": "B", 
                "mbti_type": "ISFJ",
                "details": {
                    "tenure_years": 3,
                    "motivation": 4,
                    "certifications": ["応用情報技術者"],
                    "mbti_percentages": {"E": 30, "N": 40, "T": 35, "J": 80}
                }
            },
            {
                "rank": 4,
                "employee_id": "EMP014",
                "employee_name": "斎藤八郎", 
                "role": "バックエンド開発者",
                "final_score": 0.68,
                "grade": "C",
                "mbti_type": "ESTJ",
                "details": {
                    "tenure_years": 10,
                    "motivation": 3,
                    "certifications": ["基本情報技術者", "Oracle Master"],
                    "mbti_percentages": {"E": 85, "N": 20, "T": 80, "J": 90}
                }
            }
        ]
    },
    "プロジェクトマネージャー": {
        "role": "プロジェクトマネージャー",
        "required_count": 1,
        "total_candidates": 3,
        "candidates": [
            {
                "rank": 1,
                "employee_id": "EMP021",
                "employee_name": "田村九郎",
                "role": "プロジェクトマネージャー",
                "final_score": 0.92,
                "grade": "A",
                "mbti_type": "ENTJ",
                "details": {
                    "tenure_years": 12,
                    "motivation": 5,
                    "certifications": ["PMP", "ITストラテジスト"],
                    "mbti_percentages": {"E": 90, "N": 75, "T": 85, "J": 95}
                }
            },
            {
                "rank": 2,
                "employee_id": "EMP022",
                "employee_name": "中村十子",
                "role": "プロジェクトマネージャー",
                "final_score": 0.87,
                "grade": "A", 
                "mbti_type": "ENFJ",
                "details": {
                    "tenure_years": 8,
                    "motivation": 5,
                    "certifications": ["プロジェクトマネージャ試験"],
                    "mbti_percentages": {"E": 80, "N": 70, "T": 40, "J": 85}
                }
            },
            {
                "rank": 3,
                "employee_id": "EMP023",
                "employee_name": "小林十一",
                "role": "プロジェクトマネージャー",
                "final_score": 0.79,
                "grade": "B",
                "mbti_type": "INTP", 
                "details": {
                    "tenure_years": 5,
                    "motivation": 4,
                    "certifications": ["応用情報技術者"],
                    "mbti_percentages": {"E": 25, "N": 85, "T": 80, "J": 30}
                }
            }
        ]
    }
}

# 募集要件
recruiting_roles = {
    "フロントエンド開発者": 2,
    "バックエンド開発者": 2, 
    "プロジェクトマネージャー": 1
}

class TeamSetGenerator:
    """チーム候補セット生成クラス"""
    
    @staticmethod
    def enrich_employee_data(candidates_by_role):
        """社員データにMBTI相性情報を追加"""
        enriched_groups = {}
        for role, role_data in candidates_by_role.items():
            enriched_members = []
            for candidate in role_data['candidates']:
                mbti_type = candidate.get('mbti_type', 'UNKNOWN')
                if mbti_type in MBTI_RELATIONS:
                    candidate['bad_match'] = MBTI_RELATIONS[mbti_type]['bad']
                    candidate['not_good_match'] = MBTI_RELATIONS[mbti_type]['not_good']
                else:
                    candidate['bad_match'] = ''
                    candidate['not_good_match'] = ''
                
                # 直近プロジェクトメンバー情報 (将来の拡張用)
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
                sizes[role] = min(required_count, len(groups[role]))
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
            
            tenure = member.get('details', {}).get('tenure_years', 0)
            experience_years.append(float(tenure) if tenure else 0)
            
            certs = member.get('details', {}).get('certifications', [])
            cert_counts.append(len(certs) if certs else 0)
        
        diversity_score = 0
        for dimension_scores in mbti_scores.values():
            if len(dimension_scores) > 1:
                mean_val = sum(dimension_scores) / len(dimension_scores)
                variance = sum((x - mean_val) ** 2 for x in dimension_scores) / len(dimension_scores)
                diversity_score += variance / 2500  
        
        if len(experience_years) > 1:
            exp_mean = sum(experience_years) / len(experience_years)
            exp_variance = sum((x - exp_mean) ** 2 for x in experience_years) / len(experience_years)
            diversity_score += min(exp_variance / 25, 1.0)  
        
        if len(cert_counts) > 1:
            cert_mean = sum(cert_counts) / len(cert_counts)
            cert_variance = sum((x - cert_mean) ** 2 for x in cert_counts) / len(cert_counts)
            diversity_score += min(cert_variance / 10, 1.0)  
        
        return round(diversity_score, 3)

    @staticmethod
    def calculate_team_balance_score(members):
        """チームバランススコア（若手・中堅・ベテランのバランス）"""
        if not members:
            return 0
        
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
        
        ideal_ratios = {'junior': 0.3, 'mid': 0.5, 'senior': 0.2}
        
        balance_score = 0
        for category, count in categories.items():
            actual_ratio = count / total
            ideal_ratio = ideal_ratios[category]
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
            
            if tenure_years < 2:
                weight = 1.5  
            elif tenure_years < 5:
                weight = 1.2  
            elif tenure_years < 10:
                weight = 1.0  
            else:
                weight = 0.8  
            
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
            
            if not TeamSetGenerator.is_valid_mbti(team) or not TeamSetGenerator.is_valid_recent(team):
                continue
            
            base_score = sum(m.get('final_score', 0) for m in team)
            diversity_score = TeamSetGenerator.calculate_team_diversity_score(team)
            balance_score = TeamSetGenerator.calculate_team_balance_score(team)
            
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
            
            if not TeamSetGenerator.is_valid_mbti(team) or not TeamSetGenerator.is_valid_recent(team):
                continue
            
            weighted_score = TeamSetGenerator.calculate_weighted_potential_score(team)
            balance_score = TeamSetGenerator.calculate_team_balance_score(team)
            
            motivation_bonus = 0
            for member in team:
                tenure = member.get('details', {}).get('tenure_years', 0)
                motivation = member.get('details', {}).get('motivation', 0)
                if float(tenure) < 5 and float(motivation) >= 4:  
                    motivation_bonus += 0.2
            
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
        if excluded_members:
            groups = TeamSetGenerator.exclude_selected_members(groups, excluded_members)
        
        return TeamSetGenerator.best_team_diversity_focused(groups, recruiting_roles)

    @staticmethod
    def best_team_potential_focused_with_exclusion(groups, recruiting_roles, excluded_members=None):
        """戦略3: ポテンシャル重視チーム（除外機能付き）"""
        if excluded_members:
            groups = TeamSetGenerator.exclude_selected_members(groups, excluded_members)
        
        return TeamSetGenerator.best_team_potential_focused(groups, recruiting_roles)


def generate_candidate_sets(candidates_by_role, recruiting_roles):
    """チーム候補セットを生成"""
    
    enriched_groups = TeamSetGenerator.enrich_employee_data(candidates_by_role)
    
    result = {}
    
    # set1: 純粋な高スコアチーム（各ロールのトップ）
    top_members, total_score = TeamSetGenerator.best_team_pure_score(enriched_groups, recruiting_roles)
    result["set1"] = {
        "strategy": "高スコア重視",
        "total_score": total_score,
        "members": [
            {
                "employee_name": member.get('employee_name'),
                "role": member.get('role'),
                "final_score": member.get('final_score'),
                "mbti_type": member.get('mbti_type'),
                "grade": member.get('grade')
            }
            for member in (top_members if top_members else [])
        ]
    }
    
    # set2: 多様性重視チーム（set1で選ばれた人を除外）
    best_team_diversity, best_score_diversity = TeamSetGenerator.best_team_diversity_focused_with_exclusion(
        enriched_groups, recruiting_roles, top_members
    )
    result["set2"] = {
        "strategy": "多様性重視",
        "total_score": best_score_diversity,
        "members": [
            {
                "employee_name": member.get('employee_name'),
                "role": member.get('role'),
                "final_score": member.get('final_score'),
                "mbti_type": member.get('mbti_type'),
                "grade": member.get('grade')
            }
            for member in (best_team_diversity if best_team_diversity else [])
        ]
    }
    
    # set3: ポテンシャル重視チーム（set1とset2で選ばれた人を除外）
    excluded_for_set3 = []
    if top_members:
        excluded_for_set3.extend(top_members)
    if best_team_diversity:
        excluded_for_set3.extend(best_team_diversity)
    
    best_team_potential, best_score_potential = TeamSetGenerator.best_team_potential_focused_with_exclusion(
        enriched_groups, recruiting_roles, excluded_for_set3
    )
    result["set3"] = {
        "strategy": "ポテンシャル重視",
        "total_score": best_score_potential,
        "members": [
            {
                "employee_name": member.get('employee_name'),
                "role": member.get('role'),
                "final_score": member.get('final_score'),
                "mbti_type": member.get('mbti_type'),
                "grade": member.get('grade')
            }
            for member in (best_team_potential if best_team_potential else [])
        ]
    }
    
    return result


if __name__ == "__main__":
    print("=== チーム候補セット生成システム ===\n")
    
    team_sets = generate_candidate_sets(sample_candidates_by_role, recruiting_roles)
    
    for set_name, set_data in team_sets.items():
        print(f"=== {set_name}: {set_data['strategy']} ===")
        print(f"総合スコア: {set_data['total_score']:.3f}")
        print("メンバー:")
        for member in set_data['members']:
            print(f"  - {member['employee_name']} ({member['role']}) - スコア: {member['final_score']:.3f}, MBTI: {member['mbti_type']}, グレード: {member['grade']}")
        print()
    
    print("=== 詳細候補者情報 ===")
    print(json.dumps(sample_candidates_by_role, indent=2, ensure_ascii=False))

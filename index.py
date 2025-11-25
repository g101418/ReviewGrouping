import random
import math
from collections import defaultdict
import os

# 定义分组生成的主类
class GroupGeneration:
    """
    负责读取输入数据、初始化分组参数，并使用回溯法（backtracking）
    实现组长、外部专家和普通组员的分组分配。
    分组需满足：
    1. 每组人数在 [group_person_lower_limit, group_person_upper_limit] 范围内。
    2. 每组外部专家数不超过 group_external_upper_limit。
    3. 组员的省份不能出现在其所在组的省份限制列表 groups 中。
    4. 组长必须是每组的第一个成员。
    """

    # --- 类变量定义 ---
    M = -1  # 组和组长数 (Number of groups and leaders)
    N = -1  # 组员数 (Number of general members)
    external_num = 0  # 外部专家总数 (Total number of external experts)

    group_person_lower_limit = 1
    group_person_upper_limit = -1  # 每组人数的上限 (Upper limit for people per group)
    group_external_upper_limit = -1  # 每组外部专家上限 (Upper limit for external experts per group)

    assigned_groups = defaultdict(list)  # 存储分配结果，键为组ID (0到M-1)，值为成员列表
    group_leaders = []  # 组长列表
    group_members = []  # 组员列表
    groups = []  # 组的省份限制列表，groups[i] 存储第 i 组不能包含的省份列表

    group_members_no_external = []  # 非外部专家组员
    group_members_external = []  # 外部专家组员

    # 用于限制最多有多少组可以“触顶”（达到上限人数/外部专家数）
    max_group_external_touch_upper_limit = -1
    max_group_member_touch_upper_limit = -1
    # --- 结束类变量定义 ---

    def __init__(self):
        # 构造函数，通常用于初始化实例特有的变量，这里保持简洁
        pass

    def parse_input(self, input_text):
        """
        解析输入文本，提取 M, N，组长、组员信息和组的省份限制。
        """
        lines = input_text.splitlines()
        lines = [line.strip() for line in lines if line.strip() != '']

        # 清空旧数据以支持多次运行
        self.group_leaders.clear()
        self.group_members.clear()
        self.groups.clear()
        self.assigned_groups.clear()
        self.external_num = 0

        try:
            self.M = int(lines[0])  # 组长和组的数量
            self.N = int(lines[1])  # 组员数量
        except IndexError:
            raise ValueError("输入文本行数不足，无法解析 M 和 N。")

        lines = lines[2:]

        def get_person_info(text):
            """内部辅助函数：解析单个人员信息"""
            parts = text.split()
            if len(parts) != 2 and len(parts) != 3:
                raise ValueError(f"人员信息格式错误: {text}")
            # 检查是否有 "外部" 标识
            is_external = len(parts) == 3 and parts[2] == "外部"
            return parts[0], parts[1], is_external

        # 读取组长信息 (M 行)
        for i in range(self.M):
            name, province, is_external = get_person_info(lines[i])

            self.group_leaders.append({
                "name": name,
                "province": province,
                "is_external": is_external
            })

            if is_external: self.external_num += 1

        # 读取组员信息 (N 行)
        for i in range(self.M, self.M + self.N):
            name, province, is_external = get_person_info(lines[i])

            self.group_members.append({
                "name": name,
                "province": province,
                "is_external": is_external
            })

            if is_external: self.external_num += 1

        # 读取组的省份限制信息 (M 行)
        start_index = self.M + self.N
        end_index = self.M + self.N + self.M
        
        if end_index > len(lines):
             raise ValueError("输入文本行数不足，无法解析所有组的省份限制。")

        self.groups = [
            group.split() for group in lines[start_index:end_index]
        ]
        
        if len(self.groups) != self.M:
            raise ValueError("解析到的组限制数量与 M 不匹配。")


    def format_output(self):
        """
        将分配结果格式化为易读的字符串输出。
        """
        output = []

        for i in range(self.M):
            # assigned_groups[i] 的第一个元素是组长
            leader = self.assigned_groups[i][0]
            # 剩余元素是组员
            members = self.assigned_groups[i][1:]
            
            # 格式化组长信息
            leader_tag = "（外部）" if leader["is_external"] else ""
            leader_output = f"组长：{leader['name']}{leader_tag}"
            
            # 格式化组员信息
            members_output_list = []
            for member in members:
                member_tag = "（外部）" if member['is_external'] else ""
                members_output_list.append(f"{member['name']}{member_tag}")
            
            members_output = ", ".join(members_output_list)
            
            output.append(f"第{i + 1}组：{leader_output}; 组员：{members_output}")

        res = "\n".join(output)
        return res


    def init(self):
        """
        初始化分组的上下限和触顶限制参数。
        """
        total_people = self.M + self.N
        
        # 每组人数的下限（平均数向下取整）
        self.group_person_lower_limit = total_people // self.M
        # 每组人数的上限（平均数向上取整）
        self.group_person_upper_limit = math.ceil(total_people / self.M)
        
        # 每组外部专家的上限（外部专家平均数向上取整）
        self.group_external_upper_limit = math.ceil(self.external_num / self.M)
        
        # 达到人数上限的组数限制 (余数决定)
        # 例如：总人数17，组数5。平均3.4人/组。上限4人/组。
        # 17 % 5 = 2。表示最多只有 2 组可以达到 4 人/组的上限。
        self.max_group_member_touch_upper_limit = total_people % self.M
        if self.max_group_member_touch_upper_limit == 0:
             # 如果余数为0，表示所有组平均分配，上限组数为0，但为了允许所有组都达到上限（如果上限=下限），设为M
             # 实际是：如果整除，上限等于下限，所有组都应该等于这个值。这里逻辑需要保证 check() 约束
             # 对于 (M+N)%M == 0 的情况，上限组数应为 0，因为所有组人数都应为 (M+N)/M。
             # 但在分配时，允许 M 组都可以尝试达到上限 (如果上限 > 下限)。
             # 更好的做法是，如果 (M+N)%M == 0，则所有组的人数必须等于 group_person_lower_limit。
             # 现行代码中，如果 max_group_member_touch_upper_limit 为 0，意味着在回溯中不能让任何组达到上限。
             # 但为了兼容 check() 的逻辑（最高最低人数差不超过1），当整除时，上限组数应该为 M，但分配的目标是 group_person_lower_limit。
             # 这里保持代码原意，但在 (M+N)%M == 0 时， group_person_upper_limit == group_person_lower_limit，
             # 此时触顶没有意义，分配函数需要依赖 check()。这里先用 M 替代 0，保证分配逻辑能跑完。
             self.max_group_member_touch_upper_limit = self.M
        
        # 达到外部专家上限的组数限制 (余数决定)
        self.max_group_external_touch_upper_limit = self.external_num % self.M
        if self.max_group_external_touch_upper_limit == 0:
             self.max_group_external_touch_upper_limit = self.M
             
        # 将组员按是否为外部专家分类，便于后续分批次分配
        self.group_members_external = [mem for mem in self.group_members if mem['is_external'] == True]
        self.group_members_no_external = [mem for mem in self.group_members if mem['is_external'] == False]

    def assign_backtrace(self, index, people, can_assign_func):
        """
        通用的回溯法分配函数。
        
        :param index: 当前处理的 people 列表中的人员索引。
        :param people: 待分配的人员列表 (组长、外部专家或普通组员)。
        :param can_assign_func: 检查人员 person 是否可以分配给组 group_id 的函数。
        :return: 布尔值，表示是否成功分配所有人员。
        """
        # 递归终止条件：所有人都已分配
        if index == len(people):
            return True

        person = people[index]
        
        # 尝试分配给每个组
        for group_id in range(self.M):
            # 检查是否可以分配
            if can_assign_func(person, group_id):
                # 做出选择
                self.assigned_groups[group_id].append(person)
                
                # 递归：尝试分配下一个人
                if self.assign_backtrace(index + 1, people, can_assign_func):
                    return True
                else:
                    # 撤销选择 (回溯)
                    self.assigned_groups[group_id].pop()

        # 所有组都尝试过，但无法分配
        return False

    def assign_leaders(self):
        """
        第一阶段：分配组长。组长必须是每组的第一个成员。
        约束：组长的省份不能在对应组的省份限制列表 groups 中。
        """

        def can_assign_func(person, group_id):
            # 省份冲突检查：组长的省份不能出现在该组的限制列表中
            if person["province"] in self.groups[group_id]:
                return False
            # 确保每组只分配一个组长（组长是每组的第一个成员）
            if len(self.assigned_groups[group_id]) >= 1:
                return False
            return True
        
        # 随机打乱后的组长列表进行分配
        if self.assign_backtrace(0, self.group_leaders, can_assign_func):
            return True
        else:
            return False

    def assign_externals(self):
        """
        第二阶段：分配外部专家组员。
        约束：
        1. 省份冲突。
        2. 组人数不超过 group_person_upper_limit。
        3. 组外部专家数不超过 group_external_upper_limit。
        4. 达到外部专家上限的组数不超过 max_group_external_touch_upper_limit。
        """

        def get_group_touch_limit(group_id):
            """计算当前已分配的组中，外部专家数达到上限的组的数量。"""
            used_group_touched_num = 0
            # 检查当前组是否已经触顶
            is_this_group_touched = False 
            
            for group_id_ in range(self.M):
                group = self.assigned_groups[group_id_]

                external_num = sum(1 for person in group if person["is_external"])

                # 检查当前组是否达到外部专家上限（用于判断回溯前后的状态）
                if group_id_ == group_id and external_num >= self.group_external_upper_limit:
                    is_this_group_touched = True
                    
                # 计算已触顶组的数量
                if external_num >= self.group_external_upper_limit:
                    used_group_touched_num += 1

            return is_this_group_touched, used_group_touched_num

        def get_group_external_num(group_id):
            """计算指定组当前的外部专家数量。"""
            return sum(1 for person in self.assigned_groups[group_id] if person["is_external"])

        def can_assign_func(person, group_id):
            # 省份冲突检查
            if person["province"] in self.groups[group_id]:
                return False

            this_group_external_num = get_group_external_num(group_id)
            
            # 外部专家数上限检查
            if this_group_external_num >= self.group_external_upper_limit:
                return False

            # 总人数上限检查
            if len(self.assigned_groups[group_id]) >= self.group_person_upper_limit:
                return False
            
            # 外部专家触顶组数限制检查
            _, used_group_touched_num = get_group_touch_limit(group_id)
            
            # 假设分配当前外部专家后，该组将触顶
            if this_group_external_num + 1 >= self.group_external_upper_limit:
                # 如果当前已触顶的组数已达到最大限制
                if used_group_touched_num >= self.max_group_external_touch_upper_limit:
                    return False
            
            return True


        # 随机打乱后的外部专家组员列表进行分配
        if self.assign_backtrace(0, self.group_members_external, can_assign_func):
            return True
        else:
            return False

    def assign_members(self):
        """
        第三阶段：分配普通组员（非外部专家）。
        约束：
        1. 省份冲突。
        2. 组人数不超过 group_person_upper_limit。
        3. 达到人数上限的组数不超过 max_group_member_touch_upper_limit。
        """
        
        def get_group_touch_limit(group_id):
            """计算当前已分配的组中，人数达到上限的组的数量。"""
            used_group_touched_num = 0
            is_this_group_touched = False
            
            for group_id_ in range(self.M):
                group = self.assigned_groups[group_id_]

                member_num = len(group)
                
                # 检查当前组是否已经触顶
                if group_id_ == group_id and member_num >= self.group_person_upper_limit:
                    is_this_group_touched = True
                
                # 计算已触顶组的数量
                if member_num >= self.group_person_upper_limit:
                    used_group_touched_num += 1

            return is_this_group_touched, used_group_touched_num

        def can_assign_func(person, group_id):
            # 省份冲突检查
            if person["province"] in self.groups[group_id]:
                return False
            
            current_member_num = len(self.assigned_groups[group_id])
            
            # 总人数上限检查
            if current_member_num >= self.group_person_upper_limit:
                return False
            
            # 人数触顶组数限制检查
            _, used_group_touched_num = get_group_touch_limit(group_id)
            
            # 假设分配当前组员后，该组将触顶
            if current_member_num + 1 >= self.group_person_upper_limit:
                # 如果当前已触顶的组数已达到最大限制
                if used_group_touched_num >= self.max_group_member_touch_upper_limit:
                    return False
            
            return True
        
        
        # 随机打乱后的普通组员列表进行分配
        if self.assign_backtrace(0, self.group_members_no_external, can_assign_func):
            return True
        else:
            return False

    def shuffle(self, seed):
        """
        使用给定的种子随机打乱组长和组员列表，以尝试不同的分配顺序。
        """
        random.seed(seed)
        random.shuffle(self.group_leaders)
        random.shuffle(self.group_members)

    def check(self):
        """
        检查最终分组结果是否满足所有约束条件。
        约束包括：
        1. 总人数是否正确。
        2. 每组人数是否在 [lower_limit, upper_limit] 范围内。
        3. 最高组人数和最低组人数之差是否不超过 1。
        4. 省份冲突检查 (组员省份不能在组限制中)。
        5. 每组至少包含 1 个外部专家 (此处为 1 的硬性要求)。
        """
        total_people = 0
        lowest_group_person_num = float('inf')
        highest_group_person_num = float('-inf')
        
        # 遍历所有组
        for group_id in range(self.M):
            group = self.assigned_groups[group_id]
            group_len = len(group)
            
            # 检查每组人数是否在上下限范围内
            if group_len > self.group_person_upper_limit:
                print(f"Check Error: Group {group_id + 1} person num {group_len} > upper limit {self.group_person_upper_limit}")
                return False
            if group_len < self.group_person_lower_limit:
                print(f"Check Error: Group {group_id + 1} person num {group_len} < lower limit {self.group_person_lower_limit}")
                return False
                
            external_num = 0
            for person in group:
                total_people += 1
                if person["is_external"]:
                    external_num += 1
                
                # 检查省份冲突
                if person["province"] in self.groups[group_id]:
                    print(f"Check Error: Person {person['name']} province {person['province']} in group {group_id + 1} conflict {self.groups[group_id]}")
                    return False
            
            # 检查每组至少有 1 个外部专家 (根据原代码逻辑，此处是 >= 1)
            # ⚠️ 注意: 尽管原代码 group_external_lower_limit 被初始化为 1，但它并未在 init 或 check 中被正确使用。
            # 原来的 check 函数中检查的是 if external_num < 1: return False
            if external_num < 1:
                print(f"Check Error: Group {group_id + 1} external num {external_num} < 1")
                return False
            
            # 更新最高和最低人数
            highest_group_person_num = max(highest_group_person_num, group_len)
            lowest_group_person_num = min(lowest_group_person_num, group_len)
        
        # 检查总人数是否与 M+N 相等
        if total_people != self.M + self.N:
            print(f"Check Error: Total people {total_people} != M+N {self.M + self.N}")
            return False
        
        # 检查最高人数和最低人数之差是否不超过 1 (确保人数分配尽量均衡)
        if highest_group_person_num - lowest_group_person_num > 1:
            print(f"Check Error: Person num difference {highest_group_person_num - lowest_group_person_num} > 1")
            return False

        return True

    def random_way(self, seed):
        """
        【已废弃的实现方式】
        这是一个简单的循环分配方法，不使用回溯，仅用于简单的随机测试。
        此方法无法保证满足所有复杂约束，因此被回溯法取代。
        """
        print("Warning: Calling deprecated random_way method.")
        while True:
            self.shuffle(seed)
            self.assigned_groups = defaultdict(list)
            
            # 简单分配：组长按顺序分配
            for i in range(self.M):
                self.assigned_groups[i].append(self.group_leaders[i])

            # 简单分配：组员轮流分配
            for i in range(self.N):
                self.assigned_groups[i % self.M].append(self.group_members[i])

            # 检查分配结果是否符合要求
            if self.check():
                return
            
            # 如果不符合要求，将通过外部循环继续尝试不同的 seed
            seed += 1
            random.seed(seed)
            self.shuffle(seed)


    def run(self, seed, text):
        """
        主执行函数：解析输入、初始化参数、分阶段分配。
        """
        
        self.parse_input(text)
        self.shuffle(seed)  # 使用种子打乱顺序，以尝试不同的解
        self.init()

        # 1. 分配组长 (Leaders)
        if self.assign_leaders() == False:
            return "无法找到匹配的分配方式 (分配组长失败)"
        
        # 2. 分配外部专家组员 (External Members)
        # 这一步是为了优先满足外部专家数的限制
        if self.assign_externals() == False:
            return "无法找到匹配的分配方式 (分配外部专家失败)"
            
        # 3. 分配普通组员 (General Members)
        if self.assign_members() == False:
            return "无法找到匹配的分配方式 (分配普通组员失败)"

        # self.random_way(seed) # 废弃方法

        # 检查最终结果是否满足所有硬性约束
        if not self.check():
             # 虽然回溯法设计上应该满足，但以防万一
             return "成功找到分配方式，但最终校验失败，可能存在逻辑错误。"

        return self.format_output()
        
def test_group_generation(file_path, iterations=300):
    """
    独立测试函数：对给定的输入文件，循环运行多次并检查结果。
    """
    groupGeneration = GroupGeneration()
    
    # 尝试从文件读取输入
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    print(f"--- 开始运行 {iterations} 次随机种子测试 ---")
    
    all_passed = True
    for i in range(iterations):
        # 运行分配
        result = groupGeneration.run(i, text)
        
        # 检查分配是否成功
        if "无法找到匹配的分配方式" in result or "校验失败" in result:
            print(f"Seed {i}: 分配失败 - {result}")
            all_passed = False
            # 失败后可以继续尝试下一个种子，或直接退出
            # continue
        else:
            # 检查结果是否满足所有约束
            if groupGeneration.check() == False:
                print(f"Seed {i}: 分配成功但校验失败！")
                all_passed = False
        
        # 打印最后一个成功的分配结果
        if i == iterations - 1 and all_passed:
            print("\n--- 最后一次成功分配结果 ---")
            print(result)

    print("\n--- 测试总结 ---")
    if all_passed:
        print(f"✅ 所有 {iterations} 次测试均成功通过 (分配成功且校验通过)。")
    else:
        print(f"❌ 存在失败的测试 (未能找到匹配方式或校验失败)。")


# --- __main__ 块 ---
if __name__ == "__main__":
    # 定义输入文件路径
    # ⚠️ 请确保你的运行目录下有 '情况表.txt' 文件
    INPUT_FILE = "./情况表.txt"
    
    # 将测试独立封装到函数中
    test_group_generation(INPUT_FILE, iterations=300)
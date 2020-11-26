import random
from itertools import combinations, product
import search

ids = ["328711569", "312581655"]


class MedicalProblem(search.Problem):
    """This class implements a medical problem according to problem description file"""

    def __init__(self, initial):
        self.police = initial["police"]
        self.medics = initial["medics"]
        self.initial_map = initial["map"]
        self.initial_state = (initial["map"], self.init_state_status())
        search.Problem.__init__(self, self.initial_state)

    # creates status map according to areas in initial map.
    # Status map-shows number of days that area is in some condition.
    # In initial map: -1 equals to H,U,I areas. 1 equals to Q,S areas( day 1)
    def init_state_status(self):
        status_map = [[0 for i in range(len(self.initial_map[0]))] for i in range(len(self.initial_map))]
        for i in range(len(self.initial_map)):
            for j in range(len(self.initial_map[0])):
                if self.initial_map[i][j] == "S" or self.initial_map[i][j] == "Q":
                    status_map[i][j] = 1
                else:
                    status_map[i][j] = -1
        return tuple(tuple(sub) for sub in status_map)

    # function receives state and code=area status (S,H,Q,U or I)
    # function returns all indexes where appears area with given code.
    def find_areas_in_state(self, state, code):
        qur_map = state[0]
        q_status_areas = ()
        for i in range(len(qur_map)):
            for j in range(len(qur_map[0])):
                if qur_map[i][j] == code:
                    q_status_areas = q_status_areas + ((i, j),)
        return q_status_areas

    # function receives indexes of some areas and a team
    # returns tuple of tuples. Each tuple=(team,area index)
    def add_team_to_area(self, areas, team):
        areas = list(areas)
        for i in range(len(areas)):
            action = (team, areas[i])
            areas[i] = action
        return tuple(areas)

    def actions(self, state):
        s_areas = self.add_team_to_area(self.find_areas_in_state(state, "S"), "quarantine")
        h_areas = self.add_team_to_area(self.find_areas_in_state(state, "H"), "vaccinate")
        s_combinations = tuple(combinations(s_areas, min(self.police, len(s_areas))))
        h_combinations = tuple(combinations(h_areas, min(self.medics, len(h_areas))))
        all_actions = tuple(product(h_combinations, s_combinations))
        return all_actions

    #  function receives map, areas and code in {U,I,Q,S,H}
    # function changes received areas status to code and returns modified map
    # status_map is not updated here!
    def change_area_status(self, map, areas, code):

        aux_map = list(map)
        for i in range(len(areas)):
            index = areas[i][1]
            if code == 'I':
                assert aux_map[index[0]][index[1]] == 'H'
            elif code == 'Q':
                assert aux_map[index[0]][index[1]] == 'S'
            else:
                raise NotImplementedError
            aux_map[index[0]][index[1]] = code
        return aux_map

    # function receives state and indexes of areas with status S.
    # function finds all healthy neighbours of sick areas, and updates them all to be sick
    # status_map is not updated here!
    def update_H_areas_acc_to_neighbors(self, state, sick_areas):
        qur_map = list(list(sub) for sub in state[0])
        for area in sick_areas:
            neighbors_list = []
            i = area[0]
            j = area[1]
            if i > 0:
                neighbors_list.append([i - 1, j])
            if i < len(qur_map) - 1:
                neighbors_list.append([i + 1, j])

            if j > 0:
                neighbors_list.append([i, j - 1])
            if j < len(qur_map[0]) - 1:
                neighbors_list.append([i, j + 1])

            for neighbor in neighbors_list:
                if qur_map[neighbor[0]][neighbor[1]] == 'H':
                    qur_map[neighbor[0]][neighbor[1]] = 'S'
        return qur_map, state[1]

    # function updates map and  status map. returns state after updates.
    def update_state(self, state, state_after_infection_spread):
        qur_map = state[0]
        status_map = list(list(sub) for sub in state[1])
        map_after_infection_spread = state_after_infection_spread[0]
        for i in range(len(map_after_infection_spread)):
            for j in range(len(map_after_infection_spread[0])):
                if map_after_infection_spread[i][j] == qur_map[i][j]:
                    if map_after_infection_spread[i][j] == 'U' or map_after_infection_spread[i][j] == 'I' \
                            or map_after_infection_spread[i][j] == 'H':
                        continue
                    if map_after_infection_spread[i][j] == 'Q' and status_map[i][j] < 2:
                        status_map[i][j] += 1
                    elif map_after_infection_spread[i][j] == 'S' and status_map[i][j] < 3:
                        status_map[i][j] += 1
                    else:
                        status_map[i][j] = -1
                        map_after_infection_spread[i][j] = "H"
                    continue
                if (qur_map[i][j] == "H" and map_after_infection_spread[i][j] == "S") or (
                        qur_map[i][j] == "S" and map_after_infection_spread[i][j] == "Q"):
                    status_map[i][j] = 1

        updated_status_map = tuple(tuple(sub) for sub in status_map)
        updated_map = tuple(tuple(sub) for sub in map_after_infection_spread)
        return updated_map, updated_status_map

    def result(self, state, action):
        qur_map = list(list(sub) for sub in state[0])
        areas_to_be_vaccinated = list(action[0])
        areas_to_be_quarantined = list(action[1])
        quarantined_areas_map = self.change_area_status(qur_map, areas_to_be_quarantined, "Q")
        quarantined_and_vaccinated_map = self.change_area_status(quarantined_areas_map, areas_to_be_vaccinated, "I")
        map_after_action = tuple(tuple(sub) for sub in quarantined_and_vaccinated_map)
        sick_areas = self.find_areas_in_state((map_after_action, state[1]), 'S')
        state_after_infection_spread = self.update_H_areas_acc_to_neighbors((map_after_action, state[1]), sick_areas)
        state_after_sickness_expires = self.update_state(state, state_after_infection_spread)
        return state_after_sickness_expires

    def goal_test(self, state):
        for row in state[0]:
            for code in row:
                if code == "S":
                    return False
        return True

    def h(self, node):
        num_sick = len(self.find_areas_in_state(node.state, 'S'))
        overall = len(node.state[0][0]) * len(node.state[0])
        if node.depth > 8 or num_sick * 0.5 > overall:
            return self.count_max_between_sick_after_1_step(node)
        return self.count_sick_by_actions(node)

    def count_max_between_sick_after_1_step(self, node):
        sick_areas = self.find_areas_in_state(node.state, 'S')
        state_after_infection_spread = self.update_H_areas_acc_to_neighbors(node.state, sick_areas)
        return max(len(set(self.find_areas_in_state(state_after_infection_spread, 'S'))),
                   self.count_sick(node))

    # find possible teams using action that leaded from node.parent to current state.
    # find possible actions using teams, sample group of actions.
    # Return average number of sick areas after running each action on curr state
    def count_sick_by_actions(self, node):
        qur_state = node.state
        action = node.action
        if node.parent is None or len(action) == 0:
            return self.count_max_between_sick_after_1_step(node)

        assert len(action) == 2

        if len(action[0]) > 0:
            assert action[0][0][0] == 'vaccinate'
        medics = len(action[0])

        if len(action[1]) > 0:
            assert action[1][0][0] == 'quarantine'
        police = len(action[1])

        s_areas = self.add_team_to_area(self.find_areas_in_state(qur_state, "S"), "quarantine")
        h_areas = self.add_team_to_area(self.find_areas_in_state(qur_state, "H"), "vaccinate")
        s_combinations = tuple(combinations(s_areas, min(police, len(s_areas))))
        h_combinations = tuple(combinations(h_areas, min(medics, len(h_areas))))
        all_actions = tuple(product(h_combinations, s_combinations))
        random.seed(42)
        sampled_actions = tuple(random.sample(all_actions, k=min(len(all_actions), 3)))
        sum_num_of_sick = 0
        for a in sampled_actions:
            next_state = self.result(qur_state, a)
            sum_num_of_sick += len(set(self.find_areas_in_state(next_state, 'S')))
        return sum_num_of_sick / len(sampled_actions)

    # counts  total num of sick areas
    def count_sick(self, node):
        return len(set(self.find_areas_in_state(node.state, 'S')))

    """Feel free to add your own functions
    (-2, -2, None) means there was a timeout"""


def create_medical_problem(game):
    return MedicalProblem(game)

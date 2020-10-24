import pandas as pd
from graphviz import Digraph

EPSILON = 'e'
UPPER = "UPPER"
LOWER = "LOWER"

TYPE_TABLE = "type_table"
STATE = "state"


class LStartRegularLanguages:

    table: pd.DataFrame

    def __init__(self, alphabet: set):
        self.alphabet = list(alphabet)

        self.running = True

        self.table = pd.DataFrame(columns=[TYPE_TABLE, STATE, EPSILON]).set_index([TYPE_TABLE, STATE])

        self.cache_accepted_strings = {}

        self.init_table()

    def ask_if_string_belongs_language(self, str_to_ask):
        if str_to_ask in self.cache_accepted_strings:
            return self.cache_accepted_strings[str_to_ask]

        str_show = f"El lenguaje acepta la cadena {str_to_ask}?y/n"
        if str_to_ask == EPSILON:
            str_show = f"El lenguaje acepta la cadena VACIA?y/n"

        response_in = input(str_show).lower()
        value = int(response_in[0] == 'y')

        self.cache_accepted_strings[str_to_ask] = value
        return value

    @staticmethod
    def concatenate_two_strings(str1, str2):
        if str1 == EPSILON:
            return str2

        if str2 == EPSILON:
            return str1

        return f"{str1}{str2}"

    def add_rows_table(self, data: dict):
        index_element_delete = []
        for i, state in enumerate(data[STATE]):
            if state in self.table.index.get_level_values(1).values:
                index_element_delete.append(i)

        for i in sorted(index_element_delete, reverse=True):
            for k in data.keys():
                element_remove = data[k][i]
                data[k].remove(element_remove)

        df = pd.DataFrame.from_dict(data, dtype=str)

        for c in df.columns:
            df[c].astype(str)

        df.set_index([TYPE_TABLE, STATE], inplace=True)

        self.table = pd.concat([self.table, df], sort=True)

        self.table.sort_index(inplace=True)

        for c in self.table.columns:
            self.table[c].astype(str)

    def init_table(self):
        dict_to_add = {STATE: [], EPSILON: [], TYPE_TABLE: []}

        epsilon_belongs = self.ask_if_string_belongs_language(EPSILON)

        dict_to_add[STATE].append(EPSILON)
        dict_to_add[TYPE_TABLE].append(UPPER)
        dict_to_add[EPSILON].append(epsilon_belongs)

        alphabet = self.alphabet
        for sigma in alphabet:
            sigma_belongs_language = self.ask_if_string_belongs_language(sigma)

            dict_to_add[STATE].append(sigma)
            dict_to_add[TYPE_TABLE].append(LOWER)
            dict_to_add[EPSILON].append(sigma_belongs_language)

        self.add_rows_table(dict_to_add)

    def add_column(self, sigma):
        if sigma in self.table:
            return False

        experiment_values = []

        for state_value in self.table.index.get_level_values(1).values:
            str_to_ask = self.concatenate_two_strings(state_value, sigma)
            value_to_add = self.ask_if_string_belongs_language(str_to_ask)
            experiment_values.append(str(value_to_add))

        self.table[sigma] = experiment_values
        return True

    def is_row_consistent_with(self, actual_state_name, similar_state, sigma):
        df = self.table
        is_consistent = True
        next_actual_state = self.concatenate_two_strings(actual_state_name, sigma)
        states_to_add = []
        if next_actual_state not in df.index.get_level_values(1).values:
            states_to_add.append(next_actual_state)

        next_similar_state = self.concatenate_two_strings(similar_state, sigma)
        if next_similar_state not in df.index.get_level_values(1).values:
            states_to_add.append(next_similar_state)

        if len(states_to_add) > 0:
            self.fill_columns(states_to_add, is_upper_table=False)
            df = self.table

        index_values = df.index.values
        idx = df.index.get_level_values(1).values.tolist().index(next_actual_state)
        next_row = df.loc[index_values[idx]]

        idx = df.index.get_level_values(1).values.tolist().index(next_similar_state)
        next_similar_row = df.loc[index_values[idx]]

        if not next_row.equals(next_similar_row) and sigma not in self.table.columns.values:
            # if the values are different, then rey are inconsistent with sigma
            is_consistent = False
        return is_consistent

    def table_consistent(self) -> bool:
        df = self.table
        df_upper = df[df.index.get_level_values(0) == UPPER]

        is_table_consistent = True
        # Explore only those elements that are in the upper table
        for actual_index, actual_row in df_upper.iterrows():
            actual_state_name = actual_index[1]

            for similar_index, similar_row in df_upper.iterrows():

                if similar_index == actual_index or not actual_row.equals(similar_row):
                    continue

                similar_state = similar_index[1]

                for sigma in self.alphabet:
                    consistent = self.is_row_consistent_with(actual_state_name, similar_state, sigma)
                    if is_table_consistent and not consistent:
                        # Contradiction, because we say that the table is consistent, but we found that a row is not
                        # consistent so we add the column sigma to the table
                        self.add_column(sigma)
                        is_table_consistent = False

        return is_table_consistent

    def fill_columns(self, states_to_add: list, is_upper_table: bool):
        dict_to_add = {c: [] for c in self.table.columns}

        for string_to_ask in states_to_add:
            for c in dict_to_add.keys():
                string_to_ask = self.concatenate_two_strings(string_to_ask, c)
                state_belong_language = self.ask_if_string_belongs_language(string_to_ask)
                dict_to_add[c].append(state_belong_language)

        dict_to_add[TYPE_TABLE] = [UPPER if is_upper_table else LOWER] * len(states_to_add)
        dict_to_add[STATE] = states_to_add
        self.add_rows_table(dict_to_add)

    def add_successors_row(self, current_state):
        states_to_add = []
        states_in_table = self.table.index.get_level_values(1).values.tolist()
        for sigma in self.alphabet:
            state_to_add = self.concatenate_two_strings(current_state, sigma)

            for col in self.table.columns:
                state_to_add = self.concatenate_two_strings(state_to_add, col)

                if states_to_add not in states_in_table:
                    states_to_add.append(state_to_add)

        self.fill_columns(states_to_add, is_upper_table=False)

    def table_close(self) -> bool:
        df = self.table
        df_upper = df[df.index.get_level_values(0) == UPPER]
        df_lower = df[df.index.get_level_values(0) == LOWER]
        for actual_index, actual_row in df_lower.iterrows():
            # check if the row is in the upper table
            if actual_row.values not in df_upper.values:
                # We don't found the value in the upper row, then is not close

                # We send the actual row to the upper table
                current_state = actual_index[1]

                df.reset_index(inplace=True)
                index = df.index[(df[TYPE_TABLE] == actual_index[0]) & (df[STATE] == actual_index[1])]
                df.set_value(index, TYPE_TABLE, UPPER).set_index([TYPE_TABLE, STATE], inplace=True)
                # We send the actual row to the upper table

                # Add his successors to the lower table
                self.add_successors_row(current_state)
                return False

        return True

    def get_dictionary_states(self) -> dict:
        df = self.table

        df_upper = df[df.index.get_level_values(0) == UPPER]

        name_states = {}
        i = 0
        for actual_index, actual_value in df_upper.iterrows():
            state_string = actual_index[1]

            if state_string not in name_states:
                name_states[state_string] = f"q{i}"
                i += 1

                for similar_index, similar_value in df.iterrows():
                    similar_state = similar_index[1]
                    if similar_state in name_states or not actual_value.equals(similar_value):
                        continue

                    name_states[similar_state] = name_states[state_string]

        return name_states

    def show_automaton(self):
        name_states = self.get_dictionary_states()
        df_upper = self.table[self.table.index.get_level_values(0) == UPPER]
        final_states = set(name_states[f] for f in df_upper[df_upper[EPSILON] == '1'].index.get_level_values(1).values)

        f = Digraph('finite_state_machine', filename='fsm.gv')
        f.attr(rankdir='LR', size='8,5')
        # Put initial state
        f.attr('node', shape='plaintext')
        f.node(' ')

        # Put the final states
        f.attr('node', shape='doublecircle')
        for q_f in final_states:
            f.node(q_f)

        input_symbols = set(self.alphabet)

        f.attr('node', shape='circle')
        # Initial transition
        f.edge(' ', name_states[EPSILON], label=' ')

        # Transitions
        for string_state_from, state_from in name_states.items():
            for sigma in input_symbols:
                string_state_to = self.concatenate_two_strings(string_state_from, sigma)
                state_to = name_states[string_state_to]

                f.edge(state_from, state_to, label=sigma)

        f.view()

    def deal_counterexample(self):
        string_counterexample = input("Dame un contraejemplo")

        final_string = []

        states_to_add = []
        for c in string_counterexample:
            final_string.append(c)
            current_state = ''.join(final_string)
            if current_state not in self.table.index.get_level_values(1).values:
                states_to_add.append(current_state)
            else:
                # Add the counter example and all his prefixes to the upper table
                df = self.table
                df.reset_index(inplace=True)
                try:
                    index = df.index[(df[TYPE_TABLE] == LOWER) & (df[STATE] == current_state)]
                    df.set_value(index, TYPE_TABLE, UPPER)
                except KeyError:
                    pass
                finally:
                    df.set_index([TYPE_TABLE, STATE], inplace=True)

        self.fill_columns(states_to_add, is_upper_table=True)

    def correct_automaton(self):
        self.show_automaton()
        while True:
            response = input("El automata es correcto?y/n")
            response = response.lower()
            if response[0] == "y":
                self.running = False
                break
            elif response[0] == 'n':
                self.deal_counterexample()
                break

    def run(self):
        while self.running:
            self.table.to_csv("table.csv")
            if not self.table_consistent():
                continue
            elif not self.table_close():
                continue
            self.correct_automaton()


if __name__ == '__main__':
    maestro = LStartRegularLanguages({'0', '1'})
    maestro.run()

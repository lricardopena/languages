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

    def add_rows_to_table(self, data: dict):
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

        self.add_rows_to_table(dict_to_add)

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
        upper_table = df[df.index.get_level_values(0) == UPPER]

        # Explore only those elements that are in the upper table
        for actual_index, actual_row in upper_table.iterrows():
            actual_state_name = actual_index[1]

            for similar_index, similar_row in upper_table.iterrows():

                if similar_index != actual_index and actual_row.equals(similar_row):
                    similar_state = similar_index[1]

                    for sigma in self.alphabet:
                        if sigma not in self.table.columns.values:
                            successor_actual_state = self.concatenate_two_strings(actual_state_name, sigma)
                            successor_similar_state = self.concatenate_two_strings(similar_state, sigma)

                            successor_actual_row = df[df.index.get_level_values(1) == successor_actual_state].iloc[0]
                            successor_similar_row = df[df.index.get_level_values(1) == successor_similar_state].iloc[0]

                            if not successor_actual_row.equals(successor_similar_row):
                                # Contradiction, because we say that the table is consistent, but we found that a row is not
                                # consistent so we add the column sigma to the table
                                self.add_column(sigma)
                                return False

        return True

    def fill_columns(self, states_to_add: list, is_upper_table: bool):
        dict_to_add = {c: [] for c in self.table.columns}

        for string_to_ask in states_to_add:
            for c in dict_to_add.keys():
                string_to_ask = self.concatenate_two_strings(string_to_ask, c)
                state_belong_language = self.ask_if_string_belongs_language(string_to_ask)
                dict_to_add[c].append(state_belong_language)

        dict_to_add[TYPE_TABLE] = [UPPER if is_upper_table else LOWER] * len(states_to_add)
        dict_to_add[STATE] = states_to_add
        self.add_rows_to_table(dict_to_add)

    def add_successors_row(self, current_state):
        states_to_add = [self.concatenate_two_strings(current_state, sigma) for sigma in self.alphabet]

        self.fill_columns(states_to_add, is_upper_table=False)

    def table_close(self) -> bool:
        df = self.table

        upper_table = df[df.index.get_level_values(0) == UPPER]
        lower_table = df[df.index.get_level_values(0) == LOWER]

        for actual_index, actual_row in lower_table.iterrows():
            # check if the row is in the upper table
            if actual_row.values not in upper_table.values:
                # We don't found the value in the upper row, then the table is not close

                # Get the not closed state
                current_state = actual_index[1]

                # reset the index to update the value to the upper table
                df.reset_index(inplace=True)
                # Send the actual state (row) to the upper table
                row = df.index[(df[TYPE_TABLE] == actual_index[0]) & (df[STATE] == actual_index[1])].values
                type_table_values = df[TYPE_TABLE]
                # We send the actual row to the upper table
                type_table_values.loc[row] = UPPER
                df[TYPE_TABLE] = type_table_values

                # Set the index
                df.set_index([TYPE_TABLE, STATE], inplace=True)

                # Add his successors to the lower table
                self.add_successors_row(current_state)
                return False

        return True

    def get_dictionary_states(self):
        df = self.table

        df_upper = df[df.index.get_level_values(0) == UPPER]

        name_states = {}
        states_string = {}
        i = 0
        for actual_index, actual_value in df_upper.iterrows():
            state_string = actual_index[1]

            if state_string not in name_states:
                name_states[state_string] = f"q{i}"
                states_string[f"q{i}"] = str(state_string)
                i += 1

                for similar_index, similar_value in df.iterrows():
                    similar_state = similar_index[1]
                    if similar_state in name_states or not actual_value.equals(similar_value):
                        continue

                    name_states[similar_state] = name_states[state_string]

        return name_states, states_string

    def show_automaton(self):
        name_states, states_string = self.get_dictionary_states()
        upper_table = self.table[self.table.index.get_level_values(0) == UPPER]
        final_states = set(name_states[f] for f in upper_table[upper_table[EPSILON] == '1'].index.get_level_values(1).values)

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
        for state_from, string_state_from in states_string.items():
            for sigma in input_symbols:
                string_state_to = self.concatenate_two_strings(string_state_from, sigma)
                state_to = name_states[string_state_to]

                f.edge(state_from, state_to, label=sigma)

        f.view()

    def deal_counterexample(self):
        string_counterexample = input("Dame un contraejemplo")

        final_string = []

        successors_to_add = []
        states_to_add = []
        for c in string_counterexample:
            final_string.append(c)
            current_state = ''.join(final_string)
            successors_to_add.append(current_state)
            if current_state not in self.table.index.get_level_values(1).values:
                states_to_add.append(current_state)
            else:
                # Add the counter example and all his prefixes to the upper table
                df = self.table
                df.reset_index(inplace=True)
                try:
                    # Send the actual state (row) to the upper table
                    row = df.index[(df[TYPE_TABLE] == LOWER) & (df[STATE] == current_state)].values
                    if len(row) == 0:
                        # The row is already in the upper table
                        continue
                    type_table_values = df[TYPE_TABLE]
                    # We send the actual row to the upper table
                    type_table_values.loc[row] = UPPER
                    df[TYPE_TABLE] = type_table_values
                except KeyError:
                    pass
                finally:
                    # Set the index
                    df.set_index([TYPE_TABLE, STATE], inplace=True)

        self.fill_columns(states_to_add, is_upper_table=True)

        for s in successors_to_add:
            self.add_successors_row(s)

    def correct_automaton(self):
        self.show_automaton()
        while True:
            response = input("El automata es correcto?y/n")
            response = response.lower()
            if response[0] == "y":
                self.running = False
                return True
            elif response[0] == 'n':
                self.deal_counterexample()
                return False

    def run(self):
        while self.running:
            if not self.table_consistent():
                continue

            if not self.table_close():
                continue

            if self.correct_automaton():
                break


if __name__ == '__main__':
    maestro = LStartRegularLanguages({'0', '1'})
    maestro.run()

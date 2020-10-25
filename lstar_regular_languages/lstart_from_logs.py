import pandas as pd

from lstar_regular_languages.lstart import LStartRegularLanguages

EPSILON = '\u03B5'
UPPER = "UPPER"
LOWER = "LOWER"

TYPE_TABLE = "type_table"
STATE = "state"


class LStartRegularLanguagesFromLog(LStartRegularLanguages):
    table: pd.DataFrame

    def __init__(self, path_log: str):
        language = pd.read_csv(path_log)
        language.drop_duplicates(inplace=True)
        language.replace('\\epsilon', EPSILON, inplace=True)

        self.language = language["output"].values.tolist()

        self.alphabet = self.get_alphabet_from_language()

        super().__init__(set(self.alphabet), initialize=False)
        self.init_table()

    def get_alphabet_from_language(self) -> list:
        alphabet = set()

        for s in self.language:
            for sigma in s.split(' '):
                if sigma != EPSILON:
                    alphabet.add(sigma)
        return sorted(list(alphabet))

    def ask_if_string_belongs_language(self, str_to_ask):
        if str_to_ask in self.cache_accepted_strings:
            return self.cache_accepted_strings[str_to_ask]

        self.cache_accepted_strings[str_to_ask] = int(str_to_ask in self.language)
        return self.cache_accepted_strings[str_to_ask]

    @staticmethod
    def concatenate_two_strings(str1, str2):
        if str1 == EPSILON:
            return str2

        if str2 == EPSILON:
            return str1

        return f"{str1} {str2}"

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

    def get_dict_automaton(self):
        name_states, states_string = self.get_dictionary_states()
        upper_table = self.table[self.table.index.get_level_values(0) == UPPER]
        final_states = set(name_states[f] for f in upper_table[upper_table[EPSILON] == '1'].index.get_level_values(1)
                           .values)

        input_symbols = self.alphabet

        # Initial state
        initial_state = name_states[EPSILON]
        # Transitions
        transitions = {}
        for state_from, string_state_from in states_string.items():
            transitions[state_from] = {}
            for sigma in input_symbols:
                string_state_to = self.concatenate_two_strings(string_state_from, sigma)

                state_to = name_states[string_state_to]
                transitions[state_from][sigma] = state_to

        return initial_state, transitions, final_states

    @staticmethod
    def accepts(transitions, initial_state, final_states, s):
        if s == EPSILON:
            return initial_state in final_states

        state = initial_state
        for c in s.split(' '):
            state = transitions[state][c]
        return state in final_states

    def deal_counterexample_automatic(self, string_counterexample):
        final_string = []

        successors_to_add = []
        states_to_add = []
        for c in string_counterexample.split(' '):
            final_string.append(c)
            current_state = ' '.join(final_string)
            successors_to_add.append(current_state)
            if current_state in self.table.index.get_level_values(1).values:
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
            else:
                states_to_add.append(current_state)
        self.fill_columns(states_to_add, is_upper_table=True)

        for s in successors_to_add:
            self.add_successors_row(s)

    def correct_automaton(self):
        initial_state, transitions, final_states = self.get_dict_automaton()

        for s in self.language:
            string_accepted = self.accepts(transitions, initial_state, final_states, s)

            if not string_accepted:
                # Counter example
                self.deal_counterexample_automatic(s)
                return False
        return True


if __name__ == '__main__':
    maestro = LStartRegularLanguagesFromLog("log_pair_characters.example")
    maestro.run()

import random
from operator import attrgetter

def flat_map(f, xs):
    ys = []
    for x in xs:
        ys.extend(f(x))
    return ys


def is_subset(cells1: set[int], cells2: set[int]):
    return cells1.issubset(cells2) or cells2.issubset(cells1)

class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in `self.cells` known to be mines.
        """
        if len(self.cells) == self.count:
            return self.cells.copy()
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in `self.cells` known to be safe.
        """
        if self.count == 0:
            return self.cells.copy()
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []


        self.board_cells = []
        for i in range(self.height):
            for j in range(self.width):
                self.board_cells.append((i, j))



    def rebuild_all_knowledge(self):
        changes_made = False  # Track if any changes are made

        removable = []
        for knowledge in self.knowledge:
            mines = knowledge.known_mines()
            if mines:
                for mine in mines:
                    if mine not in self.mines:
                        self.mines.add(mine)
                removable.append(knowledge)
                continue
            safes = knowledge.known_safes()
            if safes:
                for safe in safes:
                    if safe not in self.safes:
                        self.mark_safe(safe)
                removable.append(knowledge)
        for knowledge in removable:
            self.knowledge.remove(knowledge)
        if changes_made:
            self.rebuild_all_knowledge()

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        if cell in self.mines:
            return
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        if cell in self.safes:
            return
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def normalize_knowledge(self, knowledge: Sentence):
        for mine in self.mines:
            knowledge.mark_mine(mine)
        for safe in self.safes:
            knowledge.mark_safe(safe)
        return knowledge

    def create_knowledge(self, cell, count):
        x, y = cell
        adjoined_cells = []
        for i in range(max(0, x - 1), min(self.height, x + 2)):
            for j in range(max(0, y - 1), min(self.width, y + 2)):
                adjoined_cell = (i, j)
                if adjoined_cell == cell:
                    continue
                adjoined_cells.append((i, j))
        knowledge = self.normalize_knowledge(Sentence(adjoined_cells, count))
        return knowledge

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """

        self.moves_made.add(cell)
        self.mark_safe(cell)

        current_knowledge = self.create_knowledge(cell, count)

        if current_knowledge.count:
            if current_knowledge not in self.knowledge:
                synthesised_knowledge = self.synthesise_knowledge(current_knowledge)
                self.knowledge.append(current_knowledge)

                for knowledge in synthesised_knowledge:
                    if knowledge not in self.knowledge:
                        self.knowledge.append(knowledge)
        else:
            for cell in current_knowledge.cells:
                self.mark_safe(cell)

        self.rebuild_all_knowledge()

    def synthesise_knowledge(self, current_knowledge: Sentence):
        synthesised_knowledge = []
        current_knowledge_cells = set(current_knowledge.cells)
        for knowledge in self.knowledge:
            if knowledge.cells.isdisjoint(current_knowledge.cells):
                continue  # Skip if there is no overlap in cells

            if is_subset(knowledge.cells, current_knowledge.cells):
                cells_difference = [x for x in knowledge.cells if x not in current_knowledge_cells]
                if cells_difference:
                    difference_knowledge = Sentence(cells_difference, abs(current_knowledge.count - knowledge.count))
                    synthesised_knowledge.append(difference_knowledge)

        return synthesised_knowledge

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """

        for item in self.safes:
            if item not in self.moves_made:
                return item
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """

        board_cells_set = set(self.board_cells)
        free_cells = list(board_cells_set - self.mines - self.moves_made)
        free_cells_count = len(free_cells)

        if free_cells_count == 0:
            return None

        if self.knowledge:
            def get_cells(sentence: Sentence):
                return sentence.cells

            dangerous_cells = flat_map(get_cells, self.knowledge)
            for free_cell in free_cells:
                if free_cell not in self.moves_made and free_cell not in dangerous_cells:
                    # Return first possible 0 mines cell.
                    return free_cell

            # Return first cell with less possible mines.
            sorted_knowledge = sorted(self.knowledge, key=attrgetter('count'))
            safest_cells = sorted_knowledge[0].cells
            index = random.randrange(len(safest_cells))
            dangerous_cell = list(safest_cells)[index]
            return dangerous_cell
        else:
            index = random.randrange(free_cells_count)
            unknown_cell = free_cells[index]
            return unknown_cell

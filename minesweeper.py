import itertools
import random
from operator import attrgetter


def flat_map(f, xs):
    ys = []
    for x in xs:
        ys.extend(f(x))
    return ys


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
        self.center = cells[0]
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells) == self.count:
            return set(self.cells)
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count == 0:
            return set(self.cells)
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


        self.board_cells = set()
        self.unrevealed_knowledge = []
        for i in range(self.height):
            for j in range(self.width):
                self.board_cells.add((i, j))
                self.unrevealed_knowledge.append(self.create_knowledge((i, j), 8))



    def rebuild_all_knowledge(self):
        for knowledge in self.knowledge:
            mines = knowledge.known_mines()
            if len(mines):
                for mine in mines:
                    if mine not in self.mines:
                        self.mines.add(mine)
                knowledge.count = 0
            safes = knowledge.known_safes()
            for safe in safes:
                if safe not in self.safes:
                    self.safes.add(safe)
            knowledge.count = 0
        self.knowledge = [knowledge for knowledge in self.knowledge if knowledge.count > 0]

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for knowledge in self.knowledge:
            knowledge.mark_mine(cell)
        for knowledge in self.unrevealed_knowledge:
            knowledge.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for knowledge in self.knowledge:
            knowledge.mark_safe(cell)
        for knowledge in self.unrevealed_knowledge:
            knowledge.mark_safe(cell)

    def normalize_knowledge(self, knowledge: Sentence):
        for mine in self.mines:
            knowledge.mark_mine(mine)
        for safe in self.safes:
            knowledge.mark_safe(safe)
        return knowledge

    def create_knowledge(self, cell, count):
        x, y = cell
        cells = [cell]
        for i in range(max(0, x - 1), min(self.height, x + 2)):
            for j in range(max(0, y - 1), min(self.width, y + 2)):
                adjoined_cell = (i, j)
                if adjoined_cell != cell and adjoined_cell not in self.safes and adjoined_cell not in self.mines:
                    cells.append(adjoined_cell)
        # if count == 0:
        #     print("mark as safe", cells)
        #     for adjoined_cell in cells:
        #         self.mark_safe(adjoined_cell)
        #     return None

        knowledge = self.normalize_knowledge(Sentence(cells, count))
        return None if knowledge.cells == 0 else knowledge

    def splice_unrevealed_knowledge(self, cell: (int, int)):
        for knowledge in self.unrevealed_knowledge:
            if knowledge.center == cell:
                self.unrevealed_knowledge.remove(knowledge)
                return knowledge
        raise IndexError

    def is_actual_knowledge(self, knowledge: Sentence):
        if knowledge is not None and knowledge not in self.knowledge:
            return True
        return False

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

        current_knowledge = self.splice_unrevealed_knowledge(cell)
        current_knowledge.count = count

        if self.is_actual_knowledge(current_knowledge):
            synthesised_knowledge = self.synthesise_knowledge(current_knowledge)
            self.knowledge.append(current_knowledge)

            for knowledge in synthesised_knowledge:
                if knowledge not in self.knowledge:
                    self.knowledge.append(knowledge)

        self.rebuild_all_knowledge()

    def synthesise_knowledge(self, current_knowledge: Sentence):
        synthesised_knowledge = []
        for knowledge in self.knowledge:
            intersected = knowledge.cells.intersection(current_knowledge.cells)
            if intersected:
                intersection_knowledge = Sentence(intersected, current_knowledge.count - knowledge.count)
                synthesised_knowledge.append(intersection_knowledge)
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
                print("found safe", item)
                return item
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """

        unknown_cells = list(self.board_cells.difference(self.moves_made, self.mines))
        length = len(unknown_cells)
        if length == 0:
            return None

        random.shuffle(unknown_cells)

        if self.knowledge:
            def get_cells(sentence: Sentence):
                return sentence.cells

            dangerous_cells = flat_map(get_cells, self.knowledge)
            for unknown_cell in unknown_cells:
                if unknown_cell not in dangerous_cells:
                    # Return first possible 0 mines cell.
                    print("skipped dangerous and found unknown cell", unknown_cell)
                    return unknown_cell

            # Return first cell with less possible mines.
            sorted_knowledge = sorted(self.knowledge, key=attrgetter('count'))
            safest_cells = list(sorted_knowledge[0].cells)
            index = random.randrange(len(safest_cells))
            dangerous_cell = safest_cells[index]
            print("found dangerous cell", dangerous_cell)
            return dangerous_cell
        else:
            index = random.randrange(length)
            unknown_cell = unknown_cells[index]
            print("found random unknown cell", unknown_cell)
            return unknown_cell

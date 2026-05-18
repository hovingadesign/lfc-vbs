"""Word search puzzle generator for VBS worksheets."""
import random
import string


def generate_wordsearch(words, size=None, max_attempts=100):
    """Generate a word search grid with the given words placed in it.

    Returns (grid, placed_words) where grid is a 2D list of characters
    and placed_words is the list of words successfully placed.
    """
    # Clean words: uppercase, no spaces
    clean_words = []
    for w in words:
        cleaned = w.upper().replace(" ", "").replace("-", "")
        clean_words.append(cleaned)

    # Sort longest first for better placement
    clean_words.sort(key=len, reverse=True)

    # Auto-size: longest word + padding
    if size is None:
        longest = max(len(w) for w in clean_words)
        size = max(longest + 4, min(len(clean_words) + 4, 18))

    directions = [
        (0, 1),   # right
        (1, 0),   # down
        (1, 1),   # diagonal down-right
        (-1, 1),  # diagonal up-right
        (0, -1),  # left
        (-1, 0),  # up
        (-1, -1), # diagonal up-left
        (1, -1),  # diagonal down-left
    ]

    best_grid = None
    best_placed = []

    for attempt in range(max_attempts):
        grid = [['' for _ in range(size)] for _ in range(size)]
        placed = []

        for word in clean_words:
            word_placed = False
            random.shuffle(directions)

            positions = [(r, c) for r in range(size) for c in range(size)]
            random.shuffle(positions)

            for dr, dc in directions:
                if word_placed:
                    break
                for r, c in positions:
                    if _can_place(grid, word, r, c, dr, dc, size):
                        _place_word(grid, word, r, c, dr, dc)
                        placed.append(word)
                        word_placed = True
                        break

        if len(placed) > len(best_placed):
            best_grid = [row[:] for row in grid]
            best_placed = placed[:]

        if len(placed) == len(clean_words):
            break

    # Fill empty cells with random letters
    for r in range(size):
        for c in range(size):
            if best_grid[r][c] == '':
                best_grid[r][c] = random.choice(string.ascii_uppercase)

    return best_grid, best_placed


def _can_place(grid, word, row, col, dr, dc, size):
    """Check if a word can be placed at the given position and direction."""
    for i, ch in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        if r < 0 or r >= size or c < 0 or c >= size:
            return False
        if grid[r][c] != '' and grid[r][c] != ch:
            return False
    return True


def _place_word(grid, word, row, col, dr, dc):
    """Place a word in the grid."""
    for i, ch in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        grid[r][c] = ch


# ─── Criss-Cross Crossword Generator ─────────────────────────────────
def generate_crossword(words, max_attempts=500):
    """Generate a criss-cross crossword grid.

    Returns (grid, size, placed_words) where placed_words is a list of
    dicts with keys: word, row, col, direction ('across'|'down'), number.
    """
    clean_words = [w.upper().replace(" ", "").replace("-", "") for w in words]
    # Sort longest first for better placement
    clean_words.sort(key=len, reverse=True)

    best_result = None
    best_count = 0

    for _ in range(max_attempts):
        result = _try_crossword(clean_words)
        if result and len(result) > best_count:
            best_result = result
            best_count = len(result)
            if best_count == len(clean_words):
                break

    if not best_result:
        # Fallback: just place first word across
        best_result = [{'word': clean_words[0], 'row': 0, 'col': 0, 'direction': 'across'}]

    # Determine grid bounds
    min_r = min(p['row'] for p in best_result)
    min_c = min(p['col'] for p in best_result)
    max_r = max(p['row'] + (len(p['word']) - 1 if p['direction'] == 'down' else 0) for p in best_result)
    max_c = max(p['col'] + (len(p['word']) - 1 if p['direction'] == 'across' else 0) for p in best_result)

    # Shift to 0-origin
    for p in best_result:
        p['row'] -= min_r
        p['col'] -= min_c
    rows = max_r - min_r + 1
    cols = max_c - min_c + 1

    # Build grid
    grid = [['' for _ in range(cols)] for _ in range(rows)]
    for p in best_result:
        r, c = p['row'], p['col']
        for i, ch in enumerate(p['word']):
            if p['direction'] == 'across':
                grid[r][c + i] = ch
            else:
                grid[r + i][c] = ch

    # Assign clue numbers: number each cell that starts a word
    # Sort placed words by position (top-to-bottom, left-to-right)
    starts = {}
    for p in best_result:
        key = (p['row'], p['col'])
        if key not in starts:
            starts[key] = []
        starts[key].append(p)

    num = 1
    for key in sorted(starts.keys()):
        for p in starts[key]:
            p['number'] = num
        num += 1

    return grid, (rows, cols), best_result


def _try_crossword(words):
    """Attempt to build a crossword by greedily placing words with best fit.

    Tries ALL remaining words at each step and picks the placement with the
    most intersections (primary) and most compact grid (secondary).
    """
    if not words:
        return []

    # Start with the first (longest) word placed across
    placed = [{'word': words[0], 'row': 0, 'col': 0, 'direction': 'across'}]
    grid_cells = {}  # (r,c) -> letter
    for i, ch in enumerate(words[0]):
        grid_cells[(0, i)] = ch

    remaining = list(words[1:])

    stalled = 0
    while remaining and stalled < len(remaining):
        best_score = None
        best_placement = None
        best_word_idx = None

        for wi, word in enumerate(remaining):
            # Find all candidate placements for this word
            for char_i, wch in enumerate(word):
                for (r, c), gch in grid_cells.items():
                    if wch != gch:
                        continue
                    # Try across: word[char_i] lands at (r, c)
                    col_start = c - char_i
                    if _crossword_fits(word, r, col_start, 'across', grid_cells):
                        score = _placement_score(word, r, col_start, 'across', grid_cells)
                        if best_score is None or score > best_score:
                            best_score = score
                            best_placement = ('across', r, col_start)
                            best_word_idx = wi
                    # Try down: word[char_i] lands at (r, c)
                    row_start = r - char_i
                    if _crossword_fits(word, row_start, c, 'down', grid_cells):
                        score = _placement_score(word, row_start, c, 'down', grid_cells)
                        if best_score is None or score > best_score:
                            best_score = score
                            best_placement = ('down', row_start, c)
                            best_word_idx = wi

        if best_placement:
            direction, sr, sc = best_placement
            word = remaining.pop(best_word_idx)
            p = {'word': word, 'row': sr, 'col': sc, 'direction': direction}
            placed.append(p)
            for i, ch in enumerate(word):
                if direction == 'across':
                    grid_cells[(sr, sc + i)] = ch
                else:
                    grid_cells[(sr + i, sc)] = ch
            stalled = 0
        else:
            # Rotate: move first remaining word to end and try again
            remaining.append(remaining.pop(0))
            stalled += 1

    return placed


def _crossword_fits(word, row, col, direction, grid_cells):
    """Check if word fits at position with proper adjacency enforcement."""
    has_intersection = False

    for i, ch in enumerate(word):
        if direction == 'across':
            r, c = row, col + i
        else:
            r, c = row + i, col

        existing = grid_cells.get((r, c))
        if existing:
            if existing != ch:
                return False
            has_intersection = True
        else:
            # Non-intersection cell: reject parallel neighbors
            if direction == 'across':
                # No filled cells directly above or below
                if grid_cells.get((r - 1, c)):
                    return False
                if grid_cells.get((r + 1, c)):
                    return False
            else:
                # No filled cells directly left or right
                if grid_cells.get((r, c - 1)):
                    return False
                if grid_cells.get((r, c + 1)):
                    return False

    # Cells just before and after the word must be empty
    if direction == 'across':
        if grid_cells.get((row, col - 1)):
            return False
        if grid_cells.get((row, col + len(word))):
            return False
    else:
        if grid_cells.get((row - 1, col)):
            return False
        if grid_cells.get((row + len(word), col)):
            return False

    return has_intersection


def _placement_score(word, row, col, direction, grid_cells):
    """Score a placement: intersections (primary), compactness (secondary).

    Returns a tuple (intersections, -spread) for comparison.
    """
    intersections = 0
    for i, ch in enumerate(word):
        if direction == 'across':
            r, c = row, col + i
        else:
            r, c = row + i, col
        if grid_cells.get((r, c)) == ch:
            intersections += 1

    # Compute how much the grid would spread with this word
    all_rows = [r for (r, _) in grid_cells]
    all_cols = [c for (_, c) in grid_cells]
    if direction == 'across':
        new_rows = [row]
        new_cols = [col, col + len(word) - 1]
    else:
        new_rows = [row, row + len(word) - 1]
        new_cols = [col]
    min_r = min(min(all_rows), *new_rows)
    max_r = max(max(all_rows), *new_rows)
    min_c = min(min(all_cols), *new_cols)
    max_c = max(max(all_cols), *new_cols)
    spread = (max_r - min_r) + (max_c - min_c)

    return (intersections, -spread)


# ─── Word Scramble Generator ────────────────────────────────────────
def generate_scramble(words, secret_message=None):
    """Generate a word scramble puzzle.

    Returns a list of dicts with keys: original, scrambled, secret_index
    (the letter position in the unscrambled word that contributes to the
    secret message, 0-indexed). If secret_message is None, picks a short
    message automatically.

    Words are reordered so that each secret-message letter is matched to a
    word that actually contains it.  Words that don't contribute to the
    secret message are appended at the end.
    """
    clean_words = [w.upper().replace(" ", "").replace("-", "") for w in words]

    if secret_message is None:
        candidates = ["GOD SAVES", "DELIVERED", "REDEEMED", "TRUST GOD", "SET FREE"]
        msg_letters = None
        for cand in candidates:
            letters = cand.replace(" ", "")
            if len(letters) <= len(clean_words):
                msg_letters = letters.upper()
                secret_message = cand
                break
        if msg_letters is None:
            msg_letters = ""
            secret_message = ""
    else:
        msg_letters = secret_message.upper().replace(" ", "")

    # --- Assign words to secret-message positions via greedy matching ---
    ordered = _match_words_to_secret(clean_words, msg_letters)

    result = []
    for i, word in enumerate(ordered):
        secret_idx = None
        if i < len(msg_letters):
            target_ch = msg_letters[i]
            positions = [j for j, ch in enumerate(word) if ch == target_ch]
            if positions:
                secret_idx = random.choice(positions)

        scrambled = _scramble_word(word)
        result.append({
            'original': word,
            'scrambled': scrambled,
            'secret_index': secret_idx,
        })

    return result, secret_message


def _match_words_to_secret(words, msg_letters):
    """Reorder words so that word[i] contains msg_letters[i] when possible.

    Uses a greedy approach: assign the most-constrained secret-letter
    positions first (fewest candidate words), then append unassigned words.
    """
    if not msg_letters:
        return list(words)

    available = set(range(len(words)))

    # For each secret position, list candidate word indices
    candidates = []
    for i, ch in enumerate(msg_letters):
        cands = [wi for wi in range(len(words)) if ch in words[wi]]
        candidates.append((i, ch, cands))

    # Sort by fewest candidates first (most constrained)
    candidates.sort(key=lambda x: len(x[2]))

    assignment = {}  # secret_pos -> word_index
    for pos, ch, cands in candidates:
        for wi in cands:
            if wi in available:
                assignment[pos] = wi
                available.remove(wi)
                break

    # Build ordered list: assigned words at their secret positions,
    # unassigned words appended at the end
    ordered = [None] * len(msg_letters)
    for pos, wi in assignment.items():
        ordered[pos] = words[wi]

    # Fill any unmatched secret positions with remaining words
    remaining = [words[wi] for wi in sorted(available)]
    remain_iter = iter(remaining)
    for i in range(len(ordered)):
        if ordered[i] is None:
            ordered[i] = next(remain_iter)

    # Append any leftover words
    ordered.extend(remain_iter)

    return ordered


def _scramble_word(word):
    """Scramble a word's letters, ensuring the result differs from original."""
    if len(word) <= 2:
        return word[::-1]

    letters = list(word)
    for _ in range(50):
        random.shuffle(letters)
        scrambled = ''.join(letters)
        if scrambled != word:
            return scrambled
    # Fallback: just reverse
    return word[::-1]


def grid_to_html(grid, cell_size=28):
    """Convert a word search grid to an HTML table."""
    size = len(grid)
    html = f'<table class="wordsearch-grid" style="border-collapse: collapse; margin: 0 auto;">\n'
    for row in grid:
        html += '  <tr>\n'
        for cell in row:
            html += f'    <td style="width:{cell_size}px; height:{cell_size}px; text-align:center; vertical-align:middle; font-family:\'Courier New\',monospace; font-size:14px; font-weight:bold; border: 1px solid #ccc; padding:0;">{cell}</td>\n'
        html += '  </tr>\n'
    html += '</table>\n'
    return html


def word_bank_html(words):
    """Generate an HTML word bank display."""
    display_words = [w.upper().replace(" ", "").replace("-", "") for w in words]
    # Sort alphabetically for display
    display_words.sort()

    # Arrange in columns (3-4 columns)
    cols = 3 if len(display_words) <= 15 else 4
    html = '<div class="word-bank" style="margin-top: 12px;">\n'
    html += '<p style="font-weight:bold; text-align:center; margin-bottom:6px; font-size:13px;">Word Bank</p>\n'
    html += f'<div style="display:flex; flex-wrap:wrap; justify-content:center; gap:4px 20px;">\n'
    for word in display_words:
        html += f'  <span style="font-family:\'Courier New\',monospace; font-size:11px; min-width:100px;">{word}</span>\n'
    html += '</div>\n</div>\n'
    return html


if __name__ == "__main__":
    # Quick test
    test_words = ["MOSES", "PHARAOH", "EGYPT", "PLAGUES", "DELIVER", "COVENANT"]
    grid, placed = generate_wordsearch(test_words, size=12)
    print(f"Placed {len(placed)}/{len(test_words)} words")
    for row in grid:
        print(" ".join(row))

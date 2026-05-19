<div align="center">

# **Endfield Protocol**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

<br>

<table>
  <tr>
    <td><img src="demo/Screenshot%202026-05-19%20073709.png" alt="Screenshot" width="200"></td>
    <td><img src="demo/Screenshot%202026-05-19%20073717.png" alt="Screenshot" width="200"></td>
    <td><img src="demo/Screenshot%202026-05-19%20073742.png" alt="Screenshot" width="200"></td>
  </tr>
</table>

<table>
  <tr>
    <td><img src="demo/Screenshot 2026-05-19 075341.png" alt="Screenshot" width="200"></td>
    <td><img src="demo/Screenshot%202026-05-19%20073816.png" alt="Screenshot" width="200"></td>
  </tr>
</table>

</div>

A reimagining of the classic Othello (Reversi) board game with a sleek, futuristic Sci-Fi interface. Players can battle against each other locally or face off against an advanced AI Engine. Featuring dynamic board sizes, a unique Power-Up chest mechanic, and an integrated Hint system to aid your gameplay.

---

## **Description**

Endfield Protocol is built using Python and Pygame. It takes the traditional Othello gameplay and enhances it with custom grid sizes, an item system (chests), and an  AI opponent with three scalable difficulties. The AI utilizes Greedy, Minimax, and Alpha-Beta Pruning algorithms to provide a challenging and dynamic experience.

---

## **Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Project Structure](#project-structure)

---

## **Installation**

**Dependencies required:**
- Python 3.10+
- Pygame 2.0+

**Setup:**

1. Clone the repository:
```bash
git clone https://github.com/HuyDucUIT/endfield-protocol.git
cd endfield-protocol
```

2. Install the required Pygame library:
```bash
pip install pygame
```

3. Ensure the sound file `InvalidMove.mp3` is in the root directory if you want audio feedback.

---

## **Usage**

To start the game, run the main Python file from your terminal:
```bash
python game.py
```


**Controls:**
- **Navigate Menus**: Left Mouse Click
- **Place Piece**: Left Mouse Click on a valid grid cell
- **Use Hint**: Click the `[HINT]` button in the top right (during your turn)
- **Reboot Match**: Click the `[REBOOT]` button

---

## **Features**

**Gameplay**
- **Dynamic Grid Sizes**: Choose between 6x6, 8x8, or 10x10.
- **Alliance Selection**: Play as Black (moves first) or White.
- **Game Modes**: Play locally with `TWO PLAYERS` or test your skills `VS ARTIFICIAL INTELLIGENCE`.
- **Hint System**: Players get 3 Hints per match. The system uses the Hard AI engine to calculate and highlight the most optimal move on the board.

**AI Engine**
- **Easy**: Uses a Greedy Algorithm. Prioritizes capturing the most pieces immediately and targets chests. Has a 40% chance of making a random sub-optimal move.
- **Medium**: Uses Minimax (Depth 2). Calculates two steps ahead to maximize its score while minimizing yours. Has a 20% chance of making a random mistake.
- **Hard**: Uses Minimax + Alpha-Beta Pruning. Calculates four steps ahead (Depth 4) using pruning for maximum efficiency. Plays perfectly with a 0% error rate.

**Power-Up Mechanic (Chests)**
Configure the board to spawn 4, 6, or 8 chests at random empty locations at the start of the match.
- **Gold Chest**: Place a piece on a chest tile to grant the player an Extra Turn (Double Turn), but forces them to sacrifice (lose) one random friendly piece on the board.

---

## **Project Structure**

A brief overview of the project files.

- `game.py`: Main game loop, UI rendering, logic, and AI state management.
- `InvalidMove.mp3`: Audio file for invalid click feedback.
- `README.md`: Project documentation.

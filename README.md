### README.md

# Sea Battle Telegram Bot

This is a Telegram bot that allows users to play a "Sea Battle" game, where they can shoot at a grid to find hidden prizes while avoiding bombs. The bot provides a simple text-based interface with a map represented by emojis.

## Features

- **Grid-based Gameplay**: Players can shoot at a 10x10 grid to find hidden prizes.
- **Admin Panel**: Admins can add shots, place or remove prizes, mark cells as used, and add bombs.
- **Anti-Spam**: Users are blocked temporarily if they send too many commands in a short period.
- **Notification System**: Admins are notified whenever a user hits a bomb or a prize.

## Installation

### Prerequisites

- Python 3.8 or higher
- A Telegram bot token, which you can get by talking to [BotFather](https://core.telegram.org/bots#6-botfather).

### Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/seabattlebot.git
   cd seabattlebot
   ```

2. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up the environment variable for the Telegram bot token:
   ```sh
   export TELEGRAM_BOT_TOKEN=your_token_here
   ```

4. Run the bot:
   ```sh
   python bot.py
   ```

## Usage

### User Commands

- **/start**: Start the game and display the main menu.
- **/battlefield**: Show the current battlefield with the number of shots left.
- **/rules**: Display the game rules.
- **/help**: Display a list of available commands.

### Admin Commands

- **/set_admin**: Authenticate as an admin using a password.
- **Admin Panel**: Admins can use the panel to:
  - Add shots to a user.
  - Edit the map (place prizes, bombs, etc.).
  - Clear the map.
  - Check the current state of the map.

## Map and Gameplay

- **Grid Size**: The map is a 10x10 grid labeled with letters (A-J) and numbers (1-10).
- **Emojis**:
  - 🌅 - Sea (empty cell)
  - ✖️ - Used cell
  - 🎁 - Prize
  - 💣 - Bomb
  - 💥 - Explosion

Players will shoot by entering coordinates like `A1`, `B2`, etc. Admins can modify the map by placing bombs and prizes at specific coordinates.

## Anti-Spam and Security

- Users can send up to 20 commands within 10 seconds before getting blocked for 5 minutes.
- Only the admin can access certain functionalities such as editing the map, adding shots, etc.

## Contribution

Feel free to fork this project, open issues, and submit pull requests. Please ensure your contributions adhere to the existing code style.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgments

- Thanks to the developers and contributors of the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library for making Telegram bot development straightforward.

---

This README provides a comprehensive guide to understanding, setting up, and using the Sea Battle Telegram Bot, ensuring that anyone can quickly get started with the project.

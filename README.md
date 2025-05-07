Built by https://www.blackbox.ai

---

# Bean Genie Bot

## Project Overview

Bean Genie Bot is a Discord bot designed for Bigo Live streamers to help manage their streaming activities effectively. The bot provides various utilities including currency conversion, event management, growth strategies, and tier tracking. It is implemented using Python and Flask, offering both a command-line interface (CLI) and a web-based user interface.

## Installation

To get started with Bean Genie Bot, follow these steps to install the necessary dependencies and set up the environment.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bean-genie-bot.git
   cd bean-genie-bot
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate   # On Windows use `env\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your `GROQ_API_KEY`:
   ```bash
   GROQ_API_KEY=your_api_key_here
   ```
   You can get your API key from [Groq Console](https://console.groq.com/keys).

5. **Initialize the database:**
   The database will be automatically created when you run the application for the first time. Ensure that `sqlite3` is installed on your system.

## Usage

### Running the Bot

You can run the bot in CLI mode or as a web application.

**For CLI mode:**
```bash
python bean_genie_bot.py
```
You can input commands such as:
- `!convert beans 1000`
- `!track 6000 80`
- `!events`

**For Web UI:**
```bash
python web_ui.py
```
Access the web application at `http://localhost:5000` in your web browser. You can register a new account or log in to chat with the bot.

### Available Commands

1. **Currency Conversion**
   - `!convert <type> <amount>`: Convert between beans, diamonds, and USD.

2. **Progress Tracking**
   - `!track <beans> <hours>`: Track your progress and see your current tier.

3. **Get Events**
   - `!events`: Retrieve a list of current events.

4. **Growth Strategies**
   - `!growth <platform>`: Get growth strategies for different platforms like Instagram, TikTok, etc.

5. **Sponsorship Information**
   - `!sponsorship <followers>`: Get information about sponsorship tiers based on follower count.

6. **Wishlist Setup Guide**
   - `!wishlist`: Instructions for setting up an Amazon wishlist.

7. **Cross-Promotion Strategies**
   - `!cross_promote`: Strategies for promoting your streams across platforms.

8. **Loan Information**
   - `!loan_info`: Get details about loan tiers available for streamers.

9. **Check Credit Score**
   - `!credit_score`: Simulate checking a user's credit score.

### Example Commands

```plaintext
!convert beans 1000
!track 8000 120
!events
!growth instagram
```

## Features

- **Currency Conversion**: Easily convert beans to diamonds and USD.
- **Progress Tracking**: Track your streaming progress and tier status.
- **Event Management**: Review current events and join as required.
- **Strategy Guidance**: Obtain personalized growth and cross-promotion strategies.
- **Sponsorship Insights**: Learn about sponsorship tiers based on your follower count.
- **User Authentication**: Login and register functionalities in the web interface.

## Dependencies

The required packages for this project are listed in `requirements.txt`. Below are the main dependencies:

- Flask
- pydantic
- werkzeug
- sqlite3
- dotenv
- groq

To install these, ensure you run:
```bash
pip install -r requirements.txt
```

## Project Structure

Here's a breakdown of the project's structure:

```
bean-genie-bot/
│
├── bean_genie_bot.py       # Main bot logic implemented in Python
├── web_ui.py                # Flask web application for bot interaction
├── requirements.txt         # Dependencies the project needs
├── .env                     # Environment variables setup (GROQ_API_KEY)
└── chat_memory.db           # SQLite database for chat memory
```

## Contributing

Contributions are welcome! Feel free to submit a pull request or report issues as you find them.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Happy streaming with Bean Genie! 🎉
